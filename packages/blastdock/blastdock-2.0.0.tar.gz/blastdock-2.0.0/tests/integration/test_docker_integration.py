"""
Integration tests for Docker functionality
"""

import pytest
import os
import json
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from blastdock.docker.client import DockerClient
from blastdock.docker.compose import ComposeManager
from blastdock.docker.containers import ContainerManager
from blastdock.docker.health import DockerHealthChecker
from blastdock.docker.errors import DockerError, DockerNotRunningError
from tests.fixtures.docker_fixtures import DockerResponseFixtures, DockerMockFactory
from tests.utils.test_helpers import TempDirectory, temp_compose_file, MockDockerClient


class TestDockerClientIntegration:
    """Integration tests for Docker client operations"""
    
    @patch('subprocess.run')
    def test_docker_version_check(self, mock_run):
        """Test checking Docker version"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=b'Docker version 20.10.0, build b35ef10',
            stderr=b''
        )
        
        client = DockerClient()
        availability = client.check_docker_availability()
        
        assert availability['docker_installed'] is True
        assert availability['docker_running'] is True
        assert '20.10.0' in availability['docker_version']
    
    @patch('subprocess.run')
    def test_docker_not_installed(self, mock_run):
        """Test behavior when Docker is not installed"""
        mock_run.side_effect = FileNotFoundError("docker command not found")
        
        client = DockerClient()
        availability = client.check_docker_availability()
        
        assert availability['docker_installed'] is False
        assert availability['docker_running'] is False
    
    @patch('subprocess.run')
    def test_container_lifecycle(self, mock_run):
        """Test complete container lifecycle"""
        responses = [
            # docker run
            MagicMock(returncode=0, stdout=b'abc123def456', stderr=b''),
            # docker ps
            MagicMock(returncode=0, stdout=b'abc123def456', stderr=b''),
            # docker stop
            MagicMock(returncode=0, stdout=b'abc123def456', stderr=b''),
            # docker rm
            MagicMock(returncode=0, stdout=b'abc123def456', stderr=b'')
        ]
        mock_run.side_effect = responses
        
        client = DockerClient()
        
        # Run container
        result = client.execute_command(['docker', 'run', '-d', 'nginx:latest'])
        assert result.success is True
        container_id = result.stdout.strip()
        
        # Check container is running
        result = client.execute_command(['docker', 'ps', '--format', '{{.ID}}'])
        assert container_id in result.stdout
        
        # Stop container
        result = client.execute_command(['docker', 'stop', container_id])
        assert result.success is True
        
        # Remove container
        result = client.execute_command(['docker', 'rm', container_id])
        assert result.success is True


class TestComposeIntegration:
    """Integration tests for Docker Compose operations"""
    
    @patch('subprocess.run')
    def test_compose_up_down_cycle(self, mock_run):
        """Test compose up and down cycle"""
        with temp_compose_file({'version': '3.8', 'services': {'web': {'image': 'nginx:latest'}}}) as compose_path:
            # Mock responses
            mock_run.side_effect = [
                # docker-compose up
                MagicMock(returncode=0, stdout=b'Creating network test_default\nCreating test_web_1', stderr=b''),
                # docker-compose ps
                MagicMock(returncode=0, stdout=b'test_web_1   nginx:latest   Up', stderr=b''),
                # docker-compose down
                MagicMock(returncode=0, stdout=b'Stopping test_web_1\nRemoving test_web_1', stderr=b'')
            ]
            
            manager = ComposeManager(project_dir=str(compose_path.parent), project_name='test')
            
            # Start services
            result = manager.up(detach=True)
            assert result['success'] is True
            
            # Check status
            result = manager.ps()
            assert result['success'] is True
            assert 'test_web_1' in result['output']
            
            # Stop services
            result = manager.down(remove_volumes=True)
            assert result['success'] is True
    
    @patch('subprocess.run')
    def test_compose_with_environment(self, mock_run):
        """Test compose with environment variables"""
        compose_content = {
            'version': '3.8',
            'services': {
                'app': {
                    'image': 'node:16',
                    'environment': {
                        'NODE_ENV': '${NODE_ENV:-development}',
                        'PORT': '${PORT:-3000}'
                    }
                }
            }
        }
        
        with temp_compose_file(compose_content) as compose_path:
            mock_run.return_value = MagicMock(returncode=0, stdout=b'', stderr=b'')
            
            manager = ComposeManager(project_dir=str(compose_path.parent))
            
            # Set environment
            env_vars = {'NODE_ENV': 'production', 'PORT': '8080'}
            result = manager.up(environment=env_vars)
            
            # Verify environment was passed
            call_env = mock_run.call_args[1]['env']
            assert call_env['NODE_ENV'] == 'production'
            assert call_env['PORT'] == '8080'


class TestContainerManagement:
    """Integration tests for container management"""
    
    @patch('blastdock.docker.containers.get_docker_client')
    def test_container_health_monitoring(self, mock_get_client):
        """Test container health monitoring"""
        mock_client = MockDockerClient()
        mock_get_client.return_value = mock_client
        
        # Set up responses
        mock_client.set_response('inspect', {
            'success': True,
            'stdout': DockerResponseFixtures.container_inspect_response(
                health_status='healthy'
            )
        })
        
        manager = ContainerManager()
        checker = DockerHealthChecker()
        
        # Check container health
        health = checker.check_container_health('abc123')
        assert health['healthy'] is True
        assert health['status'] == 'healthy'
    
    @patch('blastdock.docker.containers.get_docker_client')
    def test_container_logs_streaming(self, mock_get_client):
        """Test container log streaming"""
        mock_client = MockDockerClient()
        mock_get_client.return_value = mock_client
        
        # Set up log response
        log_output = "2023-01-01 12:00:00 Starting application\n2023-01-01 12:00:01 Ready to accept connections"
        mock_client.set_response('logs', {
            'success': True,
            'stdout': log_output
        })
        
        manager = ContainerManager()
        logs = manager.get_logs('abc123', tail=100, follow=False)
        
        assert 'Starting application' in logs
        assert 'Ready to accept connections' in logs
    
    @patch('blastdock.docker.containers.get_docker_client')
    def test_container_stats_collection(self, mock_get_client):
        """Test container statistics collection"""
        mock_client = MockDockerClient()
        mock_get_client.return_value = mock_client
        
        # Set up stats response
        mock_client.set_response('stats', {
            'success': True,
            'stdout': DockerResponseFixtures.container_stats_response()
        })
        
        manager = ContainerManager()
        stats = manager.get_stats('abc123')
        
        assert 'cpu_stats' in stats
        assert 'memory_stats' in stats
        assert stats['memory_stats']['usage'] == 512000000  # 512MB


class TestDockerNetworking:
    """Integration tests for Docker networking"""
    
    @patch('subprocess.run')
    def test_network_creation_and_usage(self, mock_run):
        """Test creating and using custom networks"""
        mock_run.side_effect = [
            # Create network
            MagicMock(returncode=0, stdout=b'network123', stderr=b''),
            # Run container on network
            MagicMock(returncode=0, stdout=b'container123', stderr=b''),
            # Inspect network
            MagicMock(returncode=0, stdout=json.dumps({
                'Name': 'test-network',
                'Driver': 'bridge',
                'Containers': {'container123': {}}
            }).encode(), stderr=b''),
            # Remove container
            MagicMock(returncode=0, stdout=b'', stderr=b''),
            # Remove network
            MagicMock(returncode=0, stdout=b'', stderr=b'')
        ]
        
        client = DockerClient()
        
        # Create network
        result = client.execute_command(['docker', 'network', 'create', 'test-network'])
        assert result.success is True
        
        # Run container on network
        result = client.execute_command([
            'docker', 'run', '-d', '--network', 'test-network', 'nginx:latest'
        ])
        assert result.success is True
        
        # Verify network has container
        result = client.execute_command(['docker', 'network', 'inspect', 'test-network'])
        network_info = json.loads(result.stdout)
        assert 'container123' in network_info['Containers']


class TestDockerVolumes:
    """Integration tests for Docker volumes"""
    
    @patch('subprocess.run')
    def test_volume_lifecycle(self, mock_run):
        """Test volume creation, usage, and removal"""
        mock_run.side_effect = [
            # Create volume
            MagicMock(returncode=0, stdout=b'test-volume', stderr=b''),
            # Run container with volume
            MagicMock(returncode=0, stdout=b'container123', stderr=b''),
            # Write to volume
            MagicMock(returncode=0, stdout=b'', stderr=b''),
            # Stop container
            MagicMock(returncode=0, stdout=b'', stderr=b''),
            # Remove container
            MagicMock(returncode=0, stdout=b'', stderr=b''),
            # Remove volume
            MagicMock(returncode=0, stdout=b'', stderr=b'')
        ]
        
        client = DockerClient()
        
        # Create volume
        result = client.execute_command(['docker', 'volume', 'create', 'test-volume'])
        assert result.success is True
        
        # Use volume in container
        result = client.execute_command([
            'docker', 'run', '-d', '-v', 'test-volume:/data', 'nginx:latest'
        ])
        assert result.success is True
        container_id = result.stdout.strip()
        
        # Write data to volume
        result = client.execute_command([
            'docker', 'exec', container_id, 'sh', '-c', 'echo "test data" > /data/test.txt'
        ])
        assert result.success is True


class TestDockerErrorHandling:
    """Integration tests for error handling"""
    
    @patch('subprocess.run')
    def test_permission_denied_handling(self, mock_run):
        """Test handling permission denied errors"""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout=b'',
            stderr=b'permission denied while trying to connect to the Docker daemon socket'
        )
        
        client = DockerClient()
        result = client.execute_command(['docker', 'ps'])
        
        assert result.success is False
        assert 'permission denied' in result.stderr.lower()
    
    @patch('subprocess.run')
    def test_docker_daemon_not_running(self, mock_run):
        """Test handling Docker daemon not running"""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout=b'',
            stderr=b'Cannot connect to the Docker daemon at unix:///var/run/docker.sock'
        )
        
        client = DockerClient()
        with pytest.raises(DockerNotRunningError):
            client.verify_docker_connection()
    
    @patch('subprocess.run')
    def test_image_not_found_handling(self, mock_run):
        """Test handling image not found errors"""
        mock_run.return_value = MagicMock(
            returncode=125,
            stdout=b'',
            stderr=b"Unable to find image 'nonexistent:latest' locally"
        )
        
        client = DockerClient()
        result = client.execute_command(['docker', 'run', 'nonexistent:latest'])
        
        assert result.success is False
        assert 'Unable to find image' in result.stderr


class TestDockerResourceCleanup:
    """Integration tests for resource cleanup"""
    
    @patch('subprocess.run')
    def test_cleanup_unused_resources(self, mock_run):
        """Test cleaning up unused Docker resources"""
        mock_run.side_effect = [
            # List dangling images
            MagicMock(returncode=0, stdout=b'image1\nimage2', stderr=b''),
            # Remove dangling images
            MagicMock(returncode=0, stdout=b'Deleted: image1\nDeleted: image2', stderr=b''),
            # Prune volumes
            MagicMock(returncode=0, stdout=b'Total reclaimed space: 1.2GB', stderr=b''),
            # Prune networks
            MagicMock(returncode=0, stdout=b'Deleted Networks:\ntest-net1\ntest-net2', stderr=b'')
        ]
        
        client = DockerClient()
        
        # Clean dangling images
        result = client.execute_command(['docker', 'images', '-f', 'dangling=true', '-q'])
        assert result.success is True
        
        # Remove them
        if result.stdout.strip():
            result = client.execute_command(['docker', 'rmi', '-f'] + result.stdout.strip().split('\n'))
            assert result.success is True
        
        # Prune volumes
        result = client.execute_command(['docker', 'volume', 'prune', '-f'])
        assert result.success is True
        assert 'reclaimed space' in result.stdout
        
        # Prune networks
        result = client.execute_command(['docker', 'network', 'prune', '-f'])
        assert result.success is True