"""
测试工具函数模块
"""

import pytest
import tempfile
from pathlib import Path
from uvinstaller.utils import (
    validate_python_file, get_file_size, format_duration,
    get_platform_info, is_windows, get_executable_extension
)


class TestUtils:
    """工具函数测试"""
    
    def test_validate_python_file_valid(self):
        """测试验证有效的Python文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('Hello, World!')")
            temp_file = Path(f.name)
        
        try:
            assert validate_python_file(temp_file) is True
        finally:
            temp_file.unlink()
    
    def test_validate_python_file_invalid_syntax(self):
        """测试验证有语法错误的Python文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print(")  # 语法错误
            temp_file = Path(f.name)
        
        try:
            assert validate_python_file(temp_file) is False
        finally:
            temp_file.unlink()
    
    def test_validate_python_file_not_python(self):
        """测试验证非Python文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is not a Python file")
            temp_file = Path(f.name)
        
        try:
            assert validate_python_file(temp_file) is False
        finally:
            temp_file.unlink()
    
    def test_validate_python_file_not_exists(self):
        """测试验证不存在的文件"""
        non_existent_file = Path("non_existent_file.py")
        assert validate_python_file(non_existent_file) is False
    
    def test_get_file_size(self):
        """测试获取文件大小"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Hello, World!")
            temp_file = Path(f.name)
        
        try:
            size_str = get_file_size(temp_file)
            assert isinstance(size_str, str)
            assert "B" in size_str
        finally:
            temp_file.unlink()
    
    def test_format_duration(self):
        """测试格式化时间持续时间"""
        assert "秒" in format_duration(30)
        assert "分钟" in format_duration(120)
        assert "小时" in format_duration(3700)
    
    def test_get_platform_info(self):
        """测试获取平台信息"""
        system, arch = get_platform_info()
        assert isinstance(system, str)
        assert isinstance(arch, str)
        assert len(system) > 0
        assert len(arch) > 0
    
    def test_is_windows(self):
        """测试Windows检测"""
        result = is_windows()
        assert isinstance(result, bool)
    
    def test_get_executable_extension(self):
        """测试获取可执行文件扩展名"""
        ext = get_executable_extension()
        assert isinstance(ext, str)
        # 在Windows上应该是.exe，其他平台应该是空字符串
        if is_windows():
            assert ext == ".exe"
        else:
            assert ext == ""
