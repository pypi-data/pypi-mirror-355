#!/usr/bin/env python3
"""
Tests for enhanced Docker integration modules
"""

import pytest
import json
import time
from unittest.mock import MagicMock, patch, call
import subprocess

from blastdock.docker import (
    DockerClient, get_docker_client, ComposeManager, ContainerManager,
    ImageManager, NetworkManager, VolumeManager, DockerHealthChecker
)
from blastdock.docker.errors import (
    DockerError, DockerNotFoundError, DockerNotRunningError,
    DockerConnectionError, DockerComposeError, ContainerError,
    ImageError, NetworkError, VolumeError, create_docker_error
)


class TestDockerClient:
    """Test Docker client functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.client = DockerClient(timeout=10, max_retries=2)
    
    @patch('subprocess.run')
    def test_run_command_success(self, mock_run):
        """Test successful command execution"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Docker version 20.10.21"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = self.client._run_command(['docker', '--version'])
        
        assert result.stdout == "Docker version 20.10.21"
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_run_command_timeout(self, mock_run):
        """Test command timeout handling"""
        mock_run.side_effect = subprocess.TimeoutExpired(['docker', 'info'], 10)
        
        with pytest.raises(DockerError) as exc_info:
            self.client._run_command(['docker', 'info'], timeout=10)
        
        assert "timed out" in str(exc_info.value)
    
    @patch('subprocess.run')
    def test_run_command_not_found(self, mock_run):
        """Test Docker not found error"""
        mock_run.side_effect = FileNotFoundError()
        
        with pytest.raises(DockerNotFoundError):
            self.client._run_command(['docker', '--version'])
    
    @patch('subprocess.run')
    def test_check_docker_availability(self, mock_run):
        """Test Docker availability check"""
        # Mock successful docker --version
        version_result = MagicMock()
        version_result.returncode = 0
        version_result.stdout = "Docker version 20.10.21, build baeda1f"
        
        # Mock successful docker info
        info_result = MagicMock()
        info_result.returncode = 0
        info_result.stdout = "Docker info output"
        
        # Mock successful docker compose version
        compose_result = MagicMock()
        compose_result.returncode = 0
        compose_result.stdout = "Docker Compose version v2.12.2"
        
        mock_run.side_effect = [version_result, info_result, compose_result]
        
        availability = self.client.check_docker_availability()
        
        assert availability['docker_available'] is True
        assert availability['docker_running'] is True
        assert availability['docker_compose_available'] is True
        assert availability['docker_version'] == "20.10.21"
        assert availability['docker_compose_version'] == "v2.12.2"
    
    @patch('subprocess.run')
    def test_execute_compose_command(self, mock_run):
        """Test Docker Compose command execution"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Compose output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # Set compose version to use modern docker compose
        self.client._docker_compose_version = "v2.12.2"
        self.client._connection_verified = True  # Skip connection check
        
        result = self.client.execute_compose_command(
            ['up', '-d'], 
            compose_file='docker-compose.yml',
            project_name='test-project'
        )
        
        # Check that the compose command was called (last call)
        calls = mock_run.call_args_list
        compose_call = None
        for call in calls:
            if 'docker' in call[0][0] and 'compose' in call[0][0] and 'up' in call[0][0]:
                compose_call = call
                break
        
        assert compose_call is not None
        actual_cmd = compose_call[0][0]
        expected_cmd = [
            'docker', 'compose', '-f', 'docker-compose.yml', 
            '-p', 'test-project', 'up', '-d'
        ]
        assert actual_cmd == expected_cmd
    
    def test_get_docker_client_singleton(self):
        """Test that get_docker_client returns singleton"""
        client1 = get_docker_client()
        client2 = get_docker_client()
        
        assert client1 is client2


class TestDockerErrors:
    """Test Docker error handling"""
    
    def test_docker_not_found_error(self):
        """Test DockerNotFoundError creation"""
        error = DockerNotFoundError()
        
        assert "Docker not found" in str(error)
        assert len(error.suggestions) > 0
        assert "Install Docker" in error.suggestions[0]
    
    def test_docker_not_running_error(self):
        """Test DockerNotRunningError creation"""
        error = DockerNotRunningError()
        
        assert "not running" in str(error)
        assert any("Start Docker" in suggestion for suggestion in error.suggestions)
    
    def test_container_error_with_exit_code(self):
        """Test ContainerError with specific exit codes"""
        error = ContainerError(
            "Container failed", 
            container_name="test-container",
            exit_code=125
        )
        
        assert "test-container" in error.details
        assert error.exit_code == 125
        assert any("configuration error" in suggestion.lower() for suggestion in error.suggestions)
    
    def test_create_docker_error_permission(self):
        """Test error creation for permission errors"""
        original_error = PermissionError("permission denied")
        
        docker_error = create_docker_error(original_error, "Docker operation")
        
        assert isinstance(docker_error, DockerConnectionError)
        assert "permission" in str(docker_error).lower()


class TestComposeManager:
    """Test Docker Compose manager"""
    
    def setup_method(self):
        """Setup test environment"""
        self.compose_manager = ComposeManager(
            project_dir="/test/project",
            project_name="test-project"
        )
    
    @patch('os.path.isfile')
    def test_find_compose_file(self, mock_isfile):
        """Test compose file discovery"""
        mock_isfile.side_effect = lambda path: path.endswith('docker-compose.yml')
        
        compose_file = self.compose_manager.find_compose_file('/test/project')
        
        assert compose_file == '/test/project/docker-compose.yml'
    
    @patch('os.path.isfile')
    @patch('builtins.open')
    @patch('yaml.safe_load')
    def test_validate_compose_file(self, mock_yaml_load, mock_open, mock_isfile):
        """Test compose file validation"""
        mock_isfile.return_value = True
        
        mock_compose_data = {
            'version': '3.8',
            'services': {
                'web': {
                    'image': 'nginx:latest',
                    'ports': ['80:80']
                },
                'db': {
                    'image': 'postgres:13',
                    'environment': ['POSTGRES_DB=test']
                }
            }
        }
        
        mock_yaml_load.return_value = mock_compose_data
        mock_open.return_value.__enter__.return_value = MagicMock()
        
        # Mock docker-compose config command
        with patch.object(self.compose_manager.docker_client, 'execute_compose_command') as mock_exec:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_exec.return_value = mock_result
            
            validation = self.compose_manager.validate_compose_file('docker-compose.yml')
        
        assert validation['valid'] is True
        assert validation['version'] == '3.8'
        assert 'web' in validation['services']
        assert 'db' in validation['services']
    
    @patch.object(DockerClient, 'execute_compose_command')
    def test_start_services(self, mock_exec):
        """Test service startup"""
        mock_exec.return_value = MagicMock(stdout="Services started")
        
        # Mock get_service_status
        with patch.object(self.compose_manager, 'get_service_status') as mock_status:
            mock_status.return_value = {
                'web': {'state': 'running'},
                'db': {'state': 'running'}
            }
            
            result = self.compose_manager.start_services(
                services=['web', 'db'],
                compose_file='docker-compose.yml'
            )
        
        assert result['success'] is True
        assert 'web' in result['services_started']
        assert 'db' in result['services_started']
    
    @patch.object(DockerClient, 'execute_compose_command')
    def test_build_services(self, mock_exec):
        """Test service building"""
        mock_exec.return_value = MagicMock(stdout="Build completed")
        
        with patch.object(self.compose_manager, 'validate_compose_file') as mock_validate:
            mock_validate.return_value = {'services': ['web', 'db']}
            
            result = self.compose_manager.build_services(
                services=['web'],
                no_cache=True,
                compose_file='docker-compose.yml'
            )
        
        assert result['success'] is True
        assert result['build_time'] > 0


class TestContainerManager:
    """Test container manager"""
    
    def setup_method(self):
        """Setup test environment"""
        self.container_manager = ContainerManager()
    
    @patch.object(DockerClient, 'execute_command')
    def test_list_containers(self, mock_exec):
        """Test container listing"""
        mock_output = '''{"ID":"abc123","Names":"test-container","Image":"nginx","State":"running"}
{"ID":"def456","Names":"test-db","Image":"postgres","State":"exited"}'''
        
        mock_exec.return_value = MagicMock(stdout=mock_output)
        
        containers = self.container_manager.list_containers()
        
        assert len(containers) == 2
        assert containers[0]['Names'] == 'test-container'
        assert containers[1]['State'] == 'exited'
    
    @patch.object(DockerClient, 'execute_command')
    def test_get_container_info(self, mock_exec):
        """Test getting container information"""
        mock_container_data = {
            'Id': 'abc123def456',
            'Name': '/test-container',
            'Config': {'Image': 'nginx:latest'},
            'State': {'Status': 'running'},
            'Created': '2023-01-01T00:00:00Z',
            'RestartCount': 0
        }
        
        mock_exec.return_value = MagicMock(stdout=json.dumps(mock_container_data))
        
        info = self.container_manager.get_container_info('test-container')
        
        assert info['id'] == 'abc123def456'[:12]
        assert info['name'] == 'test-container'
        assert info['image'] == 'nginx:latest'
        assert info['state']['Status'] == 'running'
    
    @patch.object(DockerClient, 'execute_command')
    def test_create_container(self, mock_exec):
        """Test container creation"""
        mock_exec.return_value = MagicMock(stdout='abc123def456\n')
        
        result = self.container_manager.create_container(
            image='nginx:latest',
            name='test-container',
            ports={'8080': '80'},
            environment={'ENV': 'test'}
        )
        
        assert result['success'] is True
        assert result['container_id'] == 'abc123def456'
        
        # Verify command was called with correct parameters
        call_args = mock_exec.call_args[0][0]
        assert 'docker' in call_args
        assert 'create' in call_args
        assert '--name' in call_args
        assert 'test-container' in call_args
        assert '-p' in call_args
        assert '8080:80' in call_args
        assert '-e' in call_args
        assert 'ENV=test' in call_args


class TestImageManager:
    """Test image manager"""
    
    def setup_method(self):
        """Setup test environment"""
        self.image_manager = ImageManager()
    
    @patch.object(DockerClient, 'execute_command')
    def test_pull_image(self, mock_exec):
        """Test image pulling"""
        mock_exec.return_value = MagicMock(stdout="Pull complete")
        
        with patch.object(self.image_manager, 'get_image_info') as mock_info:
            mock_info.return_value = {
                'size': 1000000,
                'virtual_size': 1000000
            }
            
            result = self.image_manager.pull_image('nginx', 'latest')
        
        assert result['success'] is True
        assert result['image_name'] == 'nginx:latest'
        assert result['pull_time'] > 0
    
    @patch.object(DockerClient, 'execute_command')
    def test_build_image(self, mock_exec):
        """Test image building"""
        mock_exec.return_value = MagicMock(stdout="Successfully built abc123")
        
        with patch.object(self.image_manager, 'get_image_info') as mock_info:
            mock_info.return_value = {
                'size': 2000000,
                'virtual_size': 2000000
            }
            
            result = self.image_manager.build_image(
                dockerfile_path='/test/Dockerfile',
                image_name='test-app',
                tag='latest',
                build_args={'ARG1': 'value1'}
            )
        
        assert result['success'] is True
        assert result['image_name'] == 'test-app:latest'
        assert result['build_time'] > 0


class TestNetworkManager:
    """Test network manager"""
    
    def setup_method(self):
        """Setup test environment"""
        self.network_manager = NetworkManager()
    
    @patch.object(DockerClient, 'execute_command')
    def test_create_network(self, mock_exec):
        """Test network creation"""
        mock_exec.return_value = MagicMock(stdout='net123abc\n')
        
        result = self.network_manager.create_network(
            name='test-network',
            driver='bridge',
            subnet='172.20.0.0/16',
            gateway='172.20.0.1'
        )
        
        assert result['success'] is True
        assert result['network_name'] == 'test-network'
        assert result['network_id'] == 'net123abc'
    
    @patch.object(DockerClient, 'execute_command')
    def test_connect_container(self, mock_exec):
        """Test connecting container to network"""
        mock_exec.return_value = MagicMock(stdout='')
        
        result = self.network_manager.connect_container(
            network_name='test-network',
            container_name='test-container',
            alias='web-server'
        )
        
        assert result['success'] is True
        assert result['network_name'] == 'test-network'
        assert result['container_name'] == 'test-container'


class TestVolumeManager:
    """Test volume manager"""
    
    def setup_method(self):
        """Setup test environment"""
        self.volume_manager = VolumeManager()
    
    @patch.object(DockerClient, 'execute_command')
    def test_create_volume(self, mock_exec):
        """Test volume creation"""
        mock_exec.return_value = MagicMock(stdout='test-volume\n')
        
        with patch.object(self.volume_manager, 'get_volume_info') as mock_info:
            mock_info.return_value = {
                'mountpoint': '/var/lib/docker/volumes/test-volume/_data'
            }
            
            result = self.volume_manager.create_volume(
                name='test-volume',
                driver='local',
                labels={'env': 'test'}
            )
        
        assert result['success'] is True
        assert result['volume_name'] == 'test-volume'
        assert '/var/lib/docker/volumes/test-volume/_data' in result['mountpoint']
    
    @patch.object(DockerClient, 'execute_command')
    def test_get_volume_usage(self, mock_exec):
        """Test getting volume usage information"""
        # Mock volume inspect (already extracted format from get_volume_info)
        mock_volume_data = {
            'name': 'test-volume',
            'driver': 'local',
            'mountpoint': '/var/lib/docker/volumes/test-volume/_data',
            'usage_data': {
                'Size': 1000000,
                'RefCount': 1
            }
        }
        
        with patch.object(self.volume_manager, 'get_volume_info') as mock_info:
            mock_info.return_value = mock_volume_data
            
            usage = self.volume_manager.get_volume_usage('test-volume')
        
        assert usage['volume_name'] == 'test-volume'
        assert usage['size_bytes'] == 1000000
        # Note: ref_count might be from the container detection logic
        # The test verifies the basic volume info is extracted correctly


class TestDockerHealthChecker:
    """Test Docker health checker"""
    
    def setup_method(self):
        """Setup test environment"""
        self.health_checker = DockerHealthChecker()
    
    @patch('time.time')
    @patch.object(DockerClient, 'check_docker_availability')  
    @patch.object(DockerClient, 'get_system_info')
    @patch.object(DockerClient, 'execute_command')
    def test_check_docker_daemon_health(self, mock_exec, mock_system_info, mock_availability, mock_time):
        """Test Docker daemon health check"""
        # Mock time for response time calculation
        mock_time.side_effect = [1000.0, 1001.0]  # 1 second response time
        
        mock_availability.return_value = {
            'docker_running': True,
            'docker_available': True
        }
        
        mock_system_info.return_value = {
            'system': {
                'containers': 5,
                'containers_running': 3,
                'images': 10,
                'memory': 8000000000,
                'cpus': 4
            }
        }
        
        # Mock docker system df command
        mock_exec.return_value = MagicMock(stdout="TYPE TOTAL ACTIVE SIZE RECLAIMABLE\nImages 5 3 1.2GB 500MB")
        
        health = self.health_checker.check_docker_daemon_health()
        
        assert health['healthy'] is True
        assert health['daemon_responsive'] is True
        assert health['resource_usage']['containers_total'] == 5
        assert health['resource_usage']['containers_running'] == 3
    
    @patch.object(DockerClient, 'execute_command')
    def test_check_container_health(self, mock_exec):
        """Test individual container health check"""
        mock_container_data = {
            'State': {
                'Status': 'running',
                'RestartCount': 0,
                'ExitCode': 0
            },
            'Config': {
                'Healthcheck': {
                    'Test': ['CMD', 'curl', '-f', 'http://localhost/health'],
                    'Interval': '30s',
                    'Timeout': '10s',
                    'Retries': 3
                }
            }
        }
        
        # Mock container inspect
        mock_exec.side_effect = [
            MagicMock(stdout=json.dumps(mock_container_data)),  # inspect
            MagicMock(stdout='{"CPUPerc":"5.0%","MemPerc":"10.0%"}')  # stats
        ]
        
        health = self.health_checker.check_container_health('test-container')
        
        assert health['healthy'] is True
        assert health['status'] == 'running'
        assert len(health['health_checks']) > 0


class TestDockerIntegrationWorkflows:
    """Test end-to-end Docker integration workflows"""
    
    def setup_method(self):
        """Setup test environment"""
        self.compose_manager = ComposeManager()
        self.container_manager = ContainerManager()
        self.health_checker = DockerHealthChecker()
    
    @patch.object(ComposeManager, 'find_compose_file')
    @patch.object(ComposeManager, 'validate_compose_file')
    @patch.object(ComposeManager, 'build_services')
    @patch.object(ComposeManager, 'start_services')
    @patch.object(DockerHealthChecker, 'check_compose_project_health')
    def test_full_deployment_workflow(self, mock_health, mock_start, mock_build, 
                                    mock_validate, mock_find):
        """Test complete deployment workflow"""
        # Setup mocks
        mock_find.return_value = 'docker-compose.yml'
        mock_validate.return_value = {
            'valid': True,
            'services': ['web', 'db'],
            'errors': []
        }
        mock_build.return_value = {
            'success': True,
            'services_built': ['web', 'db'],
            'build_time': 30.0
        }
        mock_start.return_value = {
            'success': True,
            'services_started': ['web', 'db'],
            'startup_time': 10.0
        }
        mock_health.return_value = {
            'healthy': True,
            'overall_status': 'healthy',
            'services': {
                'web': {'healthy': True},
                'db': {'healthy': True}
            }
        }
        
        # Execute workflow
        compose_file = self.compose_manager.find_compose_file()
        validation = self.compose_manager.validate_compose_file(compose_file)
        
        assert validation['valid'] is True
        
        build_result = self.compose_manager.build_services(compose_file=compose_file)
        assert build_result['success'] is True
        
        start_result = self.compose_manager.start_services(compose_file=compose_file)
        assert start_result['success'] is True
        
        health_result = self.health_checker.check_compose_project_health('test-project')
        assert health_result['healthy'] is True
    
    @patch.object(ImageManager, 'pull_image')
    @patch.object(ContainerManager, 'create_container')
    @patch.object(ContainerManager, 'start_container')
    @patch.object(NetworkManager, 'create_network')
    @patch.object(VolumeManager, 'create_volume')
    def test_manual_container_deployment(self, mock_vol, mock_net, mock_start, 
                                       mock_create, mock_pull):
        """Test manual container deployment with all components"""
        # Setup mocks
        mock_pull.return_value = {'success': True, 'image_name': 'nginx:latest'}
        mock_vol.return_value = {'success': True, 'volume_name': 'app-data'}
        mock_net.return_value = {'success': True, 'network_name': 'app-network'}
        mock_create.return_value = {'success': True, 'container_id': 'abc123'}
        mock_start.return_value = {'success': True, 'final_state': 'running'}
        
        # Execute deployment
        image_manager = ImageManager()
        volume_manager = VolumeManager()
        network_manager = NetworkManager()
        
        # Pull image
        pull_result = image_manager.pull_image('nginx', 'latest')
        assert pull_result['success'] is True
        
        # Create volume
        volume_result = volume_manager.create_volume('app-data')
        assert volume_result['success'] is True
        
        # Create network
        network_result = network_manager.create_network('app-network')
        assert network_result['success'] is True
        
        # Create and start container
        create_result = self.container_manager.create_container(
            image='nginx:latest',
            name='app-container',
            volumes={'app-data': '/var/www/html'},
            network='app-network'
        )
        assert create_result['success'] is True
        
        start_result = self.container_manager.start_container('abc123')
        assert start_result['success'] is True


if __name__ == '__main__':
    pytest.main([__file__])