"""Comprehensive tests for Docker Compose module matching actual implementation."""

import json
import os
import time
import yaml
import subprocess
from unittest.mock import Mock, patch, MagicMock, mock_open, call
import pytest

from blastdock.docker.compose import ComposeManager
from blastdock.docker.errors import DockerComposeError


class TestComposeManager:
    """Test suite for ComposeManager."""

    @pytest.fixture
    def manager(self):
        """Create a ComposeManager instance."""
        with patch('blastdock.docker.compose.get_docker_client') as mock_client:
            mock_client.return_value = Mock()
            manager = ComposeManager(project_dir="/test/dir", project_name="test-project")
            return manager

    def test_init(self):
        """Test ComposeManager initialization."""
        with patch('blastdock.docker.compose.get_docker_client') as mock_client:
            mock_docker = Mock()
            mock_client.return_value = mock_docker
            
            manager = ComposeManager(project_dir="/test/dir", project_name="test-project")
            
            assert manager.project_dir == "/test/dir"
            assert manager.project_name == "test-project"
            assert manager.docker_client == mock_docker
            assert manager.compose_files == [
                'docker-compose.yml',
                'docker-compose.yaml',
                'compose.yml',
                'compose.yaml'
            ]

    def test_init_defaults(self):
        """Test ComposeManager initialization with defaults."""
        with patch('blastdock.docker.compose.get_docker_client'):
            manager = ComposeManager()
            
            assert manager.project_dir is None
            assert manager.project_name is None
            assert manager.docker_client is not None

    @patch('os.path.isfile')
    def test_find_compose_file_found(self, mock_isfile, manager):
        """Test finding compose file when it exists."""
        mock_isfile.side_effect = lambda path: path.endswith('docker-compose.yml')
        
        result = manager.find_compose_file()
        
        assert result == "/test/dir/docker-compose.yml"
        mock_isfile.assert_called()

    @patch('os.path.isfile')
    def test_find_compose_file_not_found(self, mock_isfile, manager):
        """Test finding compose file when none exist."""
        mock_isfile.return_value = False
        
        result = manager.find_compose_file()
        
        assert result is None

    @patch('os.path.isfile')
    @patch('os.getcwd')
    def test_find_compose_file_uses_cwd(self, mock_getcwd, mock_isfile):
        """Test finding compose file uses current directory when no project_dir."""
        mock_getcwd.return_value = "/current/dir"
        mock_isfile.side_effect = lambda path: path == "/current/dir/compose.yml"
        
        with patch('blastdock.docker.compose.get_docker_client'):
            manager = ComposeManager()  # No project_dir
            result = manager.find_compose_file()
        
        assert result == "/current/dir/compose.yml"

    @patch('os.path.isfile')
    def test_find_compose_file_custom_directory(self, mock_isfile, manager):
        """Test finding compose file in custom directory."""
        mock_isfile.side_effect = lambda path: path == "/custom/dir/docker-compose.yaml"
        
        result = manager.find_compose_file("/custom/dir")
        
        assert result == "/custom/dir/docker-compose.yaml"

    def test_validate_compose_file_not_found(self, manager):
        """Test validating non-existent compose file."""
        with patch('os.path.isfile', return_value=False):
            result = manager.validate_compose_file("/test/compose.yml")
        
        assert result['valid'] is False
        assert 'Compose file not found' in result['errors'][0]

    def test_validate_compose_file_invalid_yaml(self, manager):
        """Test validating invalid YAML file."""
        with patch('os.path.isfile', return_value=True):
            with patch('builtins.open', mock_open(read_data="invalid: yaml: content")):
                with patch('yaml.safe_load', side_effect=yaml.YAMLError("Invalid YAML")):
                    result = manager.validate_compose_file("/test/compose.yml")
        
        assert result['valid'] is False
        assert 'Validation error' in result['errors'][0]

    def test_validate_compose_file_not_dict(self, manager):
        """Test validating compose file that's not a dictionary."""
        with patch('os.path.isfile', return_value=True):
            with patch('builtins.open', mock_open(read_data="[]")):
                result = manager.validate_compose_file("/test/compose.yml")
        
        assert result['valid'] is False
        assert 'Invalid compose file format' in result['errors'][0]

    def test_validate_compose_file_no_services(self, manager):
        """Test validating compose file without services."""
        compose_data = {"version": "3.8"}
        
        with patch('os.path.isfile', return_value=True):
            with patch('builtins.open', mock_open(read_data=yaml.dump(compose_data))):
                result = manager.validate_compose_file("/test/compose.yml")
        
        assert result['valid'] is False
        assert 'No services defined' in result['errors'][0]

    def test_validate_compose_file_success(self, manager):
        """Test successful compose file validation."""
        compose_data = {
            "version": "3.8",
            "services": {
                "web": {
                    "image": "nginx:latest",
                    "ports": ["80:80"]
                },
                "db": {
                    "image": "postgres:13"
                }
            },
            "networks": {
                "frontend": {},
                "backend": {}
            },
            "volumes": {
                "data": {}
            }
        }
        
        with patch('os.path.isfile', return_value=True):
            with patch('builtins.open', mock_open(read_data=yaml.dump(compose_data))):
                result = manager.validate_compose_file("/test/compose.yml")
        
        assert result['valid'] is True
        assert result['version'] == "3.8"
        assert set(result['services']) == {"web", "db"}
        assert set(result['networks']) == {"frontend", "backend"}
        assert result['volumes'] == ["data"]
        assert result['errors'] == []

    def test_validate_compose_file_old_version(self, manager):
        """Test validating compose file with old version."""
        compose_data = {
            "version": "2.1",
            "services": {"web": {"image": "nginx"}}
        }
        
        with patch('os.path.isfile', return_value=True):
            with patch('builtins.open', mock_open(read_data=yaml.dump(compose_data))):
                result = manager.validate_compose_file("/test/compose.yml")
        
        assert result['valid'] is True
        assert result['version'] == "2.1"
        assert 'outdated' in result['warnings'][0]
        assert 'upgrading to version 3.8' in result['recommendations'][0]

    def test_validate_compose_file_no_version(self, manager):
        """Test validating compose file without version."""
        compose_data = {
            "services": {"web": {"image": "nginx"}}
        }
        
        with patch('os.path.isfile', return_value=True):
            with patch('builtins.open', mock_open(read_data=yaml.dump(compose_data))):
                result = manager.validate_compose_file("/test/compose.yml")
        
        assert result['valid'] is True
        assert 'No version specified' in result['warnings'][0]

    @patch.object(ComposeManager, 'find_compose_file')
    def test_build_services_no_compose_file(self, mock_find, manager):
        """Test building services without compose file."""
        mock_find.return_value = None
        
        with pytest.raises(DockerComposeError) as exc_info:
            manager.build_services()
        
        assert "No compose file found" in str(exc_info.value)

    @patch.object(ComposeManager, 'find_compose_file')
    def test_build_services_success(self, mock_find, manager):
        """Test successful service build."""
        mock_find.return_value = "/test/compose.yml"
        
        mock_result = Mock(stdout="Successfully built web", stderr="")
        manager.docker_client.execute_compose_command.return_value = mock_result
        
        with patch.object(manager, 'validate_compose_file') as mock_validate:
            mock_validate.return_value = {'services': ['web', 'db']}
            
            result = manager.build_services()
        
        assert result['success'] is True
        assert result['output'] == "Successfully built web"
        assert result['services_built'] == ['web', 'db']
        assert result['build_time'] > 0
        
        # Check command
        call_args = manager.docker_client.execute_compose_command.call_args
        assert call_args[0][0] == ['build']
        assert call_args[1]['compose_file'] == "/test/compose.yml"

    @patch.object(ComposeManager, 'find_compose_file')
    def test_build_services_with_options(self, mock_find, manager):
        """Test building services with options."""
        mock_find.return_value = "/test/compose.yml"
        manager.docker_client.execute_compose_command.return_value = Mock(stdout="Built")
        
        with patch.object(manager, 'validate_compose_file') as mock_validate:
            mock_validate.return_value = {'services': ['web']}
            
            result = manager.build_services(
                services=['web'], 
                no_cache=True, 
                parallel=True
            )
        
        # Check command includes options
        call_args = manager.docker_client.execute_compose_command.call_args
        cmd = call_args[0][0]
        assert '--no-cache' in cmd
        assert '--parallel' in cmd
        assert 'web' in cmd

    @patch.object(ComposeManager, 'find_compose_file')
    def test_build_services_failure(self, mock_find, manager):
        """Test service build failure."""
        mock_find.return_value = "/test/compose.yml"
        
        manager.docker_client.execute_compose_command.side_effect = Exception("Build failed")
        
        with pytest.raises(DockerComposeError) as exc_info:
            manager.build_services()
        
        assert "Failed to build services" in str(exc_info.value)

    @patch.object(ComposeManager, 'find_compose_file')
    def test_start_services_success(self, mock_find, manager):
        """Test successful service start."""
        mock_find.return_value = "/test/compose.yml"
        
        mock_result = Mock(stdout="Starting web_1... done", stderr="")
        manager.docker_client.execute_compose_command.return_value = mock_result
        
        with patch.object(manager, 'get_service_status') as mock_status:
            mock_status.return_value = {
                'web': {'status': 'running', 'health': 'healthy'}
            }
            
            result = manager.start_services()
        
        assert result['success'] is True
        assert result['output'] == "Starting web_1... done"
        assert result['container_info'] == {
            'web': {'status': 'running', 'health': 'healthy'}
        }
        
        # Check command
        call_args = manager.docker_client.execute_compose_command.call_args
        cmd = call_args[0][0]
        assert cmd[0] == 'up'
        assert '-d' in cmd
        assert '--remove-orphans' in cmd

    @patch.object(ComposeManager, 'find_compose_file')
    def test_start_services_with_options(self, mock_find, manager):
        """Test starting services with options."""
        mock_find.return_value = "/test/compose.yml"
        manager.docker_client.execute_compose_command.return_value = Mock(stdout="Started")
        
        with patch.object(manager, 'get_service_status') as mock_status:
            mock_status.return_value = {}
            
            result = manager.start_services(
                services=['web', 'db'],
                detached=False,
                remove_orphans=False
            )
        
        # Check command doesn't include -d or --remove-orphans
        call_args = manager.docker_client.execute_compose_command.call_args
        cmd = call_args[0][0]
        assert '-d' not in cmd
        assert '--remove-orphans' not in cmd
        assert 'web' in cmd
        assert 'db' in cmd

    @patch.object(ComposeManager, 'find_compose_file')
    def test_stop_services_success(self, mock_find, manager):
        """Test successful service stop."""
        mock_find.return_value = "/test/compose.yml"
        
        mock_result = Mock(stdout="Stopping web_1... done", stderr="")
        manager.docker_client.execute_compose_command.return_value = mock_result
        
        result = manager.stop_services(timeout=30)
        
        assert result['success'] is True
        assert result['output'] == "Stopping web_1... done"
        
        # Check command
        call_args = manager.docker_client.execute_compose_command.call_args
        cmd = call_args[0][0]
        assert cmd == ['stop', '-t', '30']

    @patch.object(ComposeManager, 'find_compose_file')
    def test_remove_services_success(self, mock_find, manager):
        """Test successful service removal."""
        mock_find.return_value = "/test/compose.yml"
        
        mock_result = Mock(stdout="Removing web_1... done", stderr="")
        manager.docker_client.execute_compose_command.return_value = mock_result
        
        result = manager.remove_services(volumes=True, force=True)
        
        assert result['success'] is True
        
        # Check command
        call_args = manager.docker_client.execute_compose_command.call_args
        cmd = call_args[0][0]
        assert 'down' in cmd
        assert '-v' in cmd
        assert '--remove-orphans' in cmd

    @patch.object(ComposeManager, 'find_compose_file')
    def test_get_service_status_success(self, mock_find, manager):
        """Test getting service status."""
        mock_find.return_value = "/test/compose.yml"
        
        mock_result = Mock(
            stdout="web_1  Up  5 minutes  80/tcp->0.0.0.0:8080  healthy",
            stderr=""
        )
        manager.docker_client.execute_compose_command.return_value = mock_result
        
        result = manager.get_service_status()
        
        assert 'web' in result
        assert result['web']['status'] == 'running'
        assert result['web']['uptime'] == '5 minutes'
        assert result['web']['health'] == 'healthy'

    @patch.object(ComposeManager, 'find_compose_file')
    def test_get_service_status_down(self, mock_find, manager):
        """Test getting status of down services."""
        mock_find.return_value = "/test/compose.yml"
        
        mock_result = Mock(
            stdout="web_1  Exit 0",
            stderr=""
        )
        manager.docker_client.execute_compose_command.return_value = mock_result
        
        result = manager.get_service_status()
        
        assert 'web' in result
        assert result['web']['status'] == 'exited'
        assert result['web']['exit_code'] == '0'

    @patch.object(ComposeManager, 'find_compose_file')
    def test_get_service_logs_success(self, mock_find, manager):
        """Test getting service logs."""
        mock_find.return_value = "/test/compose.yml"
        
        mock_result = Mock(
            stdout="web_1  | Starting nginx\nweb_1  | Ready",
            stderr=""
        )
        manager.docker_client.execute_compose_command.return_value = mock_result
        
        result = manager.get_service_logs(service='web', tail=100, follow=False)
        
        assert result['success'] is True
        assert 'Starting nginx' in result['logs']
        
        # Check command
        call_args = manager.docker_client.execute_compose_command.call_args
        cmd = call_args[0][0]
        assert 'logs' in cmd
        assert '--tail' in cmd
        assert '100' in cmd
        assert 'web' in cmd

    @patch.object(ComposeManager, 'find_compose_file')
    def test_get_service_logs_all_services(self, mock_find, manager):
        """Test getting logs from all services."""
        mock_find.return_value = "/test/compose.yml"
        
        mock_result = Mock(
            stdout="web_1  | nginx log\ndb_1   | postgres log",
            stderr=""
        )
        manager.docker_client.execute_compose_command.return_value = mock_result
        
        result = manager.get_service_logs()  # No specific service
        
        assert result['success'] is True
        assert 'nginx log' in result['logs']
        assert 'postgres log' in result['logs']

    @patch.object(ComposeManager, 'find_compose_file')
    def test_scale_service_success(self, mock_find, manager):
        """Test scaling a service."""
        mock_find.return_value = "/test/compose.yml"
        
        mock_result = Mock(stdout="Scaling web to 3", stderr="")
        manager.docker_client.execute_compose_command.return_value = mock_result
        
        result = manager.scale_service('web', 3)
        
        assert result['success'] is True
        assert result['service'] == 'web'
        assert result['replicas'] == 3
        
        # Check command
        call_args = manager.docker_client.execute_compose_command.call_args
        cmd = call_args[0][0]
        assert 'up' in cmd
        assert '--scale' in cmd
        assert 'web=3' in cmd

    @patch.object(ComposeManager, 'find_compose_file')
    def test_scale_service_failure(self, mock_find, manager):
        """Test scaling service failure."""
        mock_find.return_value = "/test/compose.yml"
        
        manager.docker_client.execute_compose_command.side_effect = Exception("Scale failed")
        
        with pytest.raises(DockerComposeError) as exc_info:
            manager.scale_service('web', 3)
        
        assert "Failed to scale service web" in str(exc_info.value)

    def test_compose_file_validation_service_warnings(self, manager):
        """Test various service configuration warnings."""
        compose_data = {
            "version": "3.8",
            "services": {
                "web": {
                    "image": "nginx",
                    "ports": ["80:invalid"],  # Invalid port
                    "depends_on": ["unknown_service"]  # Unknown dependency
                },
                "missing_image": {
                    "environment": {"VAR": "value"}  # No image or build
                }
            }
        }
        
        with patch('os.path.isfile', return_value=True):
            with patch('builtins.open', mock_open(read_data=yaml.dump(compose_data))):
                result = manager.validate_compose_file("/test/compose.yml")
        
        assert result['valid'] is True  # Still valid, just warnings
        assert len(result['warnings']) >= 3
        
        # Check specific warnings
        warnings_text = ' '.join(result['warnings'])
        assert 'Invalid port mapping' in warnings_text
        assert 'depends on unknown service' in warnings_text
        assert 'missing image or build' in warnings_text

    def test_error_handling_in_validation(self, manager):
        """Test error handling during validation."""
        with patch('os.path.isfile', return_value=True):
            with patch('builtins.open', side_effect=IOError("Cannot read file")):
                result = manager.validate_compose_file("/test/compose.yml")
        
        assert result['valid'] is False
        assert 'Validation error' in result['errors'][0]
        assert 'Cannot read file' in result['errors'][0]

    @patch.object(ComposeManager, 'find_compose_file')  
    def test_build_services_with_specified_services(self, mock_find, manager):
        """Test building specific services."""
        mock_find.return_value = "/test/compose.yml"
        manager.docker_client.execute_compose_command.return_value = Mock(stdout="Built")
        
        result = manager.build_services(services=['web'])
        
        assert result['services_built'] == ['web']
        
        # Check that specific services were passed to command
        call_args = manager.docker_client.execute_compose_command.call_args
        cmd = call_args[0][0]
        assert 'web' in cmd

    @patch.object(ComposeManager, 'find_compose_file')
    def test_stop_services_with_specific_services(self, mock_find, manager):
        """Test stopping specific services.""" 
        mock_find.return_value = "/test/compose.yml"
        manager.docker_client.execute_compose_command.return_value = Mock(stdout="Stopped")
        
        result = manager.stop_services(services=['web', 'db'])
        
        # Check command includes specific services
        call_args = manager.docker_client.execute_compose_command.call_args
        cmd = call_args[0][0]
        assert 'web' in cmd
        assert 'db' in cmd

    @patch.object(ComposeManager, 'find_compose_file')
    def test_command_failure_handling(self, mock_find, manager):
        """Test handling of Docker Compose command failures."""
        mock_find.return_value = "/test/compose.yml"
        
        error = subprocess.CalledProcessError(1, "docker compose up")
        error.stderr = "ERROR: Service 'web' failed to start"
        manager.docker_client.execute_compose_command.side_effect = error
        
        with pytest.raises(DockerComposeError):
            manager.start_services()

    def test_compose_file_path_handling(self, manager):
        """Test compose file path handling in commands."""
        compose_file = "/custom/path/docker-compose.yml"
        
        with patch.object(manager, 'find_compose_file') as mock_find:
            mock_find.return_value = None  # Force using provided path
            manager.docker_client.execute_compose_command.return_value = Mock(stdout="OK")
            
            with patch.object(manager, 'validate_compose_file') as mock_validate:
                mock_validate.return_value = {'services': ['web']}
                
                manager.build_services(compose_file=compose_file)
            
            # Verify the compose file was passed correctly
            call_args = manager.docker_client.execute_compose_command.call_args
            assert call_args[1]['compose_file'] == compose_file
            assert call_args[1]['cwd'] == "/custom/path"

    def test_timing_measurement_in_operations(self, manager):
        """Test that timing is measured in operations."""
        with patch.object(manager, 'find_compose_file') as mock_find:
            mock_find.return_value = "/test/compose.yml"
            
            # Mock a slow operation
            def slow_execute(*args, **kwargs):
                time.sleep(0.1)  # 100ms delay
                return Mock(stdout="Done")
            
            manager.docker_client.execute_compose_command.side_effect = slow_execute
            
            with patch.object(manager, 'validate_compose_file') as mock_validate:
                mock_validate.return_value = {'services': ['web']}
                
                result = manager.build_services()
            
            assert result['build_time'] >= 0.1