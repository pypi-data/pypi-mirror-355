"""
Tests for deploy CLI commands
"""

import pytest
from unittest.mock import patch, Mock, MagicMock
from click.testing import CliRunner

from blastdock.cli.deploy import deploy_group, DeploymentManager


class TestDeployCommands:
    """Test deploy CLI commands"""

    def test_deploy_help(self, cli_runner):
        """Test deploy help command"""
        result = cli_runner.invoke(deploy_group, ['--help'])
        assert result.exit_code == 0
        assert 'Deployment management commands' in result.output
        assert 'create' in result.output
        assert 'list' in result.output

    @patch('blastdock.cli.deploy.DeploymentManager')
    def test_deploy_create_success(self, mock_manager_class, cli_runner):
        """Test successful deployment creation"""
        mock_manager = Mock()
        mock_manager.deploy_project.return_value = {
            'success': True,
            'project_name': 'test-project',
            'template': 'wordpress'
        }
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(deploy_group, [
            'create', 'test-project', 
            '-t', 'wordpress',
            '-c', 'domain=test.com',
            '-c', 'mysql_password=secret'
        ])
        
        assert result.exit_code == 0
        assert 'successfully' in result.output
        mock_manager.deploy_project.assert_called_once()

    @patch('blastdock.cli.deploy.DeploymentManager')
    def test_deploy_create_dry_run(self, mock_manager_class, cli_runner):
        """Test deployment creation with dry run"""
        mock_manager = Mock()
        mock_manager.deploy_project.return_value = {
            'success': True,
            'dry_run': True,
            'project_name': 'test-project'
        }
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(deploy_group, [
            'create', 'test-project',
            '-t', 'wordpress',
            '--dry-run'
        ])
        
        assert result.exit_code == 0
        mock_manager.deploy_project.assert_called_once_with(
            project_name='test-project',
            template_name='wordpress',
            config_values={},
            dry_run=True,
            auto_enhance=True,
            security_level='standard'
        )

    @patch('blastdock.cli.deploy.DeploymentManager')
    def test_deploy_create_with_security_level(self, mock_manager_class, cli_runner):
        """Test deployment creation with custom security level"""
        mock_manager = Mock()
        mock_manager.deploy_project.return_value = {'success': True}
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(deploy_group, [
            'create', 'test-project',
            '-t', 'wordpress',
            '--security', 'enhanced'
        ])
        
        assert result.exit_code == 0
        args = mock_manager.deploy_project.call_args[1]
        assert args['security_level'] == 'enhanced'

    @patch('blastdock.cli.deploy.DeploymentManager')
    def test_deploy_create_no_enhance(self, mock_manager_class, cli_runner):
        """Test deployment creation with no auto-enhance"""
        mock_manager = Mock()
        mock_manager.deploy_project.return_value = {'success': True}
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(deploy_group, [
            'create', 'test-project',
            '-t', 'wordpress',
            '--no-enhance'
        ])
        
        assert result.exit_code == 0
        args = mock_manager.deploy_project.call_args[1]
        assert args['auto_enhance'] is False

    def test_deploy_create_invalid_config(self, cli_runner):
        """Test deployment creation with invalid config format"""
        result = cli_runner.invoke(deploy_group, [
            'create', 'test-project',
            '-t', 'wordpress',
            '-c', 'invalid_format'  # Missing = sign
        ])
        
        assert result.exit_code == 0  # Command handles the error gracefully
        assert 'Invalid config format' in result.output

    @patch('blastdock.cli.deploy.DeploymentManager')
    def test_deploy_create_deployment_error(self, mock_manager_class, cli_runner):
        """Test deployment creation with deployment error"""
        from blastdock.exceptions import DeploymentError
        
        mock_manager = Mock()
        mock_manager.deploy_project.side_effect = DeploymentError("Test error")
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(deploy_group, [
            'create', 'test-project',
            '-t', 'wordpress'
        ])
        
        assert result.exit_code == 1
        assert 'Deployment error' in result.output

    @patch('blastdock.cli.deploy.DeploymentManager')
    def test_deploy_create_unexpected_error(self, mock_manager_class, cli_runner):
        """Test deployment creation with unexpected error"""
        mock_manager = Mock()
        mock_manager.deploy_project.side_effect = Exception("Unexpected error")
        mock_manager_class.return_value = mock_manager

        result = cli_runner.invoke(deploy_group, [
            'create', 'test-project',
            '-t', 'wordpress'
        ])
        
        assert result.exit_code == 1
        assert 'Unexpected error' in result.output

    @patch('blastdock.utils.docker_utils.EnhancedDockerClient')
    def test_deploy_list_success(self, mock_docker_class, cli_runner):
        """Test successful deployment listing"""
        mock_docker = Mock()
        mock_container = Mock()
        mock_container.labels = {'com.docker.compose.project': 'test-project'}
        mock_docker.client.containers.list.return_value = [mock_container]
        mock_docker_class.return_value = mock_docker

        result = cli_runner.invoke(deploy_group, ['list'])
        
        assert result.exit_code == 0
        assert 'test-project' in result.output

    @patch('blastdock.utils.docker_utils.EnhancedDockerClient')
    def test_deploy_list_json_format(self, mock_docker_class, cli_runner):
        """Test deployment listing in JSON format"""
        mock_docker = Mock()
        mock_docker.client.containers.list.return_value = []
        mock_docker_class.return_value = mock_docker

        result = cli_runner.invoke(deploy_group, ['list', '--format', 'json'])
        
        assert result.exit_code == 0
        assert '[]' in result.output

    @patch('blastdock.utils.docker_utils.EnhancedDockerClient')
    def test_deploy_list_no_projects(self, mock_docker_class, cli_runner):
        """Test deployment listing with no projects"""
        mock_docker = Mock()
        mock_docker.client.containers.list.return_value = []
        mock_docker_class.return_value = mock_docker

        result = cli_runner.invoke(deploy_group, ['list'])
        
        assert result.exit_code == 0
        assert 'No deployments found' in result.output

    @patch('blastdock.utils.docker_utils.EnhancedDockerClient')
    def test_deploy_status_success(self, mock_docker_class, cli_runner):
        """Test deployment status command"""
        mock_docker = Mock()
        mock_container = Mock()
        mock_container.labels = {
            'com.docker.compose.project': 'test-project',
            'com.docker.compose.service': 'wordpress'
        }
        mock_container.status = 'running'
        mock_container.image.tags = ['wordpress:latest']
        mock_docker.client.containers.list.return_value = [mock_container]
        mock_docker_class.return_value = mock_docker

        result = cli_runner.invoke(deploy_group, ['status', 'test-project'])
        
        assert result.exit_code == 0
        assert 'test-project' in result.output
        assert 'running' in result.output

    @patch('blastdock.cli.deploy.EnhancedDockerClient')
    def test_deploy_status_no_containers(self, mock_docker_class, cli_runner):
        """Test deployment status with no containers"""
        mock_docker = Mock()
        mock_docker.client.containers.list.return_value = []
        mock_docker_class.return_value = mock_docker

        result = cli_runner.invoke(deploy_group, ['status', 'test-project'])
        
        assert result.exit_code == 0
        assert 'No containers found' in result.output

    @patch('blastdock.cli.deploy.get_config_manager')
    @patch('blastdock.cli.deploy.subprocess.run')
    def test_deploy_remove_success(self, mock_subprocess, mock_config, cli_runner):
        """Test successful deployment removal"""
        mock_config_manager = Mock()
        mock_config_manager.config.projects_dir = '/tmp/projects'
        mock_config.return_value = mock_config_manager
        
        mock_subprocess.return_value = Mock(returncode=0, stderr='')

        # Mock the project directory exists
        with patch('pathlib.Path.exists', return_value=True):
            result = cli_runner.invoke(deploy_group, [
                'remove', 'test-project', '--force'
            ])
        
        assert result.exit_code == 0
        assert 'removed successfully' in result.output

    @patch('blastdock.cli.deploy.get_config_manager')
    @patch('blastdock.cli.deploy.subprocess.run')
    def test_deploy_logs_success(self, mock_subprocess, mock_config, cli_runner):
        """Test deployment logs command"""
        mock_config_manager = Mock()
        mock_config_manager.config.projects_dir = '/tmp/projects'
        mock_config.return_value = mock_config_manager

        # Mock the project directory exists
        with patch('pathlib.Path.exists', return_value=True):
            result = cli_runner.invoke(deploy_group, [
                'logs', 'test-project', '--tail', '10'
            ])
        
        assert result.exit_code == 0

    @patch('blastdock.cli.deploy.get_config_manager')
    @patch('blastdock.cli.deploy.subprocess.run')
    def test_deploy_update_success(self, mock_subprocess, mock_config, cli_runner):
        """Test deployment update command"""
        mock_config_manager = Mock()
        mock_config_manager.config.projects_dir = '/tmp/projects'
        mock_config.return_value = mock_config_manager
        
        mock_subprocess.return_value = Mock(returncode=0, stderr='')

        # Mock the project directory exists
        with patch('pathlib.Path.exists', return_value=True):
            result = cli_runner.invoke(deploy_group, [
                'update', 'test-project', '--pull'
            ])
        
        assert result.exit_code == 0
        assert 'updated successfully' in result.output

    @patch('blastdock.cli.deploy.get_config_manager')
    @patch('blastdock.cli.deploy.subprocess.run')
    def test_deploy_exec_success(self, mock_subprocess, mock_config, cli_runner):
        """Test deployment exec command"""
        mock_config_manager = Mock()
        mock_config_manager.config.projects_dir = '/tmp/projects'
        mock_config.return_value = mock_config_manager

        # Mock the project directory and compose file exist
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open_yaml_file()):
                result = cli_runner.invoke(deploy_group, [
                    'exec', 'test-project', 'bash', '--service', 'wordpress'
                ])
        
        assert result.exit_code == 0


class TestDeploymentManager:
    """Test DeploymentManager class"""

    @patch('blastdock.cli.deploy.get_config_manager')
    @patch('blastdock.cli.deploy.get_template_registry')
    @patch('blastdock.cli.deploy.EnhancedDockerClient')
    def test_deployment_manager_init(self, mock_docker, mock_registry, mock_config):
        """Test DeploymentManager initialization"""
        manager = DeploymentManager()
        
        assert manager is not None
        mock_config.assert_called_once()
        mock_registry.assert_called_once()
        mock_docker.assert_called_once()

    @patch('blastdock.cli.deploy.get_config_manager')
    @patch('blastdock.cli.deploy.get_template_registry')
    @patch('blastdock.cli.deploy.EnhancedDockerClient')
    def test_validate_project_name(self, mock_docker, mock_registry, mock_config):
        """Test project name validation"""
        manager = DeploymentManager()
        
        # Valid names
        assert manager._validate_project_name('valid-name') is True
        assert manager._validate_project_name('test123') is True
        assert manager._validate_project_name('a') is True
        
        # Invalid names
        assert manager._validate_project_name('Invalid_Name') is False
        assert manager._validate_project_name('UPPERCASE') is False
        assert manager._validate_project_name('with spaces') is False
        assert manager._validate_project_name('') is False

    def test_deployment_manager_methods_exist(self):
        """Test that all expected methods exist on DeploymentManager"""
        expected_methods = [
            'deploy_project',
            '_validate_project_name',
            '_create_project_directory',
            '_process_template',
            '_generate_compose_file',
            '_generate_env_file',
            '_docker_compose_up',
            '_save_project_config',
            '_show_deployment_plan',
            '_show_deployment_info'
        ]
        
        for method in expected_methods:
            assert hasattr(DeploymentManager, method), f"Method {method} not found"


def mock_open_yaml_file():
    """Mock for opening YAML files"""
    from unittest.mock import mock_open
    yaml_content = """
version: '3.8'
services:
  wordpress:
    image: wordpress:latest
"""
    return mock_open(read_data=yaml_content)