"""
主程序和CLI接口

UVInstaller的主要入口点和命令行界面。
"""

import sys
import time
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from . import __version__
from .utils import (
    console, validate_python_file, create_temp_dir, cleanup_temp_dir,
    copy_file, format_duration, get_file_size, run_command
)
from .dependency_analyzer import DependencyAnalyzer
from .environment_manager import EnvironmentManager
from .packager import Packager
from .security import SecurityProtector


def print_banner():
    """打印程序横幅"""
    banner_text = Text()
    banner_text.append("UVInstaller", style="bold blue")
    banner_text.append(f" v{__version__}\n", style="dim")
    banner_text.append("Python应用程序打包工具", style="green")

    panel = Panel(
        banner_text,
        border_style="blue",
        padding=(1, 2)
    )
    console.print(panel)


def print_step(step_num: int, total_steps: int, description: str):
    """打印步骤信息"""
    console.print(f"\n[bold blue]步骤 {step_num}/{total_steps}: {description}[/bold blue]")


@click.command()
@click.argument('file_path', type=click.Path(exists=True, path_type=Path), required=False)
@click.option(
    '--work-dir', '-w',
    type=click.Path(path_type=Path),
    help='指定工作目录（默认使用临时目录）'
)
@click.option(
    '--no-protection',
    is_flag=True,
    help='跳过代码保护步骤'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='显示详细输出'
)
@click.option(
    '--cache-dir',
    type=click.Path(path_type=Path),
    help='指定缓存目录（默认使用系统缓存目录）'
)
@click.option(
    '--no-cache',
    is_flag=True,
    help='禁用缓存'
)
@click.option(
    '--refresh',
    is_flag=True,
    help='强制刷新缓存'
)
@click.option(
    '--clean-cache',
    is_flag=True,
    help='清理所有缓存后退出'
)
@click.option(
    '--cache-info',
    is_flag=True,
    help='显示缓存信息后退出'
)
@click.option(
    '--clean-env',
    is_flag=True,
    help='清理当前项目的虚拟环境后退出'
)
@click.option(
    '--clean-all-env',
    is_flag=True,
    help='清理所有虚拟环境后退出'
)
@click.option(
    '--version',
    is_flag=True,
    help='显示版本信息'
)
@click.option(
    '--add-data',
    multiple=True,
    help='添加静态文件或目录到打包中，格式: 源路径:目标路径 (可多次使用)'
)
@click.option(
    '--hidden-import',
    multiple=True,
    help='指定隐藏导入的模块名 (可多次使用)'
)
def main(
    file_path: Optional[Path],
    work_dir: Optional[Path],
    no_protection: bool,
    verbose: bool,
    cache_dir: Optional[Path],
    no_cache: bool,
    refresh: bool,
    clean_cache: bool,
    cache_info: bool,
    clean_env: bool,
    clean_all_env: bool,
    version: bool,
    add_data: tuple,
    hidden_import: tuple
):
    """
    UVInstaller - Python应用程序打包工具

    FILE_PATH: 要打包的Python文件路径
    """
    if version:
        console.print(f"UVInstaller v{__version__}")
        return

    # 处理缓存和环境相关的选项
    if clean_cache or cache_info or clean_env or clean_all_env:
        # 创建临时环境管理器来处理操作
        temp_work_dir = Path.cwd()
        env_manager = EnvironmentManager(temp_work_dir, cache_dir, no_cache, refresh)

        if cache_info:
            # 显示缓存信息
            print_banner()
            console.print("\n[bold blue]缓存信息[/bold blue]")
            cache_info_data = env_manager.get_cache_info()

            console.print(f"缓存状态: {'启用' if cache_info_data['cache_enabled'] else '禁用'}")
            if cache_info_data['cache_dir']:
                console.print(f"缓存目录: {cache_info_data['cache_dir']}")
                if 'cache_size_human' in cache_info_data:
                    console.print(f"缓存大小: {cache_info_data['cache_size_human']}")
                    console.print(f"文件数量: {cache_info_data['cache_file_count']}")
                if cache_info_data.get('cache_error'):
                    console.print(f"[yellow]缓存错误: {cache_info_data['cache_error']}[/yellow]")
            console.print(f"刷新模式: {'启用' if cache_info_data['refresh_enabled'] else '禁用'}")
            return

        if clean_cache:
            # 清理缓存
            print_banner()
            console.print("\n[bold blue]清理缓存[/bold blue]")
            if env_manager.clean_cache():
                console.print("[green]缓存清理完成[/green]")
            else:
                console.print("[red]缓存清理失败[/red]")
                sys.exit(1)
            return

        if clean_all_env:
            # 清理所有虚拟环境
            print_banner()
            console.print("\n[bold blue]清理所有虚拟环境[/bold blue]")
            if env_manager.cleanup_all_environments():
                console.print("[green]所有虚拟环境清理完成[/green]")
            else:
                console.print("[red]虚拟环境清理失败[/red]")
                sys.exit(1)
            return

        if clean_env:
            # 清理当前项目的虚拟环境
            if not file_path:
                console.print("[red]错误: 清理项目环境需要指定文件路径[/red]")
                console.print("使用 'ui <file_path> --clean-env' 清理特定项目的虚拟环境")
                sys.exit(1)

            print_banner()
            console.print("\n[bold blue]清理项目虚拟环境[/bold blue]")

            # 分析项目依赖以计算环境哈希
            analyzer = DependencyAnalyzer()
            dependencies = analyzer.analyze_project(file_path)
            third_party_packages = list(dependencies['third_party'])

            if env_manager.cleanup_project_environment(third_party_packages, file_path):
                console.print("[green]项目虚拟环境清理完成[/green]")
            else:
                console.print("[red]项目虚拟环境清理失败[/red]")
                sys.exit(1)
            return

    # 检查是否提供了文件路径
    if not file_path:
        console.print("[red]错误: 缺少必需的参数 'FILE_PATH'[/red]")
        console.print("使用 'ui --help' 查看帮助信息")
        sys.exit(1)

    # 打印横幅
    print_banner()

    start_time = time.time()
    temp_dir = None

    try:
        # 验证输入文件
        if not validate_python_file(file_path):
            console.print("[red]输入文件验证失败[/red]")
            sys.exit(1)

        # 设置工作目录
        if work_dir:
            work_dir = Path(work_dir).resolve()
            work_dir.mkdir(parents=True, exist_ok=True)
        else:
            work_dir = create_temp_dir()
            temp_dir = work_dir

        console.print(f"[blue]工作目录: {work_dir}[/blue]")

        # 初始化组件
        env_manager = EnvironmentManager(work_dir, cache_dir, no_cache, refresh)
        analyzer = DependencyAnalyzer()
        packager = Packager(env_manager)
        protector = SecurityProtector(env_manager)

        # 步骤1: 检查必要工具
        print_step(1, 6, "检查必要工具")
        console.print("检查必要工具...")

        if not env_manager.ensure_uv_installed():
            console.print("[red]uv安装失败，无法继续[/red]")
            sys.exit(1)

        console.print("[green]所有必要工具已准备就绪[/green]")

        # 显示缓存信息
        if verbose:
            cache_info_data = env_manager.get_cache_info()
            console.print(f"[dim]缓存: {'启用' if cache_info_data['cache_enabled'] else '禁用'}")
            if cache_info_data['cache_dir']:
                console.print(f"[dim]缓存目录: {cache_info_data['cache_dir']}[/dim]")
                if 'cache_size_human' in cache_info_data:
                    console.print(f"[dim]缓存大小: {cache_info_data['cache_size_human']}[/dim]")

        # 步骤2: 分析依赖
        print_step(2, 6, "分析依赖")
        dependencies = analyzer.analyze_project(file_path)
        analyzer.print_summary()

        # 步骤3: 创建或复用虚拟环境
        print_step(3, 6, "创建或复用虚拟环境")
        third_party_packages = list(dependencies['third_party'])

        if not env_manager.create_or_reuse_virtual_environment(third_party_packages, file_path):
            console.print("[red]虚拟环境创建失败[/red]")
            sys.exit(1)

        # 检查是否需要安装依赖（如果是复用的环境，可能已经安装了）
        need_install_deps = False
        need_install_tools = False

        if third_party_packages:
            # 检查依赖是否已安装
            python_exe = env_manager.get_python_executable()
            for package in third_party_packages:
                package_name = package.split("==")[0].split(">=")[0].split("<=")[0]
                try:
                    check_cmd = [python_exe, "-c", f"import {package_name}"]
                    run_command(check_cmd, capture_output=True)
                except:
                    need_install_deps = True
                    break

        # 检查构建工具是否已安装且版本正确
        for tool in ["pyinstaller", "pyarmor"]:
            tool_exe = env_manager.get_tool_executable(tool)
            if not tool_exe:
                need_install_tools = True
                break
            else:
                # 检查版本是否正确
                expected_version = "5.13.2" if tool == "pyinstaller" else "8.4.7"
                if not env_manager._check_tool_version(tool, expected_version):
                    console.print(f"[yellow]{tool} 版本不正确，需要重新安装[/yellow]")
                    need_install_tools = True
                    break

        # 安装依赖（如果需要）
        if need_install_deps and third_party_packages:
            console.print("[blue]安装项目依赖...[/blue]")
            if not env_manager.install_dependencies(third_party_packages):
                console.print("[red]依赖安装失败[/red]")
                sys.exit(1)
        elif third_party_packages:
            console.print("[green]项目依赖已存在，跳过安装[/green]")

        # 安装构建工具（如果需要）
        if need_install_tools:
            console.print("[blue]安装构建工具...[/blue]")
            if not env_manager.install_build_tools():
                console.print("[red]构建工具安装失败[/red]")
                sys.exit(1)
        else:
            console.print("[green]构建工具已存在，跳过安装[/green]")

        # 步骤4: 打包应用程序
        print_step(4, 6, "打包应用程序")

        # 处理静态文件参数
        data_files = []
        if add_data:
            console.print(f"[blue]处理 {len(add_data)} 个静态文件/目录[/blue]")
            for data_spec in add_data:
                if ':' not in data_spec:
                    console.print(f"[red]错误: 静态文件格式不正确: {data_spec}[/red]")
                    console.print("[red]正确格式: 源路径:目标路径[/red]")
                    sys.exit(1)

                src_path, dst_path = data_spec.split(':', 1)
                src_path = Path(src_path).resolve()

                if not src_path.exists():
                    console.print(f"[red]错误: 静态文件不存在: {src_path}[/red]")
                    sys.exit(1)

                data_files.append((str(src_path), dst_path))
                console.print(f"[dim]添加静态文件: {src_path} -> {dst_path}[/dim]")

        # 处理隐藏导入参数
        if hidden_import:
            console.print(f"[blue]处理 {len(hidden_import)} 个隐藏导入模块[/blue]")
            for module in hidden_import:
                console.print(f"[dim]添加隐藏导入: {module}[/dim]")

        build_options = {
            'onefile': True,
            'console': True,
            'verbose': verbose,
            'data_files': data_files,
            'hidden_imports': list(hidden_import) if hidden_import else []
        }

        if not packager.build_executable(file_path, **build_options):
            console.print("[red]应用程序打包失败[/red]")
            sys.exit(1)

        # 步骤5: 代码加固（可选）
        protected_file = None
        if not no_protection:
            print_step(5, 6, "代码加固")
            build_info = packager.get_build_info()
            if build_info['output_exists']:
                output_file = Path(build_info['output_file'])
                if protector.protect_executable(output_file, file_path):
                    protection_info = protector.get_protection_info()
                    if protection_info['protected_exists']:
                        protected_file = Path(protection_info['protected_file'])
                else:
                    console.print("[yellow]代码保护失败，将使用未保护的版本[/yellow]")
            else:
                console.print("[red]找不到要保护的可执行文件[/red]")
        else:
            print_step(5, 6, "代码加固")
            console.print("[yellow]跳过代码保护步骤[/yellow]")

        # 步骤6: 部署输出文件
        print_step(6, 6, "部署输出文件")

        # 确定最终输出文件
        final_file = protected_file if protected_file else Path(packager.get_build_info()['output_file'])

        if final_file and final_file.exists():
            # 生成输出文件名 - 直接使用原文件名但改为.exe扩展名
            output_name = file_path.stem + ".exe"
            output_path = file_path.parent / output_name

            # 复制到源文件目录
            copy_file(final_file, output_path)

            # 显示成功信息
            file_size = get_file_size(output_path)
            duration = format_duration(time.time() - start_time)

            console.print(f"\n[bold green]✅ 打包完成![/bold green]")
            console.print(f"[green]输出文件: {output_path} ({file_size})[/green]")
            console.print(f"[green]总耗时: {duration}[/green]")
        else:
            console.print("[red]最终输出文件不存在[/red]")
            sys.exit(1)

    except KeyboardInterrupt:
        console.print("\n[yellow]用户中断操作[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]发生错误: {e}[/red]")
        if verbose:
            import traceback
            console.print(f"[red]详细错误信息:\n{traceback.format_exc()}[/red]")
        sys.exit(1)
    finally:
        # 清理临时文件（但保留虚拟环境）
        if temp_dir:
            console.print(f"\n[blue]清理临时文件[/blue]")
            try:
                # 清理各组件的临时文件
                if 'packager' in locals():
                    packager.cleanup_build_files()
                if 'protector' in locals():
                    protector.cleanup_protection_files()
                # 注意：不再清理虚拟环境，保留以供下次复用
                # if 'env_manager' in locals():
                #     env_manager.cleanup()

                # 清理临时目录
                cleanup_temp_dir(temp_dir)
                console.print("[green]清理完成（虚拟环境已保留供下次复用）[/green]")
            except Exception as e:
                console.print(f"[yellow]清理时出现警告: {e}[/yellow]")


if __name__ == '__main__':
    main()
