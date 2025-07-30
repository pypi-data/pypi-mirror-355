"""
Tests for Docker utilities
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import docker.errors

from blastdock.utils.docker_utils import (
    EnhancedDockerClient, DockerError, DockerNotFoundError, DockerNotRunningError
)


class TestEnhancedDockerClient:
    """Test EnhancedDockerClient class"""

    @patch('blastdock.utils.docker_utils.docker.from_env')
    def test_client_property_success(self, mock_docker):
        """Test successful Docker client creation"""
        mock_client = Mock()
        mock_docker.return_value = mock_client
        
        docker_client = EnhancedDockerClient()
        client = docker_client.client
        
        assert client == mock_client
        mock_docker.assert_called_once()

    @patch('blastdock.utils.docker_utils.docker.from_env')
    def test_client_property_docker_exception(self, mock_docker):
        """Test Docker client creation with Docker exception"""
        mock_docker.side_effect = docker.errors.DockerException("Docker not available")
        
        docker_client = EnhancedDockerClient()
        
        with pytest.raises(DockerNotRunningError):
            _ = docker_client.client

    @patch('blastdock.utils.docker_utils.docker.from_env')
    def test_is_running_success(self, mock_docker):
        """Test Docker daemon running check - success"""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_docker.return_value = mock_client
        
        docker_client = EnhancedDockerClient()
        assert docker_client.is_running() is True

    @patch('blastdock.utils.docker_utils.docker.from_env')
    def test_is_running_failure(self, mock_docker):
        """Test Docker daemon running check - failure"""
        mock_client = Mock()
        mock_client.ping.side_effect = Exception("Connection failed")
        mock_docker.return_value = mock_client
        
        docker_client = EnhancedDockerClient()
        assert docker_client.is_running() is False

    @patch('blastdock.utils.docker_utils.docker.from_env')
    def test_is_docker_running_alias(self, mock_docker):
        """Test is_docker_running is alias for is_running"""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_docker.return_value = mock_client
        
        docker_client = EnhancedDockerClient()
        assert docker_client.is_docker_running() is True

    @patch('blastdock.utils.docker_utils.docker.from_env')
    def test_get_container_by_name_success(self, mock_docker):
        """Test get container by name - success"""
        mock_container = Mock()
        mock_client = Mock()
        mock_client.containers.get.return_value = mock_container
        mock_docker.return_value = mock_client
        
        docker_client = EnhancedDockerClient()
        result = docker_client.get_container_by_name('test-container')
        
        assert result == mock_container
        mock_client.containers.get.assert_called_once_with('test-container')

    @patch('blastdock.utils.docker_utils.docker.from_env')
    def test_get_container_by_name_not_found(self, mock_docker):
        """Test get container by name - not found"""
        mock_client = Mock()
        mock_client.containers.get.side_effect = docker.errors.NotFound("Container not found")
        mock_docker.return_value = mock_client
        
        docker_client = EnhancedDockerClient()
        result = docker_client.get_container_by_name('nonexistent')
        
        assert result is None

    @patch('blastdock.utils.docker_utils.docker.from_env')
    def test_get_container_by_name_error(self, mock_docker):
        """Test get container by name - general error"""
        mock_client = Mock()
        mock_client.containers.get.side_effect = Exception("General error")
        mock_docker.return_value = mock_client
        
        docker_client = EnhancedDockerClient()
        result = docker_client.get_container_by_name('test-container')
        
        assert result is None

    @patch('blastdock.utils.docker_utils.docker.from_env')
    def test_list_containers_success(self, mock_docker):
        """Test list containers - success"""
        mock_containers = [Mock(), Mock()]
        mock_client = Mock()
        mock_client.containers.list.return_value = mock_containers
        mock_docker.return_value = mock_client
        
        docker_client = EnhancedDockerClient()
        result = docker_client.list_containers(all=True)
        
        assert result == mock_containers
        mock_client.containers.list.assert_called_once_with(all=True)

    @patch('blastdock.utils.docker_utils.docker.from_env')
    def test_list_containers_error(self, mock_docker):
        """Test list containers - error"""
        mock_client = Mock()
        mock_client.containers.list.side_effect = Exception("List error")
        mock_docker.return_value = mock_client
        
        docker_client = EnhancedDockerClient()
        result = docker_client.list_containers()
        
        assert result == []

    @patch('blastdock.utils.docker_utils.docker.from_env')
    def test_get_container_stats_success(self, mock_docker):
        """Test get container stats - success"""
        mock_stats = {'cpu_usage': 50.0}
        mock_container = Mock()
        mock_container.stats.return_value = mock_stats
        mock_client = Mock()
        mock_client.containers.get.return_value = mock_container
        mock_docker.return_value = mock_client
        
        docker_client = EnhancedDockerClient()
        result = docker_client.get_container_stats('test-container')
        
        assert result == mock_stats
        mock_container.stats.assert_called_once_with(stream=False)

    @patch('blastdock.utils.docker_utils.docker.from_env')
    def test_get_container_stats_no_container(self, mock_docker):
        """Test get container stats - container not found"""
        mock_client = Mock()
        mock_client.containers.get.side_effect = docker.errors.NotFound("Not found")
        mock_docker.return_value = mock_client
        
        docker_client = EnhancedDockerClient()
        result = docker_client.get_container_stats('nonexistent')
        
        assert result == {}

    @patch('blastdock.utils.docker_utils.docker.from_env')
    def test_get_container_logs_success(self, mock_docker):
        """Test get container logs - success"""
        mock_logs = b'Log line 1\nLog line 2'
        mock_container = Mock()
        mock_container.logs.return_value = mock_logs
        mock_client = Mock()
        mock_client.containers.get.return_value = mock_container
        mock_docker.return_value = mock_client
        
        docker_client = EnhancedDockerClient()
        result = docker_client.get_container_logs('test-container', tail=50)
        
        assert result == 'Log line 1\nLog line 2'
        mock_container.logs.assert_called_once_with(tail=50)

    @patch('blastdock.utils.docker_utils.docker.from_env')
    def test_execute_command_success(self, mock_docker):
        """Test execute command - success"""
        mock_result = Mock()
        mock_result.output = b'Command output'
        mock_container = Mock()
        mock_container.exec_run.return_value = mock_result
        mock_client = Mock()
        mock_client.containers.get.return_value = mock_container
        mock_docker.return_value = mock_client
        
        docker_client = EnhancedDockerClient()
        result = docker_client.execute_command('test-container', ['ls', '-la'])
        
        assert result == 'Command output'
        mock_container.exec_run.assert_called_once_with(['ls', '-la'])

    @patch('blastdock.utils.docker_utils.docker.from_env')
    def test_stop_container_success(self, mock_docker):
        """Test stop container - success"""
        mock_container = Mock()
        mock_client = Mock()
        mock_client.containers.get.return_value = mock_container
        mock_docker.return_value = mock_client
        
        docker_client = EnhancedDockerClient()
        result = docker_client.stop_container('test-container')
        
        assert result is True
        mock_container.stop.assert_called_once()

    @patch('blastdock.utils.docker_utils.docker.from_env')
    def test_remove_container_success(self, mock_docker):
        """Test remove container - success"""
        mock_container = Mock()
        mock_client = Mock()
        mock_client.containers.get.return_value = mock_container
        mock_docker.return_value = mock_client
        
        docker_client = EnhancedDockerClient()
        result = docker_client.remove_container('test-container', force=True)
        
        assert result is True
        mock_container.remove.assert_called_once_with(force=True)

    @patch('blastdock.utils.docker_utils.docker.from_env')
    def test_create_network_success(self, mock_docker):
        """Test create network - success"""
        mock_client = Mock()
        mock_docker.return_value = mock_client
        
        docker_client = EnhancedDockerClient()
        result = docker_client.create_network('test-network', driver='bridge')
        
        assert result is True
        mock_client.networks.create.assert_called_once_with('test-network', driver='bridge')

    @patch('blastdock.utils.docker_utils.docker.from_env')
    def test_create_network_error(self, mock_docker):
        """Test create network - error"""
        mock_client = Mock()
        mock_client.networks.create.side_effect = Exception("Network error")
        mock_docker.return_value = mock_client
        
        docker_client = EnhancedDockerClient()
        result = docker_client.create_network('test-network')
        
        assert result is False

    @patch('blastdock.utils.docker_utils.docker.from_env')
    def test_get_network_success(self, mock_docker):
        """Test get network - success"""
        mock_network = Mock()
        mock_client = Mock()
        mock_client.networks.get.return_value = mock_network
        mock_docker.return_value = mock_client
        
        docker_client = EnhancedDockerClient()
        result = docker_client.get_network('test-network')
        
        assert result == mock_network

    @patch('blastdock.utils.docker_utils.docker.from_env')
    def test_get_network_not_found(self, mock_docker):
        """Test get network - not found"""
        mock_client = Mock()
        mock_client.networks.get.side_effect = docker.errors.NotFound("Network not found")
        mock_docker.return_value = mock_client
        
        docker_client = EnhancedDockerClient()
        result = docker_client.get_network('nonexistent')
        
        assert result is None

    @patch('blastdock.utils.docker_utils.docker.from_env')
    def test_list_images_success(self, mock_docker):
        """Test list images - success"""
        mock_images = [Mock(), Mock()]
        mock_client = Mock()
        mock_client.images.list.return_value = mock_images
        mock_docker.return_value = mock_client
        
        docker_client = EnhancedDockerClient()
        result = docker_client.list_images()
        
        assert result == mock_images

    @patch('blastdock.utils.docker_utils.docker.from_env')
    def test_pull_image_success(self, mock_docker):
        """Test pull image - success"""
        mock_client = Mock()
        mock_docker.return_value = mock_client
        
        docker_client = EnhancedDockerClient()
        result = docker_client.pull_image('nginx:latest')
        
        assert result is True
        mock_client.images.pull.assert_called_once_with('nginx:latest')

    @patch('blastdock.utils.docker_utils.docker.from_env')
    def test_get_docker_info_success(self, mock_docker):
        """Test get Docker info - success"""
        mock_info = {'Version': '20.10.0'}
        mock_client = Mock()
        mock_client.info.return_value = mock_info
        mock_docker.return_value = mock_client
        
        docker_client = EnhancedDockerClient()
        result = docker_client.get_docker_info()
        
        assert result == mock_info

    @patch('blastdock.utils.docker_utils.docker.from_env')
    def test_get_docker_version_success(self, mock_docker):
        """Test get Docker version - success"""
        mock_version = {'Version': '20.10.0'}
        mock_client = Mock()
        mock_client.version.return_value = mock_version
        mock_docker.return_value = mock_client
        
        docker_client = EnhancedDockerClient()
        result = docker_client.get_docker_version()
        
        assert result == mock_version

    def test_docker_client_alias(self):
        """Test DockerClient alias"""
        from blastdock.utils.docker_utils import DockerClient
        assert DockerClient == EnhancedDockerClient


class TestDockerExceptions:
    """Test Docker exception classes"""

    def test_docker_error(self):
        """Test DockerError exception"""
        error = DockerError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_docker_not_found_error(self):
        """Test DockerNotFoundError exception"""
        error = DockerNotFoundError("Docker not found")
        assert str(error) == "Docker not found"
        assert isinstance(error, DockerError)

    def test_docker_not_running_error(self):
        """Test DockerNotRunningError exception"""
        error = DockerNotRunningError("Docker not running")
        assert str(error) == "Docker not running"
        assert isinstance(error, DockerError)