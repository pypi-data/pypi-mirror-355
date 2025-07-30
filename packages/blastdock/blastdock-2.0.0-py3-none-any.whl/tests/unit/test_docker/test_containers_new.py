"""Comprehensive tests for Docker containers module."""

import json
import subprocess
from unittest.mock import Mock, patch, MagicMock, call
import pytest

from blastdock.docker.containers import ContainerManager
from blastdock.docker.errors import ContainerError


class TestContainerManager:
    """Test suite for ContainerManager."""

    @pytest.fixture
    def manager(self):
        """Create a ContainerManager instance."""
        with patch('blastdock.docker.containers.get_docker_client') as mock_client:
            mock_client.return_value = Mock()
            manager = ContainerManager()
            return manager

    def test_init(self):
        """Test ContainerManager initialization."""
        with patch('blastdock.docker.containers.get_docker_client') as mock_client:
            mock_docker = Mock()
            mock_client.return_value = mock_docker
            
            manager = ContainerManager()
            
            assert manager.docker_client == mock_docker
            assert manager.logger is not None

    def test_list_containers_success(self, manager):
        """Test successful container listing."""
        container_json1 = '{"ID":"abc123","Names":"/test","Image":"nginx","Status":"running"}'
        container_json2 = '{"ID":"def456","Names":"/test2","Image":"mysql","Status":"exited"}'
        
        mock_result = Mock(stdout=f"{container_json1}\n{container_json2}")
        manager.docker_client.execute_command.return_value = mock_result
        
        containers = manager.list_containers()
        
        assert len(containers) == 2
        assert containers[0]['ID'] == 'abc123'
        assert containers[0]['Names'] == '/test'
        assert containers[1]['ID'] == 'def456'
        assert containers[1]['Names'] == '/test2'
        
        # Check command
        call_args = manager.docker_client.execute_command.call_args
        cmd = call_args[0][0]
        assert cmd == ['docker', 'ps', '--format', '{{json .}}']

    def test_list_containers_all(self, manager):
        """Test listing all containers including stopped ones."""
        mock_result = Mock(stdout='{"ID":"abc123","Names":"/test","Status":"exited"}')
        manager.docker_client.execute_command.return_value = mock_result
        
        containers = manager.list_containers(all_containers=True)
        
        # Check command includes -a flag
        call_args = manager.docker_client.execute_command.call_args
        cmd = call_args[0][0]
        assert '-a' in cmd

    def test_list_containers_with_filters(self, manager):
        """Test listing containers with filters."""
        mock_result = Mock(stdout='{"ID":"abc123","Names":"/test","Status":"running"}')
        manager.docker_client.execute_command.return_value = mock_result
        
        filters = {'status': 'running', 'name': 'test'}
        containers = manager.list_containers(filters=filters)
        
        # Check command includes filters
        call_args = manager.docker_client.execute_command.call_args
        cmd = call_args[0][0]
        assert '--filter' in cmd
        assert 'status=running' in cmd
        assert 'name=test' in cmd

    def test_list_containers_json_decode_error(self, manager):
        """Test handling JSON decode errors in container listing."""
        # Mix of valid and invalid JSON
        invalid_json = "invalid json\n{\"ID\":\"abc123\",\"Names\":\"/test\"}"
        mock_result = Mock(stdout=invalid_json)
        manager.docker_client.execute_command.return_value = mock_result
        
        with patch.object(manager.logger, 'warning') as mock_warning:
            containers = manager.list_containers()
        
        # Should have 1 valid container and 1 warning
        assert len(containers) == 1
        assert containers[0]['ID'] == 'abc123'
        mock_warning.assert_called_once()

    def test_list_containers_empty_result(self, manager):
        """Test listing containers with empty result."""
        mock_result = Mock(stdout="")
        manager.docker_client.execute_command.return_value = mock_result
        
        containers = manager.list_containers()
        
        assert containers == []

    def test_get_container_info_success(self, manager):
        """Test getting container information."""
        container_info = {
            "Id": "abc123",
            "Name": "/test",
            "State": {
                "Status": "running",
                "StartedAt": "2024-01-01T00:00:00Z",
                "Pid": 1234
            },
            "Config": {
                "Image": "nginx:latest",
                "Env": ["PATH=/usr/local/sbin"]
            },
            "NetworkSettings": {
                "IPAddress": "172.17.0.2"
            }
        }
        
        mock_result = Mock(stdout=json.dumps(container_info))
        manager.docker_client.execute_command.return_value = mock_result
        
        result = manager.get_container_info("abc123")
        
        assert result == container_info
        
        # Check command
        call_args = manager.docker_client.execute_command.call_args
        cmd = call_args[0][0]
        assert cmd == ['docker', 'inspect', 'abc123']

    def test_get_container_info_not_found(self, manager):
        """Test getting info for non-existent container."""
        error = subprocess.CalledProcessError(1, "docker inspect")
        error.stderr = "Error: No such container: nonexistent"
        manager.docker_client.execute_command.side_effect = error
        
        with pytest.raises(ContainerError) as exc_info:
            manager.get_container_info("nonexistent")
        
        assert "Failed to get container info" in str(exc_info.value)

    def test_get_container_info_invalid_json(self, manager):
        """Test handling invalid JSON in container info."""
        mock_result = Mock(stdout="invalid json")
        manager.docker_client.execute_command.return_value = mock_result
        
        with pytest.raises(ContainerError) as exc_info:
            manager.get_container_info("abc123")
        
        assert "Failed to parse container info" in str(exc_info.value)

    def test_start_container_success(self, manager):
        """Test successful container start."""
        mock_result = Mock(stdout="abc123", stderr="")
        manager.docker_client.execute_command.return_value = mock_result
        
        with patch.object(manager, 'get_container_info') as mock_info:
            mock_info.return_value = {
                "State": {"Status": "running"},
                "Name": "/test"
            }
            
            result = manager.start_container("abc123")
        
        assert result['success'] is True
        assert result['container_id'] == 'abc123'
        assert result['status'] == 'running'
        
        # Check command
        call_args = manager.docker_client.execute_command.call_args
        cmd = call_args[0][0]
        assert cmd == ['docker', 'start', 'abc123']

    def test_start_container_failure(self, manager):
        """Test container start failure."""
        error = subprocess.CalledProcessError(1, "docker start")
        error.stderr = "Error response from daemon: container already started"
        manager.docker_client.execute_command.side_effect = error
        
        with pytest.raises(ContainerError) as exc_info:
            manager.start_container("abc123")
        
        assert "Failed to start container" in str(exc_info.value)

    def test_stop_container_success(self, manager):
        """Test successful container stop."""
        mock_result = Mock(stdout="abc123", stderr="")
        manager.docker_client.execute_command.return_value = mock_result
        
        with patch.object(manager, 'get_container_info') as mock_info:
            mock_info.return_value = {
                "State": {"Status": "exited"},
                "Name": "/test"
            }
            
            result = manager.stop_container("abc123", timeout=15)
        
        assert result['success'] is True
        assert result['container_id'] == 'abc123'
        assert result['status'] == 'exited'
        
        # Check command includes timeout
        call_args = manager.docker_client.execute_command.call_args
        cmd = call_args[0][0]
        assert cmd == ['docker', 'stop', '-t', '15', 'abc123']

    def test_stop_container_default_timeout(self, manager):
        """Test stopping container with default timeout."""
        mock_result = Mock(stdout="abc123")
        manager.docker_client.execute_command.return_value = mock_result
        
        with patch.object(manager, 'get_container_info') as mock_info:
            mock_info.return_value = {"State": {"Status": "exited"}, "Name": "/test"}
            
            manager.stop_container("abc123")
        
        # Check default timeout is used
        call_args = manager.docker_client.execute_command.call_args
        cmd = call_args[0][0]
        assert '10' in cmd  # Default timeout

    def test_remove_container_success(self, manager):
        """Test successful container removal."""
        mock_result = Mock(stdout="abc123", stderr="")
        manager.docker_client.execute_command.return_value = mock_result
        
        result = manager.remove_container("abc123", force=True, volumes=True)
        
        assert result['success'] is True
        assert result['container_id'] == 'abc123'
        
        # Check command includes force and volumes flags
        call_args = manager.docker_client.execute_command.call_args
        cmd = call_args[0][0]
        assert cmd == ['docker', 'rm', '-f', '-v', 'abc123']

    def test_remove_container_basic(self, manager):
        """Test basic container removal without flags."""
        mock_result = Mock(stdout="abc123")
        manager.docker_client.execute_command.return_value = mock_result
        
        result = manager.remove_container("abc123")
        
        # Check command doesn't include flags
        call_args = manager.docker_client.execute_command.call_args
        cmd = call_args[0][0]
        assert cmd == ['docker', 'rm', 'abc123']

    def test_restart_container_success(self, manager):
        """Test successful container restart."""
        mock_result = Mock(stdout="abc123", stderr="")
        manager.docker_client.execute_command.return_value = mock_result
        
        with patch.object(manager, 'get_container_info') as mock_info:
            mock_info.return_value = {
                "State": {"Status": "running"},
                "Name": "/test"
            }
            
            result = manager.restart_container("abc123", timeout=20)
        
        assert result['success'] is True
        assert result['container_id'] == 'abc123'
        assert result['status'] == 'running'
        
        # Check command includes timeout
        call_args = manager.docker_client.execute_command.call_args
        cmd = call_args[0][0]
        assert cmd == ['docker', 'restart', '-t', '20', 'abc123']

    def test_get_container_logs_success(self, manager):
        """Test getting container logs."""
        log_output = "2024-01-01 nginx started\n2024-01-01 Ready to serve"
        mock_result = Mock(stdout=log_output, stderr="")
        manager.docker_client.execute_command.return_value = mock_result
        
        result = manager.get_container_logs("abc123", tail=50, follow=False)
        
        assert result['success'] is True
        assert result['logs'] == log_output
        
        # Check command
        call_args = manager.docker_client.execute_command.call_args
        cmd = call_args[0][0]
        assert 'logs' in cmd
        assert '--tail' in cmd
        assert '50' in cmd
        assert 'abc123' in cmd

    def test_get_container_logs_with_timestamps(self, manager):
        """Test getting logs with timestamps."""
        mock_result = Mock(stdout="timestamped logs")
        manager.docker_client.execute_command.return_value = mock_result
        
        result = manager.get_container_logs("abc123", timestamps=True, since="2024-01-01")
        
        # Check command includes timestamp and since options
        call_args = manager.docker_client.execute_command.call_args
        cmd = call_args[0][0]
        assert '--timestamps' in cmd
        assert '--since' in cmd
        assert '2024-01-01' in cmd

    def test_execute_command_in_container_success(self, manager):
        """Test executing command in container."""
        command_output = "total 4\ndrwxr-xr-x 2 root root 4096 Jan  1 00:00 test"
        mock_result = Mock(stdout=command_output, stderr="", returncode=0)
        manager.docker_client.execute_command.return_value = mock_result
        
        result = manager.execute_command_in_container(
            "abc123", 
            ["ls", "-la"],
            interactive=False,
            tty=False,
            user="root",
            workdir="/app"
        )
        
        assert result['success'] is True
        assert result['output'] == command_output
        assert result['exit_code'] == 0
        
        # Check command
        call_args = manager.docker_client.execute_command.call_args
        cmd = call_args[0][0]
        assert 'exec' in cmd
        assert '--user' in cmd
        assert 'root' in cmd
        assert '--workdir' in cmd
        assert '/app' in cmd
        assert 'abc123' in cmd
        assert 'ls' in cmd
        assert '-la' in cmd

    def test_execute_command_in_container_interactive(self, manager):
        """Test executing interactive command in container."""
        mock_result = Mock(stdout="output", returncode=0)
        manager.docker_client.execute_command.return_value = mock_result
        
        result = manager.execute_command_in_container(
            "abc123",
            ["bash"],
            interactive=True,
            tty=True
        )
        
        # Check command includes -it flags
        call_args = manager.docker_client.execute_command.call_args
        cmd = call_args[0][0]
        assert '-it' in cmd

    def test_copy_to_container_success(self, manager):
        """Test copying file to container."""
        mock_result = Mock(stdout="", stderr="")
        manager.docker_client.execute_command.return_value = mock_result
        
        result = manager.copy_to_container("abc123", "/host/file.txt", "/container/path/")
        
        assert result['success'] is True
        assert result['source'] == "/host/file.txt"
        assert result['destination'] == "/container/path/"
        
        # Check command
        call_args = manager.docker_client.execute_command.call_args
        cmd = call_args[0][0]
        assert cmd == ['docker', 'cp', '/host/file.txt', 'abc123:/container/path/']

    def test_copy_from_container_success(self, manager):
        """Test copying file from container."""
        mock_result = Mock(stdout="", stderr="")
        manager.docker_client.execute_command.return_value = mock_result
        
        result = manager.copy_from_container("abc123", "/container/file.txt", "/host/path/")
        
        assert result['success'] is True
        assert result['source'] == "/container/file.txt"
        assert result['destination'] == "/host/path/"
        
        # Check command
        call_args = manager.docker_client.execute_command.call_args
        cmd = call_args[0][0]
        assert cmd == ['docker', 'cp', 'abc123:/container/file.txt', '/host/path/']

    def test_get_container_stats_success(self, manager):
        """Test getting container statistics."""
        stats_json = {
            "container": "abc123",
            "cpu": "50.0%",
            "memory": "100MB / 1GB",
            "network": "1KB / 2KB",
            "block": "10MB / 20MB"
        }
        
        mock_result = Mock(stdout=json.dumps(stats_json))
        manager.docker_client.execute_command.return_value = mock_result
        
        result = manager.get_container_stats("abc123")
        
        assert result['success'] is True
        assert result['stats']['cpu'] == "50.0%"
        assert result['stats']['memory'] == "100MB / 1GB"
        
        # Check command
        call_args = manager.docker_client.execute_command.call_args
        cmd = call_args[0][0]
        assert cmd == ['docker', 'stats', '--no-stream', '--format', '{{json .}}', 'abc123']

    def test_get_container_stats_streaming(self, manager):
        """Test getting streaming container statistics."""
        mock_result = Mock(stdout='{"cpu":"50%"}')
        manager.docker_client.execute_command.return_value = mock_result
        
        result = manager.get_container_stats("abc123", stream=True)
        
        # Check command doesn't include --no-stream
        call_args = manager.docker_client.execute_command.call_args
        cmd = call_args[0][0]
        assert '--no-stream' not in cmd

    def test_create_container_success(self, manager):
        """Test successful container creation."""
        mock_result = Mock(stdout="abc123", stderr="")
        manager.docker_client.execute_command.return_value = mock_result
        
        with patch.object(manager, 'get_container_info') as mock_info:
            mock_info.return_value = {
                "Id": "abc123",
                "Name": "/test",
                "State": {"Status": "created"}
            }
            
            result = manager.create_container(
                image="nginx:latest",
                name="test",
                ports={"80": "8080"},
                volumes={"/host": "/container"},
                environment={"ENV_VAR": "value"},
                command=["nginx", "-g", "daemon off;"]
            )
        
        assert result['success'] is True
        assert result['container_id'] == 'abc123'
        assert result['container_name'] == '/test'
        
        # Check command includes all options
        call_args = manager.docker_client.execute_command.call_args
        cmd = call_args[0][0]
        assert 'create' in cmd
        assert '--name' in cmd
        assert 'test' in cmd
        assert '-p' in cmd
        assert '80:8080' in cmd
        assert '-v' in cmd
        assert '/host:/container' in cmd
        assert '-e' in cmd
        assert 'ENV_VAR=value' in cmd
        assert 'nginx:latest' in cmd

    def test_create_container_minimal(self, manager):
        """Test creating container with minimal options."""
        mock_result = Mock(stdout="abc123")
        manager.docker_client.execute_command.return_value = mock_result
        
        with patch.object(manager, 'get_container_info') as mock_info:
            mock_info.return_value = {"Id": "abc123", "State": {"Status": "created"}}
            
            result = manager.create_container("nginx")
        
        # Check minimal command
        call_args = manager.docker_client.execute_command.call_args
        cmd = call_args[0][0]
        assert cmd[-1] == 'nginx'  # Image should be last
        assert 'create' in cmd

    def test_prune_containers_success(self, manager):
        """Test pruning containers."""
        prune_output = "Deleted Containers:\nabc123\ndef456\n\nTotal reclaimed space: 100MB"
        mock_result = Mock(stdout=prune_output, stderr="")
        manager.docker_client.execute_command.return_value = mock_result
        
        result = manager.prune_containers()
        
        assert result['success'] is True
        assert result['containers_removed'] == 2
        assert result['space_reclaimed'] == "100MB"
        
        # Check command
        call_args = manager.docker_client.execute_command.call_args
        cmd = call_args[0][0]
        assert cmd == ['docker', 'container', 'prune', '-f']

    def test_prune_containers_with_filters(self, manager):
        """Test pruning containers with filters."""
        mock_result = Mock(stdout="Total reclaimed space: 50MB")
        manager.docker_client.execute_command.return_value = mock_result
        
        filters = {'until': '24h'}
        result = manager.prune_containers(filters=filters)
        
        # Check command includes filters
        call_args = manager.docker_client.execute_command.call_args
        cmd = call_args[0][0]
        assert '--filter' in cmd
        assert 'until=24h' in cmd

    def test_prune_containers_no_containers(self, manager):
        """Test pruning when no containers to remove."""
        mock_result = Mock(stdout="Total reclaimed space: 0B")
        manager.docker_client.execute_command.return_value = mock_result
        
        result = manager.prune_containers()
        
        assert result['success'] is True
        assert result['containers_removed'] == 0
        assert result['space_reclaimed'] == "0B"

    def test_error_handling_in_operations(self, manager):
        """Test error handling in various operations."""
        error = subprocess.CalledProcessError(1, "docker command")
        error.stderr = "Generic Docker error"
        manager.docker_client.execute_command.side_effect = error
        
        # Test that all operations raise ContainerError
        with pytest.raises(ContainerError):
            manager.start_container("abc123")
        
        with pytest.raises(ContainerError):
            manager.stop_container("abc123")
        
        with pytest.raises(ContainerError):
            manager.remove_container("abc123")
        
        with pytest.raises(ContainerError):
            manager.restart_container("abc123")

    def test_timing_measurement(self, manager):
        """Test that timing is measured in operations."""
        def slow_execute(*args, **kwargs):
            import time
            time.sleep(0.1)  # 100ms delay
            return Mock(stdout="abc123")
        
        manager.docker_client.execute_command.side_effect = slow_execute
        
        with patch.object(manager, 'get_container_info') as mock_info:
            mock_info.return_value = {"State": {"Status": "running"}, "Name": "/test"}
            
            result = manager.start_container("abc123")
        
        assert result['start_time'] >= 0.1

    def test_list_containers_command_error(self, manager):
        """Test handling command error in list_containers."""
        error = subprocess.CalledProcessError(1, "docker ps")
        manager.docker_client.execute_command.side_effect = error
        
        with pytest.raises(ContainerError):
            manager.list_containers()

    def test_container_stats_json_error(self, manager):
        """Test handling JSON error in container stats."""
        mock_result = Mock(stdout="invalid json")
        manager.docker_client.execute_command.return_value = mock_result
        
        with pytest.raises(ContainerError) as exc_info:
            manager.get_container_stats("abc123")
        
        assert "Failed to parse container stats" in str(exc_info.value)

    def test_execute_command_failure(self, manager):
        """Test command execution failure in container."""
        mock_result = Mock(stdout="", stderr="command not found", returncode=127)
        manager.docker_client.execute_command.return_value = mock_result
        
        result = manager.execute_command_in_container("abc123", ["nonexistent"])
        
        assert result['success'] is False
        assert result['exit_code'] == 127
        assert result['error'] == "command not found"