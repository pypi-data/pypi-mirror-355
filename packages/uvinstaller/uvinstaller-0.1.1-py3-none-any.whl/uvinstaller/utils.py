"""
工具函数模块

提供通用的工具函数和辅助功能。
"""

import os
import shutil
import subprocess
import tempfile
import platform
from pathlib import Path
from typing import List, Optional, Tuple, Union
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def get_platform_info() -> Tuple[str, str]:
    """获取平台信息"""
    system = platform.system().lower()
    arch = platform.machine().lower()
    return system, arch


def is_windows() -> bool:
    """检查是否为Windows系统"""
    return platform.system().lower() == "windows"


def get_executable_extension() -> str:
    """获取可执行文件扩展名"""
    return ".exe" if is_windows() else ""


def run_command(
    cmd: List[str],
    cwd: Optional[Union[str, Path]] = None,
    capture_output: bool = True,
    check: bool = True,
    env: Optional[dict] = None,
) -> subprocess.CompletedProcess:
    """
    运行命令并返回结果

    Args:
        cmd: 命令列表
        cwd: 工作目录
        capture_output: 是否捕获输出
        check: 是否检查返回码
        env: 环境变量

    Returns:
        subprocess.CompletedProcess: 命令执行结果
    """
    try:
        if env is None:
            env = os.environ.copy()

        # 在Windows上设置正确的编码
        if is_windows():
            # 尝试使用UTF-8，如果失败则使用GBK
            try:
                result = subprocess.run(
                    cmd,
                    cwd=cwd,
                    capture_output=capture_output,
                    text=True,
                    check=check,
                    env=env,
                    encoding='utf-8',
                    errors='replace'
                )
                return result
            except UnicodeDecodeError:
                # 如果UTF-8失败，尝试GBK
                result = subprocess.run(
                    cmd,
                    cwd=cwd,
                    capture_output=capture_output,
                    text=True,
                    check=check,
                    env=env,
                    encoding='gbk',
                    errors='replace'
                )
                return result
        else:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=capture_output,
                text=True,
                check=check,
                env=env,
                encoding='utf-8',
                errors='replace'
            )
            return result

    except subprocess.CalledProcessError as e:
        console.print(f"[red]命令执行失败: {' '.join(cmd)}[/red]")
        console.print(f"[red]错误信息: {e.stderr}[/red]")
        raise
    except FileNotFoundError as e:
        console.print(f"[red]命令未找到: {cmd[0]}[/red]")
        raise


def check_command_exists(command: str) -> bool:
    """检查命令是否存在"""
    return shutil.which(command) is not None


def create_temp_dir(prefix: str = "uvinstaller_") -> Path:
    """创建临时目录"""
    temp_dir = Path(tempfile.mkdtemp(prefix=prefix))
    console.print(f"[dim]创建临时目录: {temp_dir}[/dim]")
    return temp_dir


def cleanup_temp_dir(temp_dir: Path) -> None:
    """清理临时目录"""
    if temp_dir.exists():
        console.print(f"[dim]清理临时目录: {temp_dir}[/dim]")
        shutil.rmtree(temp_dir, ignore_errors=True)


def ensure_dir(path: Union[str, Path]) -> Path:
    """确保目录存在"""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def copy_file(src: Union[str, Path], dst: Union[str, Path]) -> None:
    """复制文件"""
    src = Path(src)
    dst = Path(dst)

    if not src.exists():
        raise FileNotFoundError(f"源文件不存在: {src}")

    # 确保目标目录存在
    dst.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy2(src, dst)
    console.print(f"[green]文件已复制: {src} -> {dst}[/green]")


def get_file_size(path: Union[str, Path]) -> str:
    """获取文件大小的人类可读格式"""
    path = Path(path)
    if not path.exists():
        return "0 B"

    size = path.stat().st_size
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def validate_python_file(file_path: Union[str, Path]) -> bool:
    """验证Python文件是否有效"""
    file_path = Path(file_path)

    if not file_path.exists():
        console.print(f"[red]文件不存在: {file_path}[/red]")
        return False

    if not file_path.suffix == ".py":
        console.print(f"[red]不是Python文件: {file_path}[/red]")
        return False

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            compile(f.read(), str(file_path), 'exec')
        return True
    except SyntaxError as e:
        console.print(f"[red]Python语法错误: {e}[/red]")
        return False
    except Exception as e:
        console.print(f"[red]文件读取错误: {e}[/red]")
        return False


def install_tool(tool_name: str, install_cmd: List[str]) -> bool:
    """
    安装工具

    Args:
        tool_name: 工具名称
        install_cmd: 安装命令

    Returns:
        bool: 安装是否成功
    """
    try:
        console.print(f"[yellow]{tool_name} 未安装，正在自动安装...[/yellow]")

        with Progress(
            SpinnerColumn(),
            TextColumn(f"正在安装 {tool_name}..."),
            console=console,
        ) as progress:
            task = progress.add_task("installing", total=None)
            result = run_command(install_cmd, capture_output=True)
            progress.update(task, completed=True)

        if result.returncode == 0:
            console.print(f"[green]{tool_name} 安装成功[/green]")
            return True
        else:
            console.print(f"[red]{tool_name} 安装失败[/red]")
            console.print(f"[red]错误信息: {result.stderr}[/red]")
            return False

    except Exception as e:
        console.print(f"[red]{tool_name} 安装失败: {e}[/red]")
        return False


def format_duration(seconds: float) -> str:
    """格式化时间持续时间"""
    if seconds < 60:
        return f"{seconds:.1f}秒"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}分钟"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}小时"
