# UVInstaller

Python应用程序打包工具，支持依赖分析、环境隔离、打包和加固一体化解决方案。

## 特性

- 🚀 **自动依赖分析**: 智能分析项目依赖，支持第三方库和标准库识别
- 🔒 **环境隔离**: 使用 uv 创建独立虚拟环境，避免依赖冲突
- 📦 **一键打包**: 基于 PyInstaller 5.13.2，生成单文件可执行程序
- 🛡️ **代码加固**: 集成 PyArmor 8.4.7，提供代码保护和混淆
- 💾 **智能缓存**: 支持包缓存和环境复用，提升打包速度
- 🔧 **灵活配置**: 支持静态文件、隐藏导入等高级配置

## 安装

```bash
pip install uvinstaller
```

## 快速开始

### 基本用法

```bash
# 打包 Python 文件
ui your_script.py

# 显示详细输出
ui your_script.py --verbose

# 跳过代码保护
ui your_script.py --no-protection
```

### 高级用法

```bash
# 添加静态文件
ui your_script.py --add-data "data.txt:." --add-data "config/:config/"

# 指定隐藏导入模块
ui your_script.py --hidden-import requests --hidden-import numpy

# 自定义工作目录
ui your_script.py --work-dir ./build

# 禁用缓存
ui your_script.py --no-cache
```

### 缓存管理

```bash
# 查看缓存信息
ui --cache-info

# 清理所有缓存
ui --clean-cache

# 清理项目虚拟环境
ui your_script.py --clean-env

# 清理所有虚拟环境
ui --clean-all-env
```

## 命令行参数

| 参数 | 说明 |
|------|------|
| `--work-dir, -w` | 指定工作目录（默认使用临时目录） |
| `--no-protection` | 跳过代码保护步骤 |
| `--verbose, -v` | 显示详细输出 |
| `--cache-dir` | 指定缓存目录 |
| `--no-cache` | 禁用缓存 |
| `--refresh` | 强制刷新缓存 |
| `--add-data` | 添加静态文件，格式: 源路径:目标路径 |
| `--hidden-import` | 指定隐藏导入的模块名 |
| `--clean-cache` | 清理所有缓存后退出 |
| `--cache-info` | 显示缓存信息后退出 |
| `--clean-env` | 清理当前项目的虚拟环境后退出 |
| `--clean-all-env` | 清理所有虚拟环境后退出 |
| `--version` | 显示版本信息 |

## 工作流程

1. **依赖分析**: 自动扫描 Python 文件，识别导入的模块
2. **环境准备**: 创建或复用虚拟环境，安装必要依赖
3. **应用打包**: 使用 PyInstaller 生成可执行文件
4. **代码加固**: 使用 PyArmor 对可执行文件进行保护
5. **文件部署**: 将最终文件复制到源文件目录

## 技术栈

- **uv**: 快速 Python 包管理器
- **PyInstaller 5.13.2**: Python 应用打包工具
- **PyArmor 8.4.7**: Python 代码保护工具
- **Click**: 命令行界面框架
- **Rich**: 终端美化输出

## 许可证

MIT License

## 更新日志

### v0.1.1 (最新)
- ✨ 新增 `--hidden-import` 参数支持
- 🔧 支持指定 PyInstaller 隐藏导入模块
- 📝 改进日志输出和用户体验

### v0.1.0
- 🎉 首次发布
- 🚀 基础打包功能
- 🔒 代码保护集成
- 💾 缓存系统实现
