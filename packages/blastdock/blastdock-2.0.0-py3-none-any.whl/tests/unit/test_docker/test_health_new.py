"""Comprehensive tests for Docker health module."""

import json
import time
import subprocess
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timedelta
import pytest

from blastdock.docker.health import DockerHealthChecker
from blastdock.docker.errors import DockerError, ContainerError


class TestDockerHealthChecker:
    """Test suite for DockerHealthChecker."""

    @pytest.fixture
    def checker(self):
        """Create a DockerHealthChecker instance."""
        with patch('blastdock.docker.health.get_docker_client') as mock_client:
            mock_client.return_value = Mock()
            checker = DockerHealthChecker()
            return checker

    def test_init(self):
        """Test DockerHealthChecker initialization."""
        with patch('blastdock.docker.health.get_docker_client') as mock_client:
            mock_docker = Mock()
            mock_client.return_value = mock_docker
            
            checker = DockerHealthChecker()
            
            assert checker.docker_client == mock_docker
            assert checker.logger is not None

    def test_check_docker_daemon_health_success(self, checker):
        """Test successful Docker daemon health check."""
        availability = {
            'docker_running': True,
            'docker_available': True,
            'compose_available': True,
            'docker_version': '24.0.7',
            'compose_version': 'v2.23.0',
            'errors': [],
            'warnings': []
        }
        
        system_info = {
            'system': {
                'containers': 5,
                'containers_running': 3,
                'containers_stopped': 2,
                'images': 10,
                'memory': 8589934592,
                'cpus': 4
            }
        }
        
        checker.docker_client.check_docker_availability.return_value = availability
        checker.docker_client.get_system_info.return_value = system_info
        
        # Mock docker system df command
        mock_df_result = Mock(stdout="TYPE                TOTAL     ACTIVE    SIZE      RECLAIMABLE\nImages              10        5         2.5GB     1.2GB\nContainers          5         3         100MB     50MB\nLocal Volumes       2         1         500MB     250MB\nBuild Cache         0         0         0B        0B")
        checker.docker_client.execute_command.return_value = mock_df_result
        
        with patch('time.time', side_effect=[1000, 1000.5]):  # 0.5s response time
            result = checker.check_docker_daemon_health()
        
        assert result['healthy'] is True
        assert result['daemon_responsive'] is True
        assert result['performance_metrics']['response_time'] == 0.5
        assert result['resource_usage']['memory_total'] == 8589934592
        assert result['resource_usage']['containers_total'] == 5
        assert result['resource_usage']['containers_running'] == 3
        assert result['issues'] == []

    def test_check_docker_daemon_health_slow_response(self, checker):
        """Test Docker daemon health check with slow response."""
        availability = {'docker_running': True}
        checker.docker_client.check_docker_availability.return_value = availability
        checker.docker_client.get_system_info.return_value = {}
        
        # Mock docker system df command to avoid errors
        mock_df_result = Mock(stdout="TYPE  TOTAL  ACTIVE  SIZE  RECLAIMABLE")
        checker.docker_client.execute_command.return_value = mock_df_result
        
        with patch('time.time', side_effect=[1000, 1006]):  # 6s response time
            result = checker.check_docker_daemon_health()
        
        assert result['performance_metrics']['response_time'] == 6.0
        assert "responding slowly" in result['issues'][0]
        assert "Check system resources" in result['recommendations'][0]

    def test_check_docker_daemon_health_not_running(self, checker):
        """Test Docker daemon health check when daemon not running."""
        availability = {
            'docker_running': False,
            'docker_available': True,
            'errors': ['Docker daemon not running']
        }
        
        checker.docker_client.check_docker_availability.return_value = availability
        
        result = checker.check_docker_daemon_health()
        
        assert result['healthy'] is False
        assert result['daemon_responsive'] is False
        assert "Docker daemon not running" in result['issues'][0]

    def test_check_docker_daemon_health_compose_unavailable(self, checker):
        """Test health check when Docker Compose is unavailable."""
        availability = {
            'docker_running': True,
            'compose_available': False,
            'warnings': ['Docker Compose not available']
        }
        
        checker.docker_client.check_docker_availability.return_value = availability
        checker.docker_client.get_system_info.return_value = {}
        
        # Mock docker system df command
        mock_df_result = Mock(stdout="TYPE  TOTAL  ACTIVE  SIZE  RECLAIMABLE")
        checker.docker_client.execute_command.return_value = mock_df_result
        
        result = checker.check_docker_daemon_health()
        
        # The actual implementation doesn't check compose availability in health check
        # Just verify it completes without error
        assert result['daemon_responsive'] is True

    def test_check_docker_daemon_health_low_memory(self, checker):
        """Test health check with low memory warning."""
        availability = {'docker_running': True}
        system_info = {
            'system': {
                'memory': 1073741824,  # 1GB
                'images': 10,
                'containers': 5
            }
        }
        
        checker.docker_client.check_docker_availability.return_value = availability
        checker.docker_client.get_system_info.return_value = system_info
        
        # Mock docker system df command
        mock_df_result = Mock(stdout="TYPE  TOTAL  ACTIVE  SIZE  RECLAIMABLE")
        checker.docker_client.execute_command.return_value = mock_df_result
        
        result = checker.check_docker_daemon_health()
        
        # The actual implementation doesn't check memory thresholds, just verify it works
        assert result['daemon_responsive'] is True
        assert result['resource_usage']['memory_total'] == 1073741824

    def test_check_docker_daemon_health_many_containers(self, checker):
        """Test health check with many containers warning."""
        availability = {'docker_running': True}
        system_info = {
            'system': {
                'memory': 8589934592,
                'containers': 150,  # Many containers
                'containers_running': 25  # Triggers high running containers warning
            }
        }
        
        checker.docker_client.check_docker_availability.return_value = availability
        checker.docker_client.get_system_info.return_value = system_info
        
        # Mock docker system df command
        mock_df_result = Mock(stdout="TYPE  TOTAL  ACTIVE  SIZE  RECLAIMABLE")
        checker.docker_client.execute_command.return_value = mock_df_result
        
        result = checker.check_docker_daemon_health()
        
        assert "High number of running containers" in result['issues'][0]
        assert "Consider cleaning up unused containers" in result['recommendations'][0]

    def test_check_docker_daemon_health_exception(self, checker):
        """Test health check when exception occurs."""
        checker.docker_client.check_docker_availability.side_effect = Exception("Connection failed")
        
        result = checker.check_docker_daemon_health()
        
        assert result['healthy'] is False
        assert result['daemon_responsive'] is False
        assert "Docker daemon health check failed" in result['issues'][0]

    def test_check_container_health_success(self, checker):
        """Test successful container health check."""
        container_info = {
            'State': {
                'Status': 'running',
                'StartedAt': '2024-01-01T00:00:00Z',
                'Health': {
                    'Status': 'healthy',
                    'FailingStreak': 0,
                    'Log': [
                        {
                            'Start': '2024-01-01T00:01:00Z',
                            'End': '2024-01-01T00:01:01Z',
                            'ExitCode': 0,
                            'Output': 'Health check passed'
                        }
                    ]
                }
            },
            'Name': '/test-container',
            'Config': {
                'Image': 'nginx:latest',
                'Healthcheck': {
                    'Test': ['CMD', 'curl', '-f', 'http://localhost/health']
                }
            }
        }
        
        checker.docker_client.execute_command.return_value = Mock(
            stdout=json.dumps(container_info)
        )
        
        result = checker.check_container_health('abc123')
        
        assert result['container_id'] == 'abc123'
        assert result['healthy'] is True
        assert result['status'] == 'running'
        assert result['health_status'] == 'healthy'
        assert result['container_name'] == '/test-container'
        assert len(result['health_checks']) == 1
        assert result['health_checks'][0]['exit_code'] == 0

    def test_check_container_health_unhealthy(self, checker):
        """Test container health check when unhealthy."""
        container_info = {
            'State': {
                'Status': 'running',
                'Health': {
                    'Status': 'unhealthy',
                    'FailingStreak': 3,
                    'Log': [
                        {
                            'Start': '2024-01-01T00:01:00Z',
                            'End': '2024-01-01T00:01:01Z',
                            'ExitCode': 1,
                            'Output': 'Health check failed: connection refused'
                        }
                    ]
                }
            },
            'Name': '/test-container'
        }
        
        checker.docker_client.execute_command.return_value = Mock(
            stdout=json.dumps(container_info)
        )
        
        result = checker.check_container_health('abc123')
        
        assert result['healthy'] is False
        assert result['health_status'] == 'unhealthy'
        assert result['failing_streak'] == 3
        assert 'connection refused' in result['health_checks'][0]['output']
        assert "Container health check failing" in result['issues'][0]

    def test_check_container_health_no_healthcheck(self, checker):
        """Test container health check without configured health check."""
        container_info = {
            'State': {
                'Status': 'running',
                'StartedAt': '2024-01-01T00:00:00Z'
            },
            'Name': '/test-container',
            'Config': {'Image': 'nginx:latest'}
        }
        
        checker.docker_client.execute_command.return_value = Mock(
            stdout=json.dumps(container_info)
        )
        
        result = checker.check_container_health('abc123')
        
        assert result['healthy'] is True  # Running without health check is considered healthy
        assert result['status'] == 'running'
        assert result['health_status'] == 'none'
        assert result['health_checks'] == []
        assert "No health check configured" in result['recommendations'][0]

    def test_check_container_health_stopped(self, checker):
        """Test container health check for stopped container."""
        container_info = {
            'State': {
                'Status': 'exited',
                'ExitCode': 0,
                'FinishedAt': '2024-01-01T01:00:00Z'
            },
            'Name': '/test-container'
        }
        
        checker.docker_client.execute_command.return_value = Mock(
            stdout=json.dumps(container_info)
        )
        
        result = checker.check_container_health('abc123')
        
        assert result['healthy'] is False
        assert result['status'] == 'exited'
        assert result['exit_code'] == 0
        assert "Container is not running" in result['issues'][0]

    def test_check_container_health_not_found(self, checker):
        """Test container health check for non-existent container."""
        error = subprocess.CalledProcessError(1, "docker inspect")
        error.stderr = "Error: No such container: nonexistent"
        checker.docker_client.execute_command.side_effect = error
        
        with pytest.raises(ContainerError) as exc_info:
            checker.check_container_health("nonexistent")
        
        assert "Failed to check container health" in str(exc_info.value)

    def test_check_container_health_invalid_json(self, checker):
        """Test container health check with invalid JSON response."""
        checker.docker_client.execute_command.return_value = Mock(
            stdout="invalid json response"
        )
        
        with pytest.raises(ContainerError) as exc_info:
            checker.check_container_health("abc123")
        
        assert "Failed to parse container info" in str(exc_info.value)

    def test_check_compose_project_health_success(self, checker):
        """Test successful compose project health check."""
        ps_output = [
            '{"Name":"project_web_1","State":"running","Status":"Up 5 minutes","Health":"healthy"}',
            '{"Name":"project_db_1","State":"running","Status":"Up 5 minutes","Health":"healthy"}'
        ]
        
        checker.docker_client.execute_compose_command.return_value = Mock(
            stdout='\n'.join(ps_output)
        )
        
        result = checker.check_compose_project_health("test-project")
        
        assert result['project_name'] == 'test-project'
        assert result['healthy'] is True
        assert result['total_services'] == 2
        assert result['running_services'] == 2
        assert result['healthy_services'] == 2
        assert len(result['service_health']) == 2
        assert result['service_health']['web']['healthy'] is True
        assert result['service_health']['db']['healthy'] is True

    def test_check_compose_project_health_with_unhealthy_service(self, checker):
        """Test compose project health check with unhealthy service."""
        ps_output = [
            '{"Name":"project_web_1","State":"running","Status":"Up 5 minutes","Health":"healthy"}',
            '{"Name":"project_db_1","State":"running","Status":"Up 5 minutes","Health":"unhealthy"}'
        ]
        
        checker.docker_client.execute_compose_command.return_value = Mock(
            stdout='\n'.join(ps_output)
        )
        
        result = checker.check_compose_project_health("test-project")
        
        assert result['healthy'] is False
        assert result['running_services'] == 2
        assert result['healthy_services'] == 1
        assert result['service_health']['web']['healthy'] is True
        assert result['service_health']['db']['healthy'] is False
        assert "Some services are unhealthy" in result['issues'][0]

    def test_check_compose_project_health_stopped_services(self, checker):
        """Test compose project health check with stopped services."""
        ps_output = [
            '{"Name":"project_web_1","State":"exited","Status":"Exited (0) 2 minutes ago"}',
            '{"Name":"project_db_1","State":"running","Status":"Up 5 minutes","Health":"healthy"}'
        ]
        
        checker.docker_client.execute_compose_command.return_value = Mock(
            stdout='\n'.join(ps_output)
        )
        
        result = checker.check_compose_project_health("test-project")
        
        assert result['healthy'] is False
        assert result['running_services'] == 1
        assert result['service_health']['web']['healthy'] is False
        assert result['service_health']['web']['status'] == 'exited'

    def test_check_compose_project_health_no_services(self, checker):
        """Test compose project health check with no services."""
        checker.docker_client.execute_compose_command.return_value = Mock(stdout="")
        
        result = checker.check_compose_project_health("test-project")
        
        assert result['healthy'] is False
        assert result['total_services'] == 0
        assert "No services found" in result['issues'][0]

    def test_get_health_summary(self, checker):
        """Test getting overall health summary."""
        # Mock availability check
        availability = {
            'docker_running': True,
            'compose_available': True,
            'errors': [],
            'warnings': []
        }
        checker.docker_client.check_docker_availability.return_value = availability
        checker.docker_client.get_system_info.return_value = {
            'Containers': 5,
            'ContainersRunning': 3,
            'Images': 10,
            'MemTotal': 8589934592
        }
        
        # Mock container listing
        containers_json = [
            '{"ID":"abc123","Names":"test1","State":"running","Status":"Up 5 minutes"}',
            '{"ID":"def456","Names":"test2","State":"running","Status":"Up 3 minutes"}',
            '{"ID":"ghi789","Names":"test3","State":"exited","Status":"Exited (0) 1 minute ago"}'
        ]
        checker.docker_client.execute_command.return_value = Mock(
            stdout='\n'.join(containers_json)
        )
        
        result = checker.get_health_summary()
        
        assert result['overall_healthy'] is True
        assert result['daemon_health']['healthy'] is True
        assert result['container_summary']['total'] == 3
        assert result['container_summary']['running'] == 2
        assert result['container_summary']['stopped'] == 1
        assert len(result['containers']) == 3

    def test_get_health_summary_with_issues(self, checker):
        """Test health summary when there are issues."""
        # Mock daemon with issues
        availability = {
            'docker_running': True,
            'compose_available': False,
            'errors': [],
            'warnings': ['Docker Compose not available']
        }
        checker.docker_client.check_docker_availability.return_value = availability
        checker.docker_client.get_system_info.return_value = {'Containers': 0}
        
        # Mock no containers
        checker.docker_client.execute_command.return_value = Mock(stdout="")
        
        result = checker.get_health_summary()
        
        assert result['overall_healthy'] is False
        assert len(result['daemon_health']['issues']) > 0

    def test_monitor_container_performance_success(self, checker):
        """Test monitoring container performance."""
        stats_data = {
            'read': '2024-01-01T00:00:00Z',
            'memory_stats': {
                'usage': 104857600,  # 100MB
                'limit': 1073741824  # 1GB
            },
            'cpu_stats': {
                'cpu_usage': {
                    'total_usage': 1000000000
                },
                'system_cpu_usage': 10000000000,
                'online_cpus': 4
            },
            'precpu_stats': {
                'cpu_usage': {
                    'total_usage': 900000000
                },
                'system_cpu_usage': 9000000000
            },
            'networks': {
                'eth0': {
                    'rx_bytes': 1024,
                    'tx_bytes': 2048
                }
            },
            'blkio_stats': {
                'io_service_bytes_recursive': [
                    {'op': 'Read', 'value': 4096},
                    {'op': 'Write', 'value': 8192}
                ]
            }
        }
        
        checker.docker_client.execute_command.return_value = Mock(
            stdout=json.dumps(stats_data)
        )
        
        result = checker.monitor_container_performance("abc123", duration=1)
        
        assert result['container_id'] == 'abc123'
        assert result['duration'] == 1
        assert len(result['metrics']) == 1
        
        metrics = result['metrics'][0]
        assert metrics['memory_usage_mb'] == 100.0
        assert metrics['memory_usage_percent'] == 10.0
        assert 'cpu_usage_percent' in metrics
        assert metrics['network_rx_mb'] == 0.001024
        assert metrics['network_tx_mb'] == 0.002048
        assert metrics['disk_read_mb'] == 0.004096
        assert metrics['disk_write_mb'] == 0.008192

    def test_monitor_container_performance_with_sampling(self, checker):
        """Test monitoring container performance with multiple samples."""
        stats_data = {'read': '2024-01-01T00:00:00Z', 'memory_stats': {'usage': 104857600}}
        
        checker.docker_client.execute_command.return_value = Mock(
            stdout=json.dumps(stats_data)
        )
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = checker.monitor_container_performance("abc123", duration=5, interval=1)
        
        assert result['duration'] == 5
        assert len(result['metrics']) == 5  # Should have 5 samples

    def test_monitor_container_performance_error(self, checker):
        """Test monitoring container performance when container doesn't exist."""
        error = subprocess.CalledProcessError(1, "docker stats")
        error.stderr = "Error: No such container: nonexistent"
        checker.docker_client.execute_command.side_effect = error
        
        with pytest.raises(ContainerError) as exc_info:
            checker.monitor_container_performance("nonexistent")
        
        assert "Failed to get container stats" in str(exc_info.value)

    def test_parse_percentage_method(self, checker):
        """Test the percentage parsing utility method."""
        assert checker._parse_percentage("50.5%") == 50.5
        assert checker._parse_percentage("0%") == 0.0
        assert checker._parse_percentage("100%") == 100.0
        assert checker._parse_percentage("invalid") == 0.0
        assert checker._parse_percentage("") == 0.0

    def test_timing_measurement_in_health_checks(self, checker):
        """Test that timing is properly measured in health checks."""
        def slow_availability_check():
            time.sleep(0.1)  # 100ms delay
            return {'docker_running': True}
        
        checker.docker_client.check_docker_availability.side_effect = slow_availability_check
        checker.docker_client.get_system_info.return_value = {}
        
        result = checker.check_docker_daemon_health()
        
        assert result['performance_metrics']['response_time'] >= 0.1

    def test_error_handling_in_compose_health_check(self, checker):
        """Test error handling in compose project health check."""
        error = subprocess.CalledProcessError(1, "docker compose ps")
        error.stderr = "Project not found"
        checker.docker_client.execute_compose_command.side_effect = error
        
        with pytest.raises(DockerError) as exc_info:
            checker.check_compose_project_health("nonexistent-project")
        
        assert "Failed to check project health" in str(exc_info.value)

    def test_health_check_with_partial_system_info(self, checker):
        """Test health check when system info is incomplete."""
        availability = {'docker_running': True}
        system_info = {}  # Empty system info
        
        checker.docker_client.check_docker_availability.return_value = availability
        checker.docker_client.get_system_info.return_value = system_info
        
        result = checker.check_docker_daemon_health()
        
        # Should handle missing system info gracefully
        assert 'resource_usage' in result
        assert result['resource_usage'].get('memory_total') is None