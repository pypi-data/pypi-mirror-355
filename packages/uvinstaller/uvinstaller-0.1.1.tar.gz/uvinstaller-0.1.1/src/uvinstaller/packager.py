"""
打包功能模块

使用PyInstaller将Python脚本打包为可执行文件。
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from rich.progress import Progress, SpinnerColumn, TextColumn

from .utils import console, run_command, get_executable_extension, get_file_size
from .environment_manager import EnvironmentManager


class Packager:
    """打包器"""

    def __init__(self, env_manager: EnvironmentManager):
        self.env_manager = env_manager
        self.work_dir = env_manager.work_dir
        self.spec_file: Optional[Path] = None
        self.output_file: Optional[Path] = None

    def create_spec_file(self, target_file: Path, **kwargs) -> bool:
        """
        创建PyInstaller spec文件

        Args:
            target_file: 目标Python文件
            **kwargs: 额外的打包选项

        Returns:
            bool: 创建是否成功
        """
        try:
            spec_name = target_file.stem
            self.spec_file = self.work_dir / f"{spec_name}.spec"

            console.print(f"[blue]创建Spec文件: {self.spec_file}[/blue]")

            # 基本的spec文件内容
            spec_content = self._generate_spec_content(target_file, **kwargs)

            with open(self.spec_file, 'w', encoding='utf-8') as f:
                f.write(spec_content)

            console.print(f"[green]Spec文件已创建: {self.spec_file}[/green]")
            return True

        except Exception as e:
            console.print(f"[red]创建Spec文件失败: {e}[/red]")
            return False

    def _generate_spec_content(self, target_file: Path, **kwargs) -> str:
        """生成spec文件内容"""
        name = target_file.stem

        # 基本配置
        onefile = kwargs.get('onefile', True)
        console_mode = kwargs.get('console', True)
        icon = kwargs.get('icon', None)
        runtime_hooks = kwargs.get('runtime_hooks', [])
        data_files = kwargs.get('data_files', [])
        hidden_imports = kwargs.get('hidden_imports', [])

        # 转换路径为正斜杠以避免转义问题
        target_file_str = str(target_file).replace('\\', '/')

        # 处理运行时钩子路径
        runtime_hooks_str = str(runtime_hooks).replace('\\', '/') if runtime_hooks else "[]"

        # 处理静态文件
        datas_str = "[]"
        if data_files:
            datas_list = []
            for src_path, dst_path in data_files:
                # 转换路径为正斜杠
                src_path_str = str(src_path).replace('\\', '/')
                datas_list.append(f"('{src_path_str}', '{dst_path}')")
            datas_str = "[\n        " + ",\n        ".join(datas_list) + "\n    ]"

        # 处理隐藏导入
        hiddenimports_str = "[]"
        if hidden_imports:
            hiddenimports_list = [f"'{module}'" for module in hidden_imports]
            hiddenimports_str = "[\n        " + ",\n        ".join(hiddenimports_list) + "\n    ]"

        # 构建spec内容
        spec_lines = [
            "# -*- mode: python ; coding: utf-8 -*-",
            "import warnings",
            "warnings.filterwarnings('ignore', category=UserWarning, module='pkg_resources')",
            "",
            "block_cipher = None",
            "",
            "a = Analysis(",
            f"    ['{target_file_str}'],",
            "    pathex=[],",
            "    binaries=[],",
            f"    datas={datas_str},",
            f"    hiddenimports={hiddenimports_str},",
            "    hookspath=[],",
            "    hooksconfig={},",
            f"    runtime_hooks={runtime_hooks_str},",
            "    excludes=['pkg_resources'],",
            "    win_no_prefer_redirects=False,",
            "    win_private_assemblies=False,",
            "    cipher=block_cipher,",
            "    noarchive=False,",
            ")",
            "",
            "pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)",
            "",
        ]

        if onefile:
            spec_lines.extend([
                "exe = EXE(",
                "    pyz,",
                "    a.scripts,",
                "    a.binaries,",
                "    a.zipfiles,",
                "    a.datas,",
                "    [],",
                f"    name='{name}',",
                "    debug=False,",
                "    bootloader_ignore_signals=False,",
                "    strip=False,",
                "    upx=True,",
                f"    upx_exclude=[],",
                "    runtime_tmpdir=None,",
                f"    console={console_mode},",
                "    disable_windowed_traceback=False,",
                "    argv_emulation=False,",
                "    target_arch=None,",
                "    codesign_identity=None,",
                "    entitlements_file=None,",
            ])

            if icon:
                spec_lines.insert(-1, f"    icon='{icon}',")

            spec_lines.append(")")
        else:
            # 目录模式
            spec_lines.extend([
                "exe = EXE(",
                "    pyz,",
                "    a.scripts,",
                "    [],",
                "    exclude_binaries=True,",
                f"    name='{name}',",
                "    debug=False,",
                "    bootloader_ignore_signals=False,",
                "    strip=False,",
                "    upx=True,",
                f"    console={console_mode},",
                "    disable_windowed_traceback=False,",
                "    argv_emulation=False,",
                "    target_arch=None,",
                "    codesign_identity=None,",
                "    entitlements_file=None,",
                ")",
                "",
                "coll = COLLECT(",
                "    exe,",
                "    a.binaries,",
                "    a.zipfiles,",
                "    a.datas,",
                "    strip=False,",
                "    upx=True,",
                "    upx_exclude=[],",
                f"    name='{name}',",
                ")",
            ])

        return "\n".join(spec_lines)

    def _create_runtime_hook(self) -> Path:
        """创建运行时钩子来抑制pkg_resources警告"""
        hook_content = '''
import warnings
import sys

# 抑制pkg_resources弃用警告
warnings.filterwarnings("ignore", category=UserWarning, module="pkg_resources")
warnings.filterwarnings("ignore", message=".*pkg_resources.*", category=UserWarning)

# 抑制setuptools相关警告
warnings.filterwarnings("ignore", category=UserWarning, module="setuptools")
'''

        hook_file = self.work_dir / "pyi_rth_suppress_warnings.py"
        with open(hook_file, 'w', encoding='utf-8') as f:
            f.write(hook_content)

        return hook_file

    def build_executable(self, target_file: Path, **kwargs) -> bool:
        """
        构建可执行文件

        Args:
            target_file: 目标Python文件
            **kwargs: 打包选项

        Returns:
            bool: 构建是否成功
        """
        try:
            # 复制目标文件到工作目录
            import shutil
            work_target_file = self.work_dir / target_file.name
            shutil.copy2(target_file, work_target_file)
            console.print(f"[dim]复制文件到工作目录: {work_target_file}[/dim]")

            # 创建运行时钩子
            runtime_hook = self._create_runtime_hook()
            console.print(f"[dim]创建运行时钩子: {runtime_hook}[/dim]")

            # 创建spec文件
            if not self.create_spec_file(work_target_file, runtime_hooks=[str(runtime_hook)], **kwargs):
                return False

            # 获取pyinstaller可执行文件
            pyinstaller_exe = self.env_manager.get_tool_executable("pyinstaller")
            if not pyinstaller_exe:
                console.print("[red]PyInstaller未找到[/red]")
                return False

            console.print(f"[blue]开始打包应用程序[/blue]")

            # 构建命令
            cmd = [
                pyinstaller_exe,
                "--clean",
                "--noconfirm",
                str(self.spec_file)
            ]

            # 添加额外选项
            if kwargs.get('verbose', False):
                cmd.append("--log-level=DEBUG")

            with Progress(
                SpinnerColumn(),
                TextColumn("正在打包应用程序..."),
                console=console,
            ) as progress:
                task = progress.add_task("building", total=None)

                # 设置环境变量
                env = os.environ.copy()
                env["VIRTUAL_ENV"] = str(self.env_manager.venv_dir)

                result = run_command(
                    cmd,
                    cwd=self.work_dir,
                    env=env,
                    capture_output=not kwargs.get('verbose', False)
                )
                progress.update(task, completed=True)

            if result.returncode == 0:
                # 查找输出文件
                self.output_file = self._find_output_file(target_file)
                if self.output_file and self.output_file.exists():
                    file_size = get_file_size(self.output_file)
                    console.print(f"[green]打包完成: {self.output_file} ({file_size})[/green]")
                    return True
                else:
                    console.print("[red]找不到输出文件[/red]")
                    return False
            else:
                console.print("[red]打包失败[/red]")
                if result.stderr:
                    console.print(f"[red]错误信息: {result.stderr}[/red]")
                return False

        except Exception as e:
            console.print(f"[red]打包过程中出错: {e}[/red]")
            return False

    def _find_output_file(self, target_file: Path) -> Optional[Path]:
        """查找输出文件"""
        dist_dir = self.work_dir / "dist"
        if not dist_dir.exists():
            return None

        name = target_file.stem
        exe_extension = get_executable_extension()

        # 查找可执行文件
        exe_file = dist_dir / f"{name}{exe_extension}"
        if exe_file.exists():
            return exe_file

        # 查找目录模式的可执行文件
        exe_dir = dist_dir / name
        if exe_dir.exists():
            exe_file = exe_dir / f"{name}{exe_extension}"
            if exe_file.exists():
                return exe_file

        return None

    def get_build_info(self) -> Dict[str, Any]:
        """获取构建信息"""
        info = {
            "work_dir": str(self.work_dir),
            "spec_file": str(self.spec_file) if self.spec_file else None,
            "output_file": str(self.output_file) if self.output_file else None,
        }

        if self.output_file and self.output_file.exists():
            info["output_size"] = get_file_size(self.output_file)
            info["output_exists"] = True
        else:
            info["output_exists"] = False

        return info

    def cleanup_build_files(self) -> None:
        """清理构建文件"""
        import shutil

        # 清理build目录
        build_dir = self.work_dir / "build"
        if build_dir.exists():
            console.print(f"[dim]清理构建目录: {build_dir}[/dim]")
            shutil.rmtree(build_dir, ignore_errors=True)

        # 清理spec文件
        if self.spec_file and self.spec_file.exists():
            console.print(f"[dim]清理spec文件: {self.spec_file}[/dim]")
            self.spec_file.unlink(missing_ok=True)
