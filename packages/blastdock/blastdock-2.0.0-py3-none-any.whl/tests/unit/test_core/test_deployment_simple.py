"""
Simplified working deployment tests
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

@patch('blastdock.core.deployment_manager.get_config')
@patch('blastdock.core.deployment_manager.TemplateManager')
@patch('blastdock.core.deployment_manager.TraefikIntegrator')
def test_deployment_manager_imports(mock_traefik, mock_template, mock_config):
    """Test that DeploymentManager can be imported and initialized"""
    from blastdock.core.deployment_manager import DeploymentManager
    manager = DeploymentManager()
    assert manager is not None

@patch('blastdock.core.deployment_manager.get_config')
@patch('blastdock.core.deployment_manager.TemplateManager')
@patch('blastdock.core.deployment_manager.TraefikIntegrator')
def test_deployment_validate_project_name(mock_traefik, mock_template, mock_config):
    """Test project name validation"""
    from blastdock.core.deployment_manager import DeploymentManager
    manager = DeploymentManager()
    
    # Valid names
    assert manager._validate_project_name('valid-name') is True
    assert manager._validate_project_name('test123') is True
    
    # Invalid names
    assert manager._validate_project_name('Invalid_Name') is False
    assert manager._validate_project_name('') is False

@patch('blastdock.core.deployment_manager.get_config')
@patch('blastdock.core.deployment_manager.TemplateManager')
@patch('blastdock.core.deployment_manager.TraefikIntegrator')
def test_deployment_create_directory(mock_traefik, mock_template, mock_config):
    """Test project directory creation"""
    from blastdock.core.deployment_manager import DeploymentManager
    manager = DeploymentManager()
    
    with patch('pathlib.Path.mkdir') as mock_mkdir:
        result = manager._create_project_directory('test-project')
        assert isinstance(result, Path)

@patch('blastdock.core.deployment_manager.get_config')
@patch('blastdock.core.deployment_manager.TemplateManager')
@patch('blastdock.core.deployment_manager.TraefikIntegrator')
def test_deployment_write_files(mock_traefik, mock_template, mock_config):
    """Test file writing"""
    from blastdock.core.deployment_manager import DeploymentManager
    manager = DeploymentManager()
    
    # Test compose file writing
    with patch('builtins.open', create=True):
        with patch('yaml.dump'):
            result = manager._write_compose_file({}, Path('/tmp'))
            assert result is True
    
    # Test env file writing
    with patch('builtins.open', create=True):
        result = manager._write_env_file({'KEY': 'value'}, Path('/tmp'))
        assert result is True
