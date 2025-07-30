"""
UVInstaller - Python应用程序打包工具

支持依赖分析、环境隔离、打包和加固一体化解决方案。
"""

__version__ = "0.1.1"
__author__ = "UVInstaller Team"
__email__ = "team@uvinstaller.com"
__description__ = "Python应用程序打包工具，支持依赖分析、环境隔离、打包和加固一体化解决方案"

from .main import main

__all__ = ["main", "__version__"]
