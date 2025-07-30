"""
环境管理模块

使用uv管理虚拟环境和依赖安装。
"""

import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from rich.progress import Progress, SpinnerColumn, TextColumn

from .utils import (
    console, run_command, check_command_exists, install_tool,
    ensure_dir
)


class EnvironmentManager:
    """环境管理器"""

    def __init__(self, work_dir: Path, cache_dir: Optional[Path] = None, no_cache: bool = False, refresh: bool = False):
        self.work_dir = Path(work_dir)
        self.uv_available = False

        # 缓存配置
        self.no_cache = no_cache
        self.refresh = refresh
        self.cache_dir = self._get_cache_dir(cache_dir)

        # 共享虚拟环境目录
        self.shared_envs_dir = self._get_shared_envs_dir()
        self.venv_dir = None  # 将在创建或复用环境时设置

        console.print(f"[dim]使用缓存目录: {self.cache_dir}[/dim]")
        console.print(f"[dim]共享环境目录: {self.shared_envs_dir}[/dim]")

    def _get_cache_dir(self, custom_cache_dir: Optional[Path] = None) -> Optional[Path]:
        """获取缓存目录"""
        if self.no_cache:
            return None

        if custom_cache_dir:
            cache_dir = Path(custom_cache_dir).resolve()
            ensure_dir(cache_dir)
            return cache_dir

        # 使用系统默认缓存目录
        if sys.platform == "win32":
            # Windows: %LOCALAPPDATA%\uvinstaller\cache
            cache_base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
            cache_dir = cache_base / "uvinstaller" / "cache"
        else:
            # Unix: $XDG_CACHE_HOME/uvinstaller 或 $HOME/.cache/uvinstaller
            cache_base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
            cache_dir = cache_base / "uvinstaller"

        ensure_dir(cache_dir)
        return cache_dir

    def _get_shared_envs_dir(self) -> Path:
        """获取共享虚拟环境目录"""
        if sys.platform == "win32":
            # Windows: %LOCALAPPDATA%\uvinstaller\envs
            envs_base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
            envs_dir = envs_base / "uvinstaller" / "envs"
        else:
            # Unix: $XDG_CACHE_HOME/uvinstaller/envs 或 $HOME/.cache/uvinstaller/envs
            envs_base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
            envs_dir = envs_base / "uvinstaller" / "envs"

        ensure_dir(envs_dir)
        return envs_dir

    def _build_uv_command(self, base_cmd: List[str]) -> List[str]:
        """构建带缓存参数的uv命令"""
        cmd = base_cmd.copy()

        # 检查是否已经包含 --no-cache 参数
        has_no_cache = "--no-cache" in cmd

        # 添加缓存目录参数（如果没有 --no-cache）
        if not has_no_cache:
            if self.cache_dir:
                cmd.extend(["--cache-dir", str(self.cache_dir)])
            elif self.no_cache:
                cmd.append("--no-cache")

        # 添加刷新参数（如果没有 --no-cache）
        if self.refresh and not has_no_cache:
            cmd.append("--refresh")

        return cmd

    def ensure_uv_installed(self) -> bool:
        """确保uv已安装"""
        if check_command_exists("uv"):
            self.uv_available = True
            console.print("[green]uv 已安装[/green]")
            return True

        # 尝试安装uv
        console.print("[yellow]uv 未安装，正在自动安装...[/yellow]")

        # 使用pip安装uv
        install_cmd = [sys.executable, "-m", "pip", "install", "uv"]
        success = install_tool("uv", install_cmd)

        if success:
            self.uv_available = check_command_exists("uv")
            if not self.uv_available:
                console.print("[red]uv安装后仍无法找到，请检查PATH环境变量[/red]")
                return False

        return success

    def _calculate_env_hash(self, packages: List[str], project_path: Optional[Path] = None) -> str:
        """计算依赖包的哈希值，用于环境复用"""
        import hashlib

        # 包含构建工具的完整包列表
        all_packages = sorted(packages + ["pyinstaller==5.13.2", "pyarmor==8.4.7"])
        packages_str = "|".join(all_packages)

        # 添加Python版本信息
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        # 添加项目路径信息，让不同项目使用不同的虚拟环境
        project_info = ""
        if project_path:
            # 使用项目文件的父目录路径作为项目标识
            project_dir = str(project_path.parent.resolve())
            project_info = f"|project-{project_dir}"

        hash_input = f"{packages_str}|python-{python_version}{project_info}"

        return hashlib.md5(hash_input.encode()).hexdigest()[:12]

    def _find_compatible_env(self, env_hash: str) -> Optional[Path]:
        """查找兼容的虚拟环境"""
        env_dir = self.shared_envs_dir / f"env_{env_hash}"

        if env_dir.exists():
            # 检查环境是否有效
            if sys.platform == "win32":
                python_exe = env_dir / "Scripts" / "python.exe"
            else:
                python_exe = env_dir / "bin" / "python"

            if python_exe.exists():
                console.print(f"[green]找到兼容的虚拟环境: {env_dir}[/green]")
                return env_dir
            else:
                console.print(f"[yellow]环境损坏，将重新创建: {env_dir}[/yellow]")
                import shutil
                shutil.rmtree(env_dir, ignore_errors=True)

        return None

    def create_or_reuse_virtual_environment(self, packages: List[str], project_path: Optional[Path] = None) -> bool:
        """创建或复用虚拟环境"""
        if not self.uv_available:
            console.print("[red]uv不可用，无法创建虚拟环境[/red]")
            return False

        try:
            # 计算环境哈希（包含项目路径信息）
            env_hash = self._calculate_env_hash(packages, project_path)
            console.print(f"[dim]环境哈希: {env_hash}[/dim]")
            if project_path:
                console.print(f"[dim]项目路径: {project_path.parent}[/dim]")

            # 查找兼容的环境
            existing_env = self._find_compatible_env(env_hash)

            if existing_env and not self.refresh:
                # 复用现有环境
                self.venv_dir = existing_env
                console.print(f"[green]复用现有虚拟环境: {self.venv_dir}[/green]")
                return True

            # 创建新环境
            self.venv_dir = self.shared_envs_dir / f"env_{env_hash}"

            # 删除已存在的环境（如果需要刷新）
            if self.venv_dir.exists():
                console.print("[yellow]删除已存在的虚拟环境[/yellow]")
                import shutil
                shutil.rmtree(self.venv_dir)

            console.print(f"[blue]创建新的虚拟环境: {self.venv_dir}[/blue]")

            # 使用uv创建虚拟环境
            base_cmd = ["uv", "venv", str(self.venv_dir)]
            cmd = self._build_uv_command(base_cmd)

            with Progress(
                SpinnerColumn(),
                TextColumn("正在创建虚拟环境..."),
                console=console,
            ) as progress:
                task = progress.add_task("creating", total=None)
                result = run_command(cmd, cwd=self.work_dir)
                progress.update(task, completed=True)

            if result.returncode == 0:
                console.print(f"[green]虚拟环境创建成功: {self.venv_dir}[/green]")
                return True
            else:
                console.print("[red]虚拟环境创建失败[/red]")
                return False

        except Exception as e:
            console.print(f"[red]创建虚拟环境时出错: {e}[/red]")
            return False

    def create_virtual_environment(self) -> bool:
        """创建虚拟环境（在工作目录中，用于向后兼容）"""
        if not self.uv_available:
            console.print("[red]uv不可用，无法创建虚拟环境[/red]")
            return False

        try:
            # 确保工作目录存在
            ensure_dir(self.work_dir)

            # 设置工作目录中的虚拟环境
            self.venv_dir = self.work_dir / "venv"

            # 删除已存在的虚拟环境
            if self.venv_dir.exists():
                console.print("[yellow]删除已存在的虚拟环境[/yellow]")
                import shutil
                shutil.rmtree(self.venv_dir)

            console.print(f"[blue]创建虚拟环境: {self.venv_dir}[/blue]")

            # 使用uv创建虚拟环境，使用缓存配置
            base_cmd = ["uv", "venv", str(self.venv_dir)]
            cmd = self._build_uv_command(base_cmd)

            with Progress(
                SpinnerColumn(),
                TextColumn("正在创建虚拟环境..."),
                console=console,
            ) as progress:
                task = progress.add_task("creating", total=None)
                result = run_command(cmd, cwd=self.work_dir)
                progress.update(task, completed=True)

            if result.returncode == 0:
                console.print(f"[green]虚拟环境创建成功: {self.venv_dir}[/green]")
                return True
            else:
                console.print("[red]虚拟环境创建失败[/red]")
                return False

        except Exception as e:
            console.print(f"[red]创建虚拟环境时出错: {e}[/red]")
            return False

    def install_dependencies(self, packages: List[str]) -> bool:
        """
        安装依赖包（一个一个安装，跳过不存在的包）

        Args:
            packages: 要安装的包列表

        Returns:
            bool: 安装是否成功（至少安装成功一个包就返回True）
        """
        if not packages:
            console.print("[yellow]没有需要安装的依赖包[/yellow]")
            return True

        if not self.venv_dir.exists():
            console.print("[red]虚拟环境不存在，请先创建虚拟环境[/red]")
            return False

        console.print(f"[blue]安装 {len(packages)} 个依赖包[/blue]")

        successful_installs = 0
        failed_packages = []

        # 设置虚拟环境
        env = os.environ.copy()
        env["VIRTUAL_ENV"] = str(self.venv_dir)

        # 一个一个安装包
        for package in packages:
            try:
                console.print(f"[dim]正在安装: {package}[/dim]")

                # 使用uv pip install安装单个包，强制安装指定版本
                base_cmd = ["uv", "pip", "install", "--force-reinstall", package]
                cmd = self._build_uv_command(base_cmd)

                with Progress(
                    SpinnerColumn(),
                    TextColumn(f"正在安装 {package}..."),
                    console=console,
                ) as progress:
                    task = progress.add_task("installing", total=None)

                    result = run_command(
                        cmd,
                        cwd=self.work_dir,
                        env=env,
                        capture_output=True
                    )
                    progress.update(task, completed=True)

                if result.returncode == 0:
                    console.print(f"[green]✓ {package} 安装成功[/green]")
                    successful_installs += 1
                else:
                    console.print(f"[yellow]✗ {package} 安装失败，跳过[/yellow]")
                    failed_packages.append(package)
                    if "not found in the package registry" in result.stderr or "No solution found" in result.stderr:
                        console.print(f"[dim]  原因: 包不存在于PyPI[/dim]")
                    else:
                        console.print(f"[dim]  原因: {result.stderr.strip()[:100]}[/dim]")

            except Exception as e:
                console.print(f"[yellow]✗ {package} 安装时出错: {e}[/yellow]")
                failed_packages.append(package)

        # 显示安装结果
        if successful_installs > 0:
            console.print(f"[green]成功安装 {successful_installs} 个包[/green]")

        if failed_packages:
            console.print(f"[yellow]跳过 {len(failed_packages)} 个包: {', '.join(failed_packages)}[/yellow]")

        # 只要有一个包安装成功就认为成功
        return successful_installs > 0

    def install_build_tools(self) -> bool:
        """安装构建工具（强制安装正确版本）"""
        build_tools = ["pyinstaller==5.13.2", "pyarmor==8.4.7"]

        console.print("[blue]检查并安装构建工具[/blue]")

        for tool in build_tools:
            tool_name = tool.split("==")[0]
            expected_version = tool.split("==")[1]

            # 总是检查版本，如果不正确就强制重新安装
            if not self._check_tool_version(tool_name, expected_version):
                console.print(f"[yellow]{tool_name} 版本不正确或未安装，强制安装 {tool}[/yellow]")
                if not self._install_single_tool(tool):
                    return False
            else:
                console.print(f"[green]{tool_name} {expected_version} 版本正确[/green]")

        console.print("[green]所有必要工具已准备就绪[/green]")
        return True

    def _check_tool_version(self, module_name: str, expected_version: str) -> bool:
        """检查工具版本是否正确"""
        try:
            if module_name == "pyinstaller":
                python_exe = self.get_python_executable()
                version_cmd = [python_exe, "-c", "import PyInstaller; print(PyInstaller.__version__)"]
            else:  # pyarmor
                # pyarmor 8.4.7 使用命令行方式检查版本
                pyarmor_exe = self.get_tool_executable("pyarmor")
                if not pyarmor_exe:
                    return False
                version_cmd = [pyarmor_exe, "--version"]

            result = run_command(version_cmd, capture_output=True)
            if result.returncode == 0:
                if module_name == "pyinstaller":
                    installed_version = result.stdout.strip()
                else:  # pyarmor
                    # pyarmor --version 输出格式: "Pyarmor 8.4.7 (trial), 000000, non-profits"
                    output = result.stdout.strip()
                    if "Pyarmor" in output:
                        # 提取版本号
                        import re
                        match = re.search(r'Pyarmor\s+(\d+\.\d+\.\d+)', output)
                        if match:
                            installed_version = match.group(1)
                        else:
                            return False
                    else:
                        return False

                return installed_version == expected_version
        except:
            pass
        return False

    def _install_single_tool(self, tool_name: str) -> bool:
        """安装单个工具"""
        try:
            # 提取实际的模块名（去掉版本号）
            module_name = tool_name.split("==")[0].split(">=")[0].split("<=")[0]

            # 对于pyinstaller和pyarmor，检查版本并强制重新安装指定版本
            if module_name in ["pyinstaller", "pyarmor"]:
                expected_version = tool_name.split("==")[1] if "==" in tool_name else None

                # 注意：这里不再跳过安装，因为我们在 install_build_tools 中已经检查过了
                # 如果调用到这里，说明需要强制重新安装
                console.print(f"[yellow]强制安装指定版本 {tool_name}...[/yellow]")

                env = os.environ.copy()
                env["VIRTUAL_ENV"] = str(self.venv_dir)

                # 1. 先清理该包的缓存
                console.print(f"[dim]清理 {module_name} 的缓存...[/dim]")
                try:
                    cache_clean_cmd = ["uv", "cache", "clean", module_name]
                    if self.cache_dir:
                        cache_clean_cmd.extend(["--cache-dir", str(self.cache_dir)])
                    run_command(cache_clean_cmd, cwd=self.work_dir, capture_output=True)
                    console.print(f"[dim]已清理 {module_name} 缓存[/dim]")
                except:
                    pass  # 缓存清理失败不影响继续

                # 2. 卸载可能存在的其他版本
                console.print(f"[dim]卸载现有的 {module_name}...[/dim]")
                try:
                    # uv pip uninstall 不支持 -y 参数，直接卸载
                    uninstall_cmd = ["uv", "pip", "uninstall", module_name]
                    if self.cache_dir:
                        uninstall_cmd.extend(["--cache-dir", str(self.cache_dir)])
                    run_command(uninstall_cmd, cwd=self.work_dir, env=env, capture_output=True)
                    console.print(f"[dim]已卸载现有的 {module_name}[/dim]")
                except:
                    pass  # 如果没有安装则忽略错误

                # 3. 强制重新下载并安装指定版本
                base_cmd = ["uv", "pip", "install", "--force-reinstall", "--no-cache", tool_name]
                cmd = self._build_uv_command(base_cmd)
            else:
                # 检查工具是否已在虚拟环境中安装
                python_exe = self.get_python_executable()
                check_cmd = [python_exe, "-c", f"import {module_name}"]

                try:
                    run_command(check_cmd, capture_output=True)
                    console.print(f"[green]{module_name} 已安装[/green]")
                    return True
                except:
                    pass

                # 安装工具
                console.print(f"[yellow]{tool_name} 未安装，正在自动安装...[/yellow]")
                base_cmd = ["uv", "pip", "install", tool_name]
                cmd = self._build_uv_command(base_cmd)

            with Progress(
                SpinnerColumn(),
                TextColumn(f"正在安装 {tool_name}..."),
                console=console,
            ) as progress:
                task = progress.add_task("installing", total=None)

                env = os.environ.copy()
                env["VIRTUAL_ENV"] = str(self.venv_dir)

                result = run_command(cmd, cwd=self.work_dir, env=env)
                progress.update(task, completed=True)

            if result.returncode == 0:
                console.print(f"[green]{tool_name} 安装成功[/green]")

                # 如果是 pyinstaller 或 pyarmor，验证版本是否正确
                if module_name in ["pyinstaller", "pyarmor"]:
                    # 验证安装的版本
                    try:
                        if module_name == "pyinstaller":
                            python_exe = self.get_python_executable()
                            version_cmd = [python_exe, "-c", "import PyInstaller; print(PyInstaller.__version__)"]
                            expected_version = "5.13.2"
                        else:  # pyarmor
                            # pyarmor 8.4.7 使用命令行方式检查版本
                            pyarmor_exe = self.get_tool_executable("pyarmor")
                            if not pyarmor_exe:
                                console.print(f"[yellow]无法找到 {module_name} 可执行文件[/yellow]")
                                return True  # 跳过版本验证，但不影响安装成功
                            version_cmd = [pyarmor_exe, "--version"]
                            expected_version = "8.4.7"

                        version_result = run_command(version_cmd, capture_output=True)
                        if version_result.returncode == 0:
                            if module_name == "pyinstaller":
                                installed_version = version_result.stdout.strip()
                            else:  # pyarmor
                                # pyarmor --version 输出格式: "Pyarmor 8.4.7 (trial), 000000, non-profits"
                                output = version_result.stdout.strip()
                                if "Pyarmor" in output:
                                    # 提取版本号
                                    import re
                                    match = re.search(r'Pyarmor\s+(\d+\.\d+\.\d+)', output)
                                    if match:
                                        installed_version = match.group(1)
                                    else:
                                        console.print(f"[yellow]无法解析 {module_name} 版本信息[/yellow]")
                                        return True  # 跳过版本验证，但不影响安装成功
                                else:
                                    console.print(f"[yellow]无法解析 {module_name} 版本信息[/yellow]")
                                    return True  # 跳过版本验证，但不影响安装成功

                            if installed_version == expected_version:
                                console.print(f"[green]{module_name} {installed_version} 版本正确[/green]")
                            else:
                                console.print(f"[yellow]警告: {module_name} 版本不匹配，期望 {expected_version}，实际 {installed_version}[/yellow]")
                        else:
                            console.print(f"[yellow]无法验证 {module_name} 版本[/yellow]")
                    except Exception as e:
                        console.print(f"[yellow]验证 {module_name} 版本时出错: {e}[/yellow]")

                    # 安装必要的依赖
                    console.print(f"[dim]安装 {module_name} 的必要依赖...[/dim]")
                    try:
                        if module_name == "pyinstaller":
                            # PyInstaller 的核心依赖
                            deps = ["altgraph", "pefile", "pywin32-ctypes", "setuptools"]
                        else:  # pyarmor
                            # PyArmor 的核心依赖
                            deps = ["setuptools"]

                        for dep in deps:
                            dep_cmd = ["uv", "pip", "install", dep]
                            dep_cmd = self._build_uv_command(dep_cmd)
                            try:
                                dep_result = run_command(dep_cmd, cwd=self.work_dir, env=env, capture_output=True)
                                if dep_result.returncode == 0:
                                    console.print(f"[dim]✓ {dep} 安装成功[/dim]")
                                else:
                                    console.print(f"[yellow]✗ {dep} 安装失败[/yellow]")
                            except:
                                console.print(f"[yellow]✗ {dep} 安装出错[/yellow]")
                    except Exception as e:
                        console.print(f"[yellow]安装依赖时出错: {e}[/yellow]")

                return True
            else:
                console.print(f"[red]{tool_name} 安装失败[/red]")
                return False

        except Exception as e:
            console.print(f"[red]安装 {tool_name} 时出错: {e}[/red]")
            return False

    def get_python_executable(self) -> str:
        """获取虚拟环境中的Python可执行文件路径"""
        if sys.platform == "win32":
            python_exe = self.venv_dir / "Scripts" / "python.exe"
        else:
            python_exe = self.venv_dir / "bin" / "python"

        if python_exe.exists():
            return str(python_exe)
        else:
            # 回退到系统Python
            return sys.executable

    def get_tool_executable(self, tool_name: str) -> Optional[str]:
        """获取工具的可执行文件路径（优先使用虚拟环境中的工具）"""
        if not self.venv_dir or not self.venv_dir.exists():
            console.print(f"[yellow]虚拟环境不存在，无法获取 {tool_name} 工具[/yellow]")
            return None

        if sys.platform == "win32":
            scripts_dir = self.venv_dir / "Scripts"
            tool_exe = scripts_dir / f"{tool_name}.exe"
            if not tool_exe.exists():
                tool_exe = scripts_dir / tool_name
        else:
            bin_dir = self.venv_dir / "bin"
            tool_exe = bin_dir / tool_name

        if tool_exe.exists():
            console.print(f"[dim]使用虚拟环境中的 {tool_name}: {tool_exe}[/dim]")
            return str(tool_exe)

        # 不再回退到系统工具，确保使用虚拟环境中的版本
        console.print(f"[red]{tool_name} 在虚拟环境中未找到: {tool_exe}[/red]")
        return None

    def get_environment_info(self) -> Dict[str, Any]:
        """获取环境信息"""
        python_exe = self.get_python_executable()

        info = {
            "work_dir": str(self.work_dir),
            "venv_dir": str(self.venv_dir),
            "python_executable": python_exe,
            "uv_available": self.uv_available,
            "venv_exists": self.venv_dir.exists(),
        }

        # 获取工具路径
        for tool in ["pyinstaller", "pyarmor"]:
            info[f"{tool}_executable"] = self.get_tool_executable(tool)

        return info

    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        cache_info = {
            "cache_enabled": not self.no_cache,
            "cache_dir": str(self.cache_dir) if self.cache_dir else None,
            "refresh_enabled": self.refresh,
        }

        if self.cache_dir and self.cache_dir.exists():
            try:
                # 计算缓存目录大小
                total_size = 0
                file_count = 0
                for root, _, files in os.walk(self.cache_dir):
                    for file in files:
                        file_path = Path(root) / file
                        if file_path.exists():
                            total_size += file_path.stat().st_size
                            file_count += 1

                cache_info.update({
                    "cache_size_bytes": total_size,
                    "cache_size_human": self._format_size(total_size),
                    "cache_file_count": file_count,
                })
            except Exception as e:
                cache_info["cache_error"] = str(e)

        return cache_info

    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def clean_cache(self, package_name: Optional[str] = None) -> bool:
        """清理缓存"""
        if not self.cache_dir or self.no_cache:
            console.print("[yellow]缓存未启用，无需清理[/yellow]")
            return True

        try:
            if package_name:
                # 清理特定包的缓存
                cmd = self._build_uv_command(["uv", "cache", "clean", package_name])
                console.print(f"[blue]清理 {package_name} 的缓存...[/blue]")
            else:
                # 清理所有缓存
                cmd = self._build_uv_command(["uv", "cache", "clean"])
                console.print("[blue]清理所有缓存...[/blue]")

            result = run_command(cmd, capture_output=True)

            if result.returncode == 0:
                console.print("[green]缓存清理成功[/green]")
                return True
            else:
                console.print(f"[red]缓存清理失败: {result.stderr}[/red]")
                return False

        except Exception as e:
            console.print(f"[red]清理缓存时出错: {e}[/red]")
            return False

    def prune_cache(self) -> bool:
        """清理未使用的缓存条目"""
        if not self.cache_dir or self.no_cache:
            console.print("[yellow]缓存未启用，无需清理[/yellow]")
            return True

        try:
            cmd = self._build_uv_command(["uv", "cache", "prune"])
            console.print("[blue]清理未使用的缓存条目...[/blue]")

            result = run_command(cmd, capture_output=True)

            if result.returncode == 0:
                console.print("[green]缓存清理成功[/green]")
                return True
            else:
                console.print(f"[red]缓存清理失败: {result.stderr}[/red]")
                return False

        except Exception as e:
            console.print(f"[red]清理缓存时出错: {e}[/red]")
            return False

    def cleanup(self) -> None:
        """清理临时文件（保留虚拟环境供下次复用）"""
        # 不再删除虚拟环境，保留以供下次复用
        console.print(f"[dim]虚拟环境已保留供下次复用: {self.venv_dir}[/dim]")

        # 可以在这里清理其他临时文件，但保留虚拟环境
        pass

    def cleanup_project_environment(self, packages: List[str], project_path: Optional[Path] = None) -> bool:
        """清理特定项目的虚拟环境"""
        try:
            env_hash = self._calculate_env_hash(packages, project_path)
            env_dir = self.shared_envs_dir / f"env_{env_hash}"

            if env_dir.exists():
                console.print(f"[yellow]清理项目虚拟环境: {env_dir}[/yellow]")
                import shutil
                shutil.rmtree(env_dir, ignore_errors=True)
                console.print("[green]项目虚拟环境清理完成[/green]")
                return True
            else:
                console.print("[yellow]项目虚拟环境不存在，无需清理[/yellow]")
                return True
        except Exception as e:
            console.print(f"[red]清理项目虚拟环境时出错: {e}[/red]")
            return False

    def cleanup_all_environments(self) -> bool:
        """清理所有虚拟环境"""
        try:
            if self.shared_envs_dir.exists():
                console.print(f"[yellow]清理所有虚拟环境: {self.shared_envs_dir}[/yellow]")
                import shutil
                shutil.rmtree(self.shared_envs_dir, ignore_errors=True)
                # 重新创建目录
                self.shared_envs_dir.mkdir(parents=True, exist_ok=True)
                console.print("[green]所有虚拟环境清理完成[/green]")
                return True
            else:
                console.print("[yellow]虚拟环境目录不存在，无需清理[/yellow]")
                return True
        except Exception as e:
            console.print(f"[red]清理所有虚拟环境时出错: {e}[/red]")
            return False
