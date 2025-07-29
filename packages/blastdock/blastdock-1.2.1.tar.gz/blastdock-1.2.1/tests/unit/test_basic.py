"""
Basic unit tests to verify test framework
"""

import pytest
import sys
import os


def test_python_version():
    """Test Python version is appropriate"""
    assert sys.version_info >= (3, 8)


def test_imports():
    """Test basic imports work"""
    import click
    import yaml
    import docker
    import rich
    import jinja2
    import pydantic
    
    assert click.__version__
    assert pydantic.VERSION


def test_project_structure():
    """Test project structure exists"""
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    # Check main package exists
    blastdock_path = os.path.join(project_root, 'blastdock')
    assert os.path.exists(blastdock_path)
    
    # Check main modules exist
    assert os.path.exists(os.path.join(blastdock_path, '__init__.py'))
    assert os.path.exists(os.path.join(blastdock_path, 'cli'))
    assert os.path.exists(os.path.join(blastdock_path, 'utils'))
    assert os.path.exists(os.path.join(blastdock_path, 'traefik'))


def test_math_operations():
    """Test basic math operations for framework verification"""
    assert 2 + 2 == 4
    assert 5 * 3 == 15
    assert 10 / 2 == 5.0


class TestBasicClass:
    """Test basic class functionality"""
    
    def test_class_instantiation(self):
        """Test class can be instantiated"""
        class TestClass:
            def __init__(self, value):
                self.value = value
        
        instance = TestClass(42)
        assert instance.value == 42
    
    def test_class_methods(self):
        """Test class methods work"""
        class Calculator:
            def add(self, a, b):
                return a + b
            
            def multiply(self, a, b):
                return a * b
        
        calc = Calculator()
        assert calc.add(2, 3) == 5
        assert calc.multiply(4, 5) == 20


@pytest.mark.parametrize("input_value,expected", [
    (1, 1),
    (2, 4),
    (3, 9),
    (4, 16),
    (5, 25)
])
def test_parametrized_square(input_value, expected):
    """Test parametrized test functionality"""
    assert input_value ** 2 == expected


def test_exception_handling():
    """Test exception handling works"""
    with pytest.raises(ValueError):
        raise ValueError("Test exception")
    
    with pytest.raises(ZeroDivisionError):
        result = 1 / 0


def test_fixture_usage(tmp_path):
    """Test pytest fixtures work"""
    # Test temporary directory fixture
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")
    
    assert test_file.read_text() == "test content"


def test_mock_functionality():
    """Test mock functionality is available"""
    from unittest.mock import Mock, patch
    
    mock_obj = Mock()
    mock_obj.method.return_value = "mocked"
    
    assert mock_obj.method() == "mocked"
    
    with patch('os.getcwd', return_value='/mocked/path'):
        assert os.getcwd() == '/mocked/path'