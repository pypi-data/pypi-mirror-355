"""
依赖分析模块

分析Python文件的导入依赖，识别第三方包和标准库模块。
"""

import ast
import sys
import importlib.util
from pathlib import Path
from typing import Set, List, Dict, Optional, Tuple
from rich.console import Console
from rich.table import Table

from .utils import console

# Python标准库模块列表（Python 3.8+）
STDLIB_MODULES = {
    'abc', 'aifc', 'argparse', 'array', 'ast', 'asynchat', 'asyncio', 'asyncore',
    'atexit', 'audioop', 'base64', 'bdb', 'binascii', 'binhex', 'bisect', 'builtins',
    'bz2', 'calendar', 'cgi', 'cgitb', 'chunk', 'cmath', 'cmd', 'code', 'codecs',
    'codeop', 'collections', 'colorsys', 'compileall', 'concurrent', 'configparser',
    'contextlib', 'copy', 'copyreg', 'cProfile', 'crypt', 'csv', 'ctypes', 'curses',
    'dataclasses', 'datetime', 'dbm', 'decimal', 'difflib', 'dis', 'distutils',
    'doctest', 'email', 'encodings', 'ensurepip', 'enum', 'errno', 'faulthandler',
    'fcntl', 'filecmp', 'fileinput', 'fnmatch', 'formatter', 'fractions', 'ftplib',
    'functools', 'gc', 'getopt', 'getpass', 'gettext', 'glob', 'grp', 'gzip',
    'hashlib', 'heapq', 'hmac', 'html', 'http', 'imaplib', 'imghdr', 'imp',
    'importlib', 'inspect', 'io', 'ipaddress', 'itertools', 'json', 'keyword',
    'lib2to3', 'linecache', 'locale', 'logging', 'lzma', 'mailbox', 'mailcap',
    'marshal', 'math', 'mimetypes', 'mmap', 'modulefinder', 'msilib', 'msvcrt',
    'multiprocessing', 'netrc', 'nntplib', 'numbers', 'operator', 'optparse', 'os',
    'ossaudiodev', 'parser', 'pathlib', 'pdb', 'pickle', 'pickletools', 'pipes',
    'pkgutil', 'platform', 'plistlib', 'poplib', 'posix', 'pprint', 'profile',
    'pstats', 'pty', 'pwd', 'py_compile', 'pyclbr', 'pydoc', 'queue', 'quopri',
    'random', 're', 'readline', 'reprlib', 'resource', 'rlcompleter', 'runpy',
    'sched', 'secrets', 'select', 'selectors', 'shelve', 'shlex', 'shutil', 'signal',
    'site', 'smtpd', 'smtplib', 'sndhdr', 'socket', 'socketserver', 'sqlite3',
    'ssl', 'stat', 'statistics', 'string', 'stringprep', 'struct', 'subprocess',
    'sunau', 'symbol', 'symtable', 'sys', 'sysconfig', 'tabnanny', 'tarfile',
    'telnetlib', 'tempfile', 'termios', 'test', 'textwrap', 'threading', 'time',
    'timeit', 'tkinter', 'token', 'tokenize', 'trace', 'traceback', 'tracemalloc',
    'tty', 'turtle', 'turtledemo', 'types', 'typing', 'unicodedata', 'unittest',
    'urllib', 'uu', 'uuid', 'venv', 'warnings', 'wave', 'weakref', 'webbrowser',
    'winreg', 'winsound', 'wsgiref', 'xdrlib', 'xml', 'xmlrpc', 'zipapp', 'zipfile',
    'zipimport', 'zlib', 'zoneinfo'
}


class ImportVisitor(ast.NodeVisitor):
    """AST访问器，用于提取导入语句"""

    def __init__(self):
        self.imports: Set[str] = set()
        self.from_imports: Set[str] = set()

    def visit_Import(self, node: ast.Import) -> None:
        """访问import语句"""
        for alias in node.names:
            self.imports.add(alias.name.split('.')[0])
        # 继续访问子节点
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """访问from...import语句"""
        if node.module:
            self.from_imports.add(node.module.split('.')[0])
        # 继续访问子节点
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        """访问try语句，确保处理try块中的导入"""
        # 访问try块中的所有语句
        for stmt in node.body:
            self.visit(stmt)
        # 访问except块
        for handler in node.handlers:
            for stmt in handler.body:
                self.visit(stmt)
        # 访问else块
        for stmt in node.orelse:
            self.visit(stmt)
        # 访问finally块
        for stmt in node.finalbody:
            self.visit(stmt)


class DependencyAnalyzer:
    """依赖分析器"""

    def __init__(self):
        self.analyzed_files: Set[Path] = set()
        self.all_imports: Set[str] = set()
        self.third_party_packages: Set[str] = set()
        self.stdlib_modules: Set[str] = set()

    def analyze_file(self, file_path: Path) -> Dict[str, Set[str]]:
        """
        分析单个Python文件的依赖

        Args:
            file_path: Python文件路径

        Returns:
            Dict[str, Set[str]]: 包含imports, third_party, stdlib的字典
        """
        if file_path in self.analyzed_files:
            return self._get_current_results()

        self.analyzed_files.add(file_path)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, str(file_path))
            visitor = ImportVisitor()
            visitor.visit(tree)

            # 合并所有导入
            file_imports = visitor.imports | visitor.from_imports
            self.all_imports.update(file_imports)

            # 分类导入
            for module in file_imports:
                if self._is_stdlib_module(module):
                    self.stdlib_modules.add(module)
                else:
                    self.third_party_packages.add(module)

            console.print(f"[dim]分析文件: {file_path} - 发现 {len(file_imports)} 个导入[/dim]")

        except SyntaxError as e:
            console.print(f"[red]语法错误 {file_path}: {e}[/red]")
        except Exception as e:
            console.print(f"[red]分析文件失败 {file_path}: {e}[/red]")

        return self._get_current_results()

    def analyze_directory(self, dir_path: Path, recursive: bool = True) -> Dict[str, Set[str]]:
        """
        分析目录中的所有Python文件

        Args:
            dir_path: 目录路径
            recursive: 是否递归分析子目录

        Returns:
            Dict[str, Set[str]]: 分析结果
        """
        pattern = "**/*.py" if recursive else "*.py"
        python_files = list(dir_path.glob(pattern))

        console.print(f"[blue]发现 {len(python_files)} 个Python文件[/blue]")

        for file_path in python_files:
            self.analyze_file(file_path)

        return self._get_current_results()

    def analyze_project(self, target_path: Path) -> Dict[str, Set[str]]:
        """
        分析项目依赖

        Args:
            target_path: 目标文件或目录路径

        Returns:
            Dict[str, Set[str]]: 分析结果
        """
        if target_path.is_file():
            return self.analyze_file(target_path)
        elif target_path.is_dir():
            return self.analyze_directory(target_path)
        else:
            raise ValueError(f"无效的路径: {target_path}")

    def _is_stdlib_module(self, module_name: str) -> bool:
        """检查模块是否为标准库模块"""
        # 首先检查已知的标准库列表
        if module_name in STDLIB_MODULES:
            return True

        # 尝试导入检查
        try:
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                return False

            # 检查模块路径是否在标准库中
            if spec.origin:
                origin_path = Path(spec.origin)

                # 获取Python标准库路径
                import sysconfig
                stdlib_paths = [
                    Path(sysconfig.get_path('stdlib')),
                    Path(sysconfig.get_path('platstdlib')),
                ]

                # 检查是否在标准库路径中，且不在site-packages中
                for stdlib_path in stdlib_paths:
                    try:
                        relative_path = origin_path.relative_to(stdlib_path)
                        # 确保不是site-packages中的模块
                        if 'site-packages' not in str(relative_path):
                            return True
                    except ValueError:
                        continue

        except (ImportError, ModuleNotFoundError, ValueError):
            pass

        return False

    def _get_current_results(self) -> Dict[str, Set[str]]:
        """获取当前分析结果"""
        return {
            'imports': self.all_imports.copy(),
            'third_party': self.third_party_packages.copy(),
            'stdlib': self.stdlib_modules.copy()
        }

    def print_summary(self) -> None:
        """打印依赖分析摘要"""
        console.print("\n[bold blue]依赖分析完成:[/bold blue]")

        # 创建摘要表格
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("类型", style="cyan")
        table.add_column("数量", justify="right", style="green")
        table.add_column("详情", style="dim")

        table.add_row(
            "总导入数",
            str(len(self.all_imports)),
            f"分析了 {len(self.analyzed_files)} 个文件"
        )
        table.add_row(
            "第三方包",
            str(len(self.third_party_packages)),
            ", ".join(sorted(self.third_party_packages)) if self.third_party_packages else "无"
        )
        table.add_row(
            "标准库模块",
            str(len(self.stdlib_modules)),
            ", ".join(sorted(self.stdlib_modules)) if self.stdlib_modules else "无"
        )

        console.print(table)

        # 单独显示第三方依赖
        if self.third_party_packages:
            console.print("\n[bold yellow]第三方依赖:[/bold yellow]")
            for package in sorted(self.third_party_packages):
                console.print(f"  - {package}")

    def get_requirements_list(self) -> List[str]:
        """获取requirements列表"""
        return sorted(list(self.third_party_packages))
