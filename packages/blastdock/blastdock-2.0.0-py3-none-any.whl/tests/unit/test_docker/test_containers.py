"""
Test suite for Docker containers management
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from blastdock.docker.containers import ContainerManager
from blastdock.docker.errors import ContainerError


class TestContainerManager:
    """Test cases for ContainerManager class"""

    @patch('blastdock.docker.containers.get_docker_client')
    def test_manager_initialization(self, mock_client):
        """Test ContainerManager initialization"""
        manager = ContainerManager()
        assert manager.docker_client is not None
        assert manager.logger is not None

    @patch('blastdock.docker.containers.get_docker_client')
    def test_list_containers(self, mock_client):
        """Test container listing"""
        mock_docker = Mock()
        mock_docker.execute_command.return_value = Mock(
            success=True,
            stdout='{"ID":"abc123","Names":"/test","Image":"nginx","Status":"running"}\n{"ID":"def456","Names":"/test2","Image":"mysql","Status":"exited"}'
        )
        mock_client.return_value = mock_docker
        
        manager = ContainerManager()
        containers = manager.list_containers()
        
        assert len(containers) == 2
        assert containers[0]['ID'] == 'abc123'
        assert containers[1]['ID'] == 'def456'

    @patch('blastdock.docker.containers.get_docker_client')
    def test_list_containers_with_filters(self, mock_client):
        """Test container listing with filters"""
        mock_docker = Mock()
        mock_docker.execute_command.return_value = Mock(
            success=True,
            stdout='{"ID":"abc123","Names":"/test","Image":"nginx","Status":"running"}'
        )
        mock_client.return_value = mock_docker
        
        manager = ContainerManager()
        containers = manager.list_containers(
            all_containers=True,
            filters={'status': 'running', 'label': 'app=test'}
        )
        
        # Verify filters were applied
        args = mock_docker.execute_command.call_args[0][0]
        assert '-a' in args
        assert '--filter' in args
        assert 'status=running' in ' '.join(args)
        assert 'label=app=test' in ' '.join(args)

    @patch('blastdock.docker.containers.get_docker_client')
    def test_get_container_details(self, mock_client):
        """Test getting container details"""
        mock_docker = Mock()
        mock_docker.execute_command.return_value = Mock(
            success=True,
            stdout='{"Id":"abc123","Name":"/test","Image":"nginx:latest","State":{"Status":"running"}}'
        )
        mock_client.return_value = mock_docker
        
        manager = ContainerManager()
        details = manager.get_container_details('abc123')
        
        assert details is not None
        assert details['Id'] == 'abc123'
        assert details['State']['Status'] == 'running'

    @patch('blastdock.docker.containers.get_docker_client')
    def test_get_container_details_not_found(self, mock_client):
        """Test getting non-existent container details"""
        mock_docker = Mock()
        mock_docker.execute_command.return_value = Mock(
            success=False,
            stderr='Error: No such container: nonexistent'
        )
        mock_client.return_value = mock_docker
        
        manager = ContainerManager()
        
        with pytest.raises(ContainerError):
            manager.get_container_details('nonexistent')

    @patch('blastdock.docker.containers.get_docker_client')
    def test_start_container(self, mock_client):
        """Test container start"""
        mock_docker = Mock()
        mock_docker.execute_command.return_value = Mock(
            success=True,
            stdout='abc123'
        )
        mock_client.return_value = mock_docker
        
        manager = ContainerManager()
        result = manager.start_container('abc123')
        
        assert result is True
        args = mock_docker.execute_command.call_args[0][0]
        assert 'start' in args
        assert 'abc123' in args

    @patch('blastdock.docker.containers.get_docker_client')
    def test_stop_container(self, mock_client):
        """Test container stop"""
        mock_docker = Mock()
        mock_docker.execute_command.return_value = Mock(
            success=True,
            stdout='abc123'
        )
        mock_client.return_value = mock_docker
        
        manager = ContainerManager()
        result = manager.stop_container('abc123', timeout=30)
        
        assert result is True
        args = mock_docker.execute_command.call_args[0][0]
        assert 'stop' in args
        assert '-t' in args
        assert '30' in args
        assert 'abc123' in args

    @patch('blastdock.docker.containers.get_docker_client')
    def test_restart_container(self, mock_client):
        """Test container restart"""
        mock_docker = Mock()
        mock_docker.execute_command.return_value = Mock(
            success=True,
            stdout='abc123'
        )
        mock_client.return_value = mock_docker
        
        manager = ContainerManager()
        result = manager.restart_container('abc123')
        
        assert result is True
        args = mock_docker.execute_command.call_args[0][0]
        assert 'restart' in args
        assert 'abc123' in args

    @patch('blastdock.docker.containers.get_docker_client')
    def test_remove_container(self, mock_client):
        """Test container removal"""
        mock_docker = Mock()
        mock_docker.execute_command.return_value = Mock(
            success=True,
            stdout='abc123'
        )
        mock_client.return_value = mock_docker
        
        manager = ContainerManager()
        result = manager.remove_container('abc123', force=True, remove_volumes=True)
        
        assert result is True
        args = mock_docker.execute_command.call_args[0][0]
        assert 'rm' in args
        assert '-f' in args
        assert '-v' in args
        assert 'abc123' in args

    @patch('blastdock.docker.containers.get_docker_client')
    def test_get_container_logs(self, mock_client):
        """Test getting container logs"""
        mock_logs = "2023-01-01 12:00:00 INFO: Application started\n2023-01-01 12:00:01 INFO: Ready"
        mock_docker = Mock()
        mock_docker.execute_command.return_value = Mock(
            success=True,
            stdout=mock_logs
        )
        mock_client.return_value = mock_docker
        
        manager = ContainerManager()
        logs = manager.get_logs('abc123', tail=100, follow=False, timestamps=True)
        
        assert 'Application started' in logs
        args = mock_docker.execute_command.call_args[0][0]
        assert 'logs' in args
        assert '--tail' in args
        assert '100' in args
        assert '--timestamps' in args
        assert 'abc123' in args

    @patch('blastdock.docker.containers.get_docker_client')
    def test_exec_command(self, mock_client):
        """Test executing command in container"""
        mock_docker = Mock()
        mock_docker.execute_command.return_value = Mock(
            success=True,
            stdout='total 8\ndrwxr-xr-x 2 root root 4096 Jan  1 12:00 app'
        )
        mock_client.return_value = mock_docker
        
        manager = ContainerManager()
        result = manager.exec_command('abc123', 'ls -la')
        
        assert 'app' in result
        args = mock_docker.execute_command.call_args[0][0]
        assert 'exec' in args
        assert 'abc123' in args
        assert 'ls' in args
        assert '-la' in args

    @patch('blastdock.docker.containers.get_docker_client')
    def test_get_container_stats(self, mock_client):
        """Test getting container statistics"""
        mock_docker = Mock()
        mock_docker.execute_command.return_value = Mock(
            success=True,
            stdout='{"memory_stats":{"usage":512000000,"limit":1073741824},"cpu_stats":{"cpu_usage":{"total_usage":1000000}}}'
        )
        mock_client.return_value = mock_docker
        
        manager = ContainerManager()
        stats = manager.get_stats('abc123')
        
        assert stats is not None
        assert 'memory_stats' in stats
        assert stats['memory_stats']['usage'] == 512000000

    @patch('blastdock.docker.containers.get_docker_client')
    def test_wait_for_container(self, mock_client):
        """Test waiting for container to finish"""
        mock_docker = Mock()
        mock_docker.execute_command.return_value = Mock(
            success=True,
            stdout='0'  # Exit code
        )
        mock_client.return_value = mock_docker
        
        manager = ContainerManager()
        exit_code = manager.wait_container('abc123')
        
        assert exit_code == 0
        args = mock_docker.execute_command.call_args[0][0]
        assert 'wait' in args
        assert 'abc123' in args

    @patch('blastdock.docker.containers.get_docker_client')
    def test_container_exists(self, mock_client):
        """Test checking if container exists"""
        mock_docker = Mock()
        # First call succeeds (container exists)
        mock_docker.execute_command.side_effect = [
            Mock(success=True, stdout='{"Id":"abc123"}'),
            Mock(success=False, stderr='Error: No such container')
        ]
        mock_client.return_value = mock_docker
        
        manager = ContainerManager()
        
        # Container exists
        assert manager.container_exists('abc123') is True
        
        # Container doesn't exist
        assert manager.container_exists('nonexistent') is False

    @patch('blastdock.docker.containers.get_docker_client')
    def test_get_container_by_name(self, mock_client):
        """Test getting container by name"""
        mock_docker = Mock()
        mock_docker.execute_command.return_value = Mock(
            success=True,
            stdout='{"ID":"abc123","Names":"/test-container","Image":"nginx"}'
        )
        mock_client.return_value = mock_docker
        
        manager = ContainerManager()
        containers = manager.list_containers(filters={'name': 'test-container'})
        
        assert len(containers) > 0
        assert '/test-container' in containers[0]['Names']

    @patch('blastdock.docker.containers.get_docker_client')
    def test_handle_docker_errors(self, mock_client):
        """Test proper error handling for Docker operations"""
        mock_docker = Mock()
        mock_docker.execute_command.return_value = Mock(
            success=False,
            stderr='Error response from daemon: Container abc123 is not running'
        )
        mock_client.return_value = mock_docker
        
        manager = ContainerManager()
        
        with pytest.raises(ContainerError) as exc_info:
            manager.stop_container('abc123')
        
        assert 'not running' in str(exc_info.value)