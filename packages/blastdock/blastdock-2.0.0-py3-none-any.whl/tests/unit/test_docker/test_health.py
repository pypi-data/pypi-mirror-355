"""
Test suite for Docker health monitoring
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from blastdock.docker.health import DockerHealthChecker
from blastdock.docker.errors import DockerError, ContainerError


class TestDockerHealthChecker:
    """Test cases for DockerHealthChecker class"""

    @patch('blastdock.docker.health.get_docker_client')
    def test_health_checker_initialization(self, mock_client):
        """Test DockerHealthChecker initialization"""
        checker = DockerHealthChecker()
        assert checker.docker_client is not None
        assert checker.logger is not None

    @patch('blastdock.docker.health.get_docker_client')
    def test_check_docker_daemon_health(self, mock_client):
        """Test checking Docker daemon health"""
        mock_docker = Mock()
        mock_docker.check_docker_availability.return_value = {
            'docker_installed': True,
            'docker_running': True,
            'docker_version': '20.10.0',
            'compose_installed': True,
            'compose_version': '2.0.0'
        }
        mock_client.return_value = mock_docker
        
        checker = DockerHealthChecker()
        result = checker.check_docker_daemon_health()
        
        assert result['healthy'] is True
        assert result['daemon_responsive'] is True
        assert 'performance_metrics' in result
        assert 'issues' in result
        assert 'recommendations' in result

    @patch('blastdock.docker.health.get_docker_client')
    def test_check_docker_daemon_health_not_running(self, mock_client):
        """Test checking Docker daemon when not running"""
        mock_docker = Mock()
        mock_docker.check_docker_availability.return_value = {
            'docker_installed': True,
            'docker_running': False,
            'docker_version': None,
            'compose_installed': True,
            'compose_version': None
        }
        mock_client.return_value = mock_docker
        
        checker = DockerHealthChecker()
        result = checker.check_docker_daemon_health()
        
        assert result['healthy'] is False
        assert result['daemon_responsive'] is False
        assert len(result['issues']) > 0
        assert 'Docker daemon not running' in result['issues'][0]

    @patch('blastdock.docker.health.get_docker_client')
    def test_check_container_health(self, mock_client):
        """Test checking container health"""
        mock_docker = Mock()
        mock_docker.execute_command.return_value = Mock(
            success=True,
            stdout='{"State":{"Status":"running","Health":{"Status":"healthy","FailingStreak":0,"Log":[{"ExitCode":0,"Output":"Health check passed"}]}}}'
        )
        mock_client.return_value = mock_docker
        
        checker = DockerHealthChecker()
        result = checker.check_container_health('abc123')
        
        assert result['healthy'] is True
        assert result['status'] == 'healthy'
        assert result['failing_streak'] == 0
        assert 'last_check' in result

    @patch('blastdock.docker.health.get_docker_client')
    def test_check_container_health_unhealthy(self, mock_client):
        """Test checking unhealthy container"""
        mock_docker = Mock()
        mock_docker.execute_command.return_value = Mock(
            success=True,
            stdout='{"State":{"Status":"running","Health":{"Status":"unhealthy","FailingStreak":3,"Log":[{"ExitCode":1,"Output":"Health check failed"}]}}}'
        )
        mock_client.return_value = mock_docker
        
        checker = DockerHealthChecker()
        result = checker.check_container_health('abc123')
        
        assert result['healthy'] is False
        assert result['status'] == 'unhealthy'
        assert result['failing_streak'] == 3

    @patch('blastdock.docker.health.get_docker_client')
    def test_check_container_health_no_healthcheck(self, mock_client):
        """Test checking container without health check"""
        mock_docker = Mock()
        mock_docker.execute_command.return_value = Mock(
            success=True,
            stdout='{"State":{"Status":"running"}}'
        )
        mock_client.return_value = mock_docker
        
        checker = DockerHealthChecker()
        result = checker.check_container_health('abc123')
        
        assert result['healthy'] is True  # Running containers without health check are considered healthy
        assert result['status'] == 'running'
        assert 'health_check_configured' in result
        assert result['health_check_configured'] is False

    @patch('blastdock.docker.health.get_docker_client')
    def test_check_container_health_not_found(self, mock_client):
        """Test checking non-existent container"""
        mock_docker = Mock()
        mock_docker.execute_command.return_value = Mock(
            success=False,
            stderr='Error: No such container: nonexistent'
        )
        mock_client.return_value = mock_docker
        
        checker = DockerHealthChecker()
        result = checker.check_container_health('nonexistent')
        
        assert result['healthy'] is False
        assert result['error'] is not None
        assert 'No such container' in result['error']

    @patch('blastdock.docker.health.get_docker_client')
    def test_wait_for_healthy_container(self, mock_client):
        """Test waiting for container to become healthy"""
        mock_docker = Mock()
        # First unhealthy, then healthy
        mock_docker.execute_command.side_effect = [
            Mock(success=True, stdout='{"State":{"Status":"running","Health":{"Status":"starting"}}}'),
            Mock(success=True, stdout='{"State":{"Status":"running","Health":{"Status":"starting"}}}'),
            Mock(success=True, stdout='{"State":{"Status":"running","Health":{"Status":"healthy"}}}')
        ]
        mock_client.return_value = mock_docker
        
        checker = DockerHealthChecker()
        result = checker.wait_for_healthy_container('abc123', timeout=30, check_interval=1)
        
        assert result['healthy'] is True
        assert result['status'] == 'healthy'
        assert result['time_elapsed'] > 0

    @patch('blastdock.docker.health.get_docker_client')
    def test_wait_for_healthy_container_timeout(self, mock_client):
        """Test waiting for container health with timeout"""
        mock_docker = Mock()
        mock_docker.execute_command.return_value = Mock(
            success=True,
            stdout='{"State":{"Status":"running","Health":{"Status":"unhealthy"}}}'
        )
        mock_client.return_value = mock_docker
        
        checker = DockerHealthChecker()
        result = checker.wait_for_healthy_container('abc123', timeout=2, check_interval=0.5)
        
        assert result['healthy'] is False
        assert result['timeout'] is True

    @patch('blastdock.docker.health.get_docker_client')
    def test_check_compose_health(self, mock_client):
        """Test checking compose project health"""
        mock_docker = Mock()
        # List containers response
        mock_docker.execute_command.side_effect = [
            Mock(
                success=True,
                stdout='{"ID":"abc123","Names":"/test-project_web_1","Labels":{"com.docker.compose.service":"web"},"State":"running"}\n{"ID":"def456","Names":"/test-project_db_1","Labels":{"com.docker.compose.service":"db"},"State":"running"}'
            ),
            # Health check for web container
            Mock(
                success=True,
                stdout='{"State":{"Status":"running","Health":{"Status":"healthy"}}}'
            ),
            # Health check for db container
            Mock(
                success=True,
                stdout='{"State":{"Status":"running"}}'
            )
        ]
        mock_client.return_value = mock_docker
        
        checker = DockerHealthChecker()
        result = checker.check_compose_health('test-project')
        
        assert result['overall_healthy'] is True
        assert result['total_containers'] == 2
        assert len(result['services']) == 2
        assert 'web' in result['services']
        assert 'db' in result['services']

    @patch('blastdock.docker.health.get_docker_client')
    def test_check_resources_health(self, mock_client):
        """Test checking resource usage health"""
        mock_docker = Mock()
        # Docker system df response
        mock_docker.execute_command.side_effect = [
            Mock(
                success=True,
                stdout=json.dumps({
                    "Images": [{"Size": 1073741824}],  # 1GB
                    "Containers": [{"SizeRw": 524288000}],  # 500MB
                    "Volumes": [{"Size": 2147483648}],  # 2GB
                    "BuildCache": [{"Size": 268435456}]  # 256MB
                })
            ),
            # Docker info response
            Mock(
                success=True,
                stdout=json.dumps({
                    "MemTotal": 8589934592,  # 8GB
                    "NCPU": 4,
                    "ContainersRunning": 2,
                    "ContainersStopped": 5,
                    "Images": 10
                })
            )
        ]
        mock_client.return_value = mock_docker
        
        checker = DockerHealthChecker()
        result = checker.check_resources_health()
        
        assert 'disk_usage' in result
        assert 'system_info' in result
        assert 'healthy' in result
        assert 'recommendations' in result

    @patch('blastdock.docker.health.get_docker_client')
    def test_perform_deep_health_check(self, mock_client):
        """Test performing deep health check"""
        mock_docker = Mock()
        # Mock all required responses
        mock_docker.check_docker_availability.return_value = {
            'docker_installed': True,
            'docker_running': True,
            'docker_version': '20.10.0',
            'compose_installed': True,
            'compose_version': '2.0.0'
        }
        mock_docker.execute_command.side_effect = [
            # System df
            Mock(success=True, stdout='{"Images":[{"Size":1073741824}],"Containers":[],"Volumes":[],"BuildCache":[]}'),
            # System info
            Mock(success=True, stdout='{"MemTotal":8589934592,"NCPU":4,"ContainersRunning":0,"ContainersStopped":0,"Images":1}'),
            # Network ls
            Mock(success=True, stdout='[{"Name":"bridge","Driver":"bridge"},{"Name":"host","Driver":"host"}]')
        ]
        mock_client.return_value = mock_docker
        
        checker = DockerHealthChecker()
        result = checker.perform_deep_health_check()
        
        assert 'daemon_health' in result
        assert 'resource_health' in result
        assert 'overall_status' in result
        assert 'summary' in result

    @patch('blastdock.docker.health.get_docker_client')
    def test_monitor_container_health(self, mock_client):
        """Test monitoring container health over time"""
        mock_docker = Mock()
        mock_docker.execute_command.return_value = Mock(
            success=True,
            stdout='{"State":{"Status":"running","Health":{"Status":"healthy"}}}'
        )
        mock_client.return_value = mock_docker
        
        checker = DockerHealthChecker()
        
        # Mock the monitoring to run only once
        with patch('time.sleep'):
            result = checker.monitor_container_health('abc123', duration=1, interval=1)
        
        assert 'container_id' in result
        assert 'checks_performed' in result
        assert result['checks_performed'] > 0
        assert 'health_history' in result

    @patch('blastdock.docker.health.get_docker_client')
    def test_get_container_health_logs(self, mock_client):
        """Test getting container health check logs"""
        mock_docker = Mock()
        health_data = {
            "State": {
                "Health": {
                    "Status": "healthy",
                    "Log": [
                        {
                            "Start": "2023-01-01T12:00:00Z",
                            "End": "2023-01-01T12:00:01Z",
                            "ExitCode": 0,
                            "Output": "Health check passed"
                        },
                        {
                            "Start": "2023-01-01T12:01:00Z",
                            "End": "2023-01-01T12:01:01Z",
                            "ExitCode": 0,
                            "Output": "Health check passed"
                        }
                    ]
                }
            }
        }
        mock_docker.execute_command.return_value = Mock(
            success=True,
            stdout=json.dumps(health_data)
        )
        mock_client.return_value = mock_docker
        
        checker = DockerHealthChecker()
        result = checker.get_container_health_logs('abc123', limit=5)
        
        assert 'logs' in result
        assert len(result['logs']) == 2
        assert result['logs'][0]['exit_code'] == 0
        assert 'Health check passed' in result['logs'][0]['output']