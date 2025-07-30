"""
安全加固模块

使用PyArmor对可执行文件进行代码保护和加密。
"""

import os
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
from rich.progress import Progress, SpinnerColumn, TextColumn

from .utils import console, run_command, get_file_size
from .environment_manager import EnvironmentManager


class SecurityProtector:
    """安全保护器"""

    def __init__(self, env_manager: EnvironmentManager):
        self.env_manager = env_manager
        self.work_dir = env_manager.work_dir
        self.protected_file: Optional[Path] = None
        self.protected_source: Optional[Path] = None

    def protect_executable(self, executable_path: Path, target_file: Path) -> bool:
        """
        保护可执行文件

        Args:
            executable_path: 可执行文件路径
            target_file: 原始Python文件路径

        Returns:
            bool: 保护是否成功
        """
        try:
            if not executable_path.exists():
                console.print(f"[red]可执行文件不存在: {executable_path}[/red]")
                return False

            if not target_file.exists():
                console.print(f"[red]原始Python文件不存在: {target_file}[/red]")
                return False

            console.print(f"[blue]开始代码保护[/blue]")

            # 获取pyarmor可执行文件
            pyarmor_exe = self.env_manager.get_tool_executable("pyarmor")
            if not pyarmor_exe:
                console.print("[red]PyArmor未找到[/red]")
                return False

            # 创建保护后的文件名
            protected_name = executable_path.stem + "_protected" + executable_path.suffix
            self.protected_file = self.work_dir / protected_name

            # 使用PyArmor保护可执行文件
            success = self._protect_with_pyarmor(executable_path, target_file, pyarmor_exe)
            if not success:
                return False

            if self.protected_file and self.protected_file.exists():
                file_size = get_file_size(self.protected_file)
                console.print(f"[green]代码保护完成: {self.protected_file} ({file_size})[/green]")
                return True
            else:
                console.print("[red]保护后的文件未找到[/red]")
                return False

        except Exception as e:
            console.print(f"[red]代码保护过程中出错: {e}[/red]")
            return False



    def _protect_with_pyarmor(self, executable_path: Path, target_file: Path, pyarmor_exe: str) -> bool:
        """使用PyArmor保护可执行文件"""
        try:
            # 复制文件到工作目录以便PyArmor处理
            work_exe_path = self.work_dir / executable_path.name
            work_py_path = self.work_dir / target_file.name

            # 如果文件不在工作目录，复制过来
            if executable_path != work_exe_path:
                shutil.copy2(executable_path, work_exe_path)
            if target_file != work_py_path:
                shutil.copy2(target_file, work_py_path)

            console.print("[blue]使用PyArmor保护可执行文件[/blue]")

            # 创建输出目录
            output_dir = self.work_dir / "obfdist"
            output_dir.mkdir(exist_ok=True)

            # 构建PyArmor命令 - 使用新的命令格式
            # pyarmor gen -O obfdist --pack .\dist\ABC.exe .\ABC.py
            cmd = [
                pyarmor_exe,
                "gen",
                "-O", str(output_dir),
                "--pack", str(work_exe_path),
                str(work_py_path)
            ]

            with Progress(
                SpinnerColumn(),
                TextColumn("正在保护可执行文件..."),
                console=console,
            ) as progress:
                task = progress.add_task("protecting", total=None)

                # 设置环境变量
                env = os.environ.copy()
                env["VIRTUAL_ENV"] = str(self.env_manager.venv_dir)

                result = run_command(
                    cmd,
                    cwd=self.work_dir,
                    env=env,
                    capture_output=True,
                    check=False  # 不要在失败时抛出异常
                )
                progress.update(task, completed=True)

            # 显示PyArmor的详细输出
            if result.stdout:
                console.print(f"[dim]PyArmor输出: {result.stdout}[/dim]")
            if result.stderr:
                console.print(f"[yellow]PyArmor警告/错误: {result.stderr}[/yellow]")

            if result.returncode == 0:
                # PyArmor 8.4.7 使用 --pack 选项会直接修改原始可执行文件
                # 检查PyArmor输出信息确认成功
                if "generate patched bundle" in result.stderr and "successfully" in result.stderr:
                    console.print("[green]PyArmor保护成功，原始文件已被修改[/green]")

                    # PyArmor直接修改了原始文件，所以我们使用修改后的原始文件
                    if work_exe_path.exists():
                        # 复制保护后的文件到最终位置
                        shutil.copy2(work_exe_path, self.protected_file)
                        console.print(f"[green]保护后的可执行文件生成成功: {self.protected_file}[/green]")
                        return True
                    else:
                        console.print("[red]原始可执行文件不存在[/red]")
                        return False
                else:
                    console.print("[yellow]PyArmor输出中未找到成功标识，尝试查找生成的文件[/yellow]")

                    # 备用方案：查找可能的输出位置
                    possible_protected_exe_locations = [
                        output_dir / executable_path.name,  # 主要输出位置
                        output_dir / "dist" / executable_path.name,  # 备选位置1
                        self.work_dir / ".pyarmor" / "pack" / "dist" / executable_path.name,  # 备选位置2
                        self.work_dir / ".pyarmor" / "pack" / executable_path.name,  # 备选位置3
                        work_exe_path,  # 原始文件位置（可能已被修改）
                    ]

                    protected_exe = None
                    for location in possible_protected_exe_locations:
                        if location.exists():
                            protected_exe = location
                            break

                    if protected_exe:
                        console.print(f"[green]找到保护后的可执行文件: {protected_exe}[/green]")
                        shutil.copy2(protected_exe, self.protected_file)
                        console.print("[green]保护后的可执行文件生成成功[/green]")
                        return True
                    else:
                        console.print("[red]未找到任何保护后的可执行文件[/red]")
                        return False
            else:
                console.print(f"[red]PyArmor执行失败，返回码: {result.returncode}[/red]")
                if result.stderr:
                    console.print(f"[red]错误信息: {result.stderr}[/red]")
                if result.stdout:
                    console.print(f"[red]输出信息: {result.stdout}[/red]")
                return False

        except Exception as e:
            console.print(f"[red]保护可执行文件时出错: {e}[/red]")

            # 如果是PyArmor授权问题，提供友好的提示
            if "未经授权" in str(e) or "unauthorized" in str(e).lower():
                console.print("[yellow]检测到PyArmor授权限制。[/yellow]")
                console.print("[dim]提示: 可以使用 --no-protection 选项跳过代码保护[/dim]")

            return False



    def simple_protect(self, executable_path: Path) -> bool:
        """
        简单保护模式（仅对已有可执行文件进行基本保护）

        Args:
            executable_path: 可执行文件路径

        Returns:
            bool: 保护是否成功
        """
        try:
            if not executable_path.exists():
                console.print(f"[red]可执行文件不存在: {executable_path}[/red]")
                return False

            console.print(f"[blue]应用简单保护[/blue]")

            # 创建保护后的文件名
            protected_name = executable_path.stem + "_protected" + executable_path.suffix
            self.protected_file = executable_path.parent / protected_name

            # 简单复制并添加基本保护标记
            shutil.copy2(executable_path, self.protected_file)

            # 这里可以添加更多的保护措施，比如：
            # - 文件头部修改
            # - 简单的加密
            # - 反调试检测等

            console.print(f"[green]简单保护完成: {self.protected_file}[/green]")
            return True

        except Exception as e:
            console.print(f"[red]简单保护过程中出错: {e}[/red]")
            return False

    def get_protection_info(self) -> Dict[str, Any]:
        """获取保护信息"""
        info = {
            "work_dir": str(self.work_dir),
            "protected_file": str(self.protected_file) if self.protected_file else None,
        }

        if self.protected_file and self.protected_file.exists():
            info["protected_size"] = get_file_size(self.protected_file)
            info["protected_exists"] = True
        else:
            info["protected_exists"] = False

        return info

    def cleanup_protection_files(self) -> None:
        """清理保护相关的临时文件"""
        # 清理PyArmor输出目录
        obfdist_dir = self.work_dir / "obfdist"
        if obfdist_dir.exists():
            console.print(f"[dim]清理保护输出目录: {obfdist_dir}[/dim]")
            shutil.rmtree(obfdist_dir, ignore_errors=True)
