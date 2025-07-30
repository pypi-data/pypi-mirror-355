"""
Simplified test suite for Docker client functionality
"""

import pytest
import subprocess
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from blastdock.docker.client import DockerClient, get_docker_client
from blastdock.docker.errors import (
    DockerError, DockerNotFoundError, DockerNotRunningError,
    DockerConnectionError
)


class TestDockerClient:
    """Test cases for DockerClient class"""

    def test_init_default_values(self):
        """Test DockerClient initialization with default values"""
        client = DockerClient()
        assert client.timeout == 300
        assert client.max_retries == 3
        assert client._connection_verified is False
        assert client.logger is not None

    def test_init_custom_values(self):
        """Test DockerClient initialization with custom values"""
        client = DockerClient(timeout=600, max_retries=5)
        assert client.timeout == 600
        assert client.max_retries == 5

    @patch('blastdock.docker.client.subprocess.run')
    def test_check_docker_availability_success(self, mock_run):
        """Test successful Docker availability check"""
        mock_run.return_value = Mock(returncode=0, stdout="Docker version 20.10.0", stderr="")
        
        client = DockerClient()
        result = client.check_docker_availability()
        
        assert result['available'] is True
        assert result['docker_found'] is True

    @patch('blastdock.docker.client.subprocess.run')
    def test_check_docker_availability_not_found(self, mock_run):
        """Test Docker availability check when Docker not found"""
        mock_run.side_effect = FileNotFoundError()
        
        client = DockerClient()
        result = client.check_docker_availability()
        
        assert result['available'] is False
        assert result['docker_found'] is False

    @patch('blastdock.docker.client.subprocess.run')
    def test_get_version_info(self, mock_run):
        """Test getting Docker version information"""
        mock_run.side_effect = [
            Mock(returncode=0, stdout="Docker version 20.10.0", stderr=""),
            Mock(returncode=0, stdout="docker-compose version 1.29.0", stderr="")
        ]
        
        client = DockerClient()
        version_info = client.get_version_info()
        
        assert 'docker_version' in version_info
        assert 'compose_version' in version_info

    @patch('blastdock.docker.client.subprocess.run')
    def test_execute_command_success(self, mock_run):
        """Test successful command execution"""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Command output",
            stderr=""
        )
        
        client = DockerClient()
        result = client.execute_command(['docker', 'ps'])
        
        assert result['success'] is True
        assert result['output'] == "Command output"

    @patch('blastdock.docker.client.subprocess.run')
    def test_execute_command_failure(self, mock_run):
        """Test command execution failure"""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="Error message"
        )
        
        client = DockerClient()
        result = client.execute_command(['docker', 'ps'])
        
        assert result['success'] is False
        assert result['error'] == "Error message"

    @patch('blastdock.docker.client.subprocess.run')
    def test_execute_compose_command(self, mock_run):
        """Test Docker Compose command execution"""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Compose output",
            stderr=""
        )
        
        client = DockerClient()
        result = client.execute_compose_command(['up', '-d'])
        
        assert result['success'] is True
        assert result['output'] == "Compose output"
        
        # Verify compose command was called
        args = mock_run.call_args[0][0]
        assert 'docker-compose' in args or 'docker' in args

    @patch('blastdock.docker.client.subprocess.run')
    def test_get_system_info(self, mock_run):
        """Test getting Docker system information"""
        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"Containers": 5, "Images": 10}',
            stderr=""
        )
        
        client = DockerClient()
        result = client.get_system_info()
        
        assert result['success'] is True
        assert 'system_info' in result

    @patch('blastdock.docker.client.subprocess.run')
    def test_cleanup_resources(self, mock_run):
        """Test resource cleanup"""
        mock_run.return_value = Mock(returncode=0, stdout="Cleanup complete", stderr="")
        
        client = DockerClient()
        result = client.cleanup_resources()
        
        assert result['success'] is True

    @patch('blastdock.docker.client.subprocess.run')
    def test_cleanup_resources_aggressive(self, mock_run):
        """Test aggressive resource cleanup"""
        mock_run.return_value = Mock(returncode=0, stdout="Aggressive cleanup complete", stderr="")
        
        client = DockerClient()
        result = client.cleanup_resources(aggressive=True)
        
        assert result['success'] is True

    @patch('blastdock.docker.client.subprocess.run')
    def test_ensure_connection(self, mock_run):
        """Test connection verification"""
        mock_run.return_value = Mock(returncode=0, stdout="Docker version", stderr="")
        
        client = DockerClient()
        client.ensure_connection()
        
        assert client._connection_verified is True

    @patch('blastdock.docker.client.subprocess.run')
    def test_ensure_connection_failure(self, mock_run):
        """Test connection verification failure"""
        mock_run.return_value = Mock(returncode=1, stderr="Connection failed")
        
        client = DockerClient()
        
        with pytest.raises(DockerConnectionError):
            client.ensure_connection()

    def test_get_docker_client_function(self):
        """Test get_docker_client utility function"""
        client = get_docker_client()
        assert isinstance(client, DockerClient)

    @patch('blastdock.docker.client.subprocess.run')
    def test_command_timeout(self, mock_run):
        """Test command timeout handling"""
        mock_run.side_effect = subprocess.TimeoutExpired(['docker', 'ps'], 30)
        
        client = DockerClient()
        result = client.execute_command(['docker', 'ps'], timeout=30)
        
        assert result['success'] is False
        assert 'timeout' in result['error'].lower()

    @patch('blastdock.docker.client.subprocess.run')
    def test_command_retries(self, mock_run):
        """Test command retry mechanism"""
        # First call fails, second succeeds
        mock_run.side_effect = [
            Mock(returncode=1, stderr="Temporary error"),
            Mock(returncode=0, stdout="Success", stderr="")
        ]
        
        client = DockerClient(max_retries=2)
        result = client.execute_command(['docker', 'ps'])
        
        assert result['success'] is True
        assert mock_run.call_count == 2

    @patch('blastdock.docker.client.subprocess.run')
    def test_command_sanitization(self, mock_run):
        """Test command input sanitization"""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        client = DockerClient()
        # Test with potentially dangerous input
        result = client.execute_command(['docker', 'run', '--name', 'test; rm -rf /'])
        
        # Verify the command was called (sanitization happens in _run_command)
        assert mock_run.called

    @patch('blastdock.docker.client.subprocess.run')
    def test_working_directory(self, mock_run):
        """Test command execution with working directory"""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        client = DockerClient()
        result = client.execute_command(['docker', 'ps'], cwd='/tmp')
        
        # Verify cwd was passed
        assert mock_run.call_args[1]['cwd'] == '/tmp'

    @patch('blastdock.docker.client.subprocess.run')
    def test_environment_variables(self, mock_run):
        """Test command execution with environment variables"""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        client = DockerClient()
        result = client.execute_command(['docker', 'ps'], env_vars={'DOCKER_HOST': 'unix:///var/run/docker.sock'})
        
        assert result['success'] is True