"""
测试依赖分析模块
"""

import pytest
import tempfile
from pathlib import Path
from uvinstaller.dependency_analyzer import DependencyAnalyzer


class TestDependencyAnalyzer:
    """依赖分析器测试"""
    
    def test_analyze_simple_file(self):
        """测试分析简单Python文件"""
        # 创建临时Python文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
import os
import sys
import requests
from pathlib import Path
""")
            temp_file = Path(f.name)
        
        try:
            analyzer = DependencyAnalyzer()
            result = analyzer.analyze_file(temp_file)
            
            # 检查结果
            assert 'imports' in result
            assert 'third_party' in result
            assert 'stdlib' in result
            
            # 检查具体导入
            assert 'os' in result['stdlib']
            assert 'sys' in result['stdlib']
            assert 'pathlib' in result['stdlib']
            assert 'requests' in result['third_party']
            
        finally:
            temp_file.unlink()
    
    def test_analyze_file_with_syntax_error(self):
        """测试分析有语法错误的文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import os\nprint(")  # 语法错误
            temp_file = Path(f.name)
        
        try:
            analyzer = DependencyAnalyzer()
            result = analyzer.analyze_file(temp_file)
            
            # 即使有语法错误，也应该返回结果结构
            assert 'imports' in result
            assert 'third_party' in result
            assert 'stdlib' in result
            
        finally:
            temp_file.unlink()
    
    def test_get_requirements_list(self):
        """测试获取requirements列表"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
import requests
import click
import rich
""")
            temp_file = Path(f.name)
        
        try:
            analyzer = DependencyAnalyzer()
            analyzer.analyze_file(temp_file)
            requirements = analyzer.get_requirements_list()
            
            # 检查requirements列表
            assert isinstance(requirements, list)
            assert 'requests' in requirements
            assert 'click' in requirements
            assert 'rich' in requirements
            
        finally:
            temp_file.unlink()
