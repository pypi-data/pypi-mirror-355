"""Comprehensive tests for security docker_security module."""

import json
import subprocess
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
import pytest

from blastdock.security.docker_security import DockerSecurityChecker, get_docker_security_checker


class TestDockerSecurityChecker:
    """Test suite for DockerSecurityChecker."""

    @pytest.fixture
    def checker(self):
        """Create a DockerSecurityChecker instance."""
        return DockerSecurityChecker()

    @pytest.fixture
    def sample_container_inspect(self):
        """Sample container inspection data."""
        return {
            "Id": "abc123",
            "Name": "/test-container",
            "Config": {
                "User": "appuser",
                "ExposedPorts": {
                    "80/tcp": {},
                    "443/tcp": {}
                }
            },
            "HostConfig": {
                "Privileged": False,
                "NetworkMode": "bridge",
                "PidMode": "",
                "IpcMode": "",
                "ReadonlyRootfs": False,
                "CapAdd": [],
                "CapDrop": []
            },
            "Mounts": [
                {
                    "Type": "volume",
                    "Source": "app-data",
                    "Destination": "/data"
                }
            ]
        }

    @pytest.fixture
    def sample_image_inspect(self):
        """Sample image inspection data."""
        return {
            "Id": "sha256:def456",
            "RepoTags": ["nginx:1.21"],
            "Created": "2023-01-01T12:00:00Z",
            "Size": 500000000,
            "Config": {
                "ExposedPorts": {
                    "80/tcp": {}
                }
            }
        }

    @pytest.fixture
    def sample_docker_info(self):
        """Sample Docker daemon info."""
        return {
            "ServerVersion": "24.0.7",
            "Driver": "overlay2",
            "OSType": "linux",
            "ExperimentalBuild": False,
            "SecurityOptions": ["apparmor", "seccomp"],
            "RegistryConfig": {
                "InsecureRegistryCIDRs": []
            }
        }

    def test_init(self, checker):
        """Test DockerSecurityChecker initialization."""
        assert checker.logger is not None
        assert 'SYS_ADMIN' in checker.DANGEROUS_CAPABILITIES
        assert '/var/run/docker.sock' in checker.DANGEROUS_BIND_MOUNTS
        assert 'localhost' in checker.UNSAFE_REGISTRIES

    def test_check_container_security_success(self, checker, sample_container_inspect):
        """Test successful container security check."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([sample_container_inspect])
        
        with patch('subprocess.run', return_value=mock_result):
            result = checker.check_container_security('test-container')
        
        assert result['container'] == 'test-container'
        assert result['accessible'] is True
        assert 'security_score' in result
        assert 'security_issues' in result
        assert 'configuration' in result

    def test_check_container_security_privileged_container(self, checker, sample_container_inspect):
        """Test security check for privileged container."""
        sample_container_inspect['HostConfig']['Privileged'] = True
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([sample_container_inspect])
        
        with patch('subprocess.run', return_value=mock_result):
            result = checker.check_container_security('privileged-container')
        
        assert result['security_score'] <= 70  # Should lose 30 points
        assert any(issue['severity'] == 'critical' for issue in result['security_issues'])
        assert any('privileged mode' in issue['issue'].lower() for issue in result['security_issues'])

    def test_check_container_security_dangerous_capabilities(self, checker, sample_container_inspect):
        """Test security check for dangerous capabilities."""
        sample_container_inspect['HostConfig']['CapAdd'] = ['SYS_ADMIN', 'SYS_MODULE']
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([sample_container_inspect])
        
        with patch('subprocess.run', return_value=mock_result):
            result = checker.check_container_security('dangerous-caps-container')
        
        assert result['security_score'] <= 80  # Should lose 20 points
        assert any(issue['severity'] == 'high' for issue in result['security_issues'])
        assert any('capabilities' in issue['issue'].lower() for issue in result['security_issues'])

    def test_check_container_security_dangerous_bind_mounts(self, checker, sample_container_inspect):
        """Test security check for dangerous bind mounts."""
        sample_container_inspect['Mounts'] = [
            {
                "Type": "bind",
                "Source": "/var/run/docker.sock",
                "Destination": "/var/run/docker.sock"
            }
        ]
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([sample_container_inspect])
        
        with patch('subprocess.run', return_value=mock_result):
            result = checker.check_container_security('bind-mount-container')
        
        assert result['security_score'] <= 80  # Should lose 20 points
        assert any('bind mount' in issue['issue'].lower() for issue in result['security_issues'])

    def test_check_container_security_root_user(self, checker, sample_container_inspect):
        """Test security check for root user."""
        sample_container_inspect['Config']['User'] = 'root'
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([sample_container_inspect])
        
        with patch('subprocess.run', return_value=mock_result):
            result = checker.check_container_security('root-container')
        
        assert result['security_score'] <= 85  # Should lose 15 points
        assert any('root user' in issue['issue'].lower() for issue in result['security_issues'])

    def test_check_container_security_host_network(self, checker, sample_container_inspect):
        """Test security check for host network mode."""
        sample_container_inspect['HostConfig']['NetworkMode'] = 'host'
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([sample_container_inspect])
        
        with patch('subprocess.run', return_value=mock_result):
            result = checker.check_container_security('host-network-container')
        
        assert result['security_score'] <= 75  # Should lose 25 points
        assert any('host network' in issue['issue'].lower() for issue in result['security_issues'])

    def test_check_container_security_host_pid(self, checker, sample_container_inspect):
        """Test security check for host PID mode."""
        sample_container_inspect['HostConfig']['PidMode'] = 'host'
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([sample_container_inspect])
        
        with patch('subprocess.run', return_value=mock_result):
            result = checker.check_container_security('host-pid-container')
        
        assert result['security_score'] <= 75  # Should lose 25 points
        assert any('pid namespace' in issue['issue'].lower() for issue in result['security_issues'])

    def test_check_container_security_host_ipc(self, checker, sample_container_inspect):
        """Test security check for host IPC mode."""
        sample_container_inspect['HostConfig']['IpcMode'] = 'host'
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([sample_container_inspect])
        
        with patch('subprocess.run', return_value=mock_result):
            result = checker.check_container_security('host-ipc-container')
        
        assert result['security_score'] <= 90  # Should lose 10 points
        assert any('ipc namespace' in issue['issue'].lower() for issue in result['security_issues'])

    def test_check_container_security_writable_root_fs(self, checker, sample_container_inspect):
        """Test security check for writable root filesystem."""
        sample_container_inspect['HostConfig']['ReadonlyRootfs'] = False
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([sample_container_inspect])
        
        with patch('subprocess.run', return_value=mock_result):
            result = checker.check_container_security('writable-root-container')
        
        assert result['security_score'] <= 95  # Should lose 5 points
        assert any('writable' in issue['issue'].lower() for issue in result['security_issues'])

    def test_check_container_security_docker_command_failed(self, checker):
        """Test container security check when Docker command fails."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "No such container: nonexistent"
        
        with patch('subprocess.run', return_value=mock_result):
            result = checker.check_container_security('nonexistent')
        
        assert result['container'] == 'nonexistent'
        assert result['accessible'] is False
        assert 'error' in result

    def test_check_container_security_timeout(self, checker):
        """Test container security check with timeout."""
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired('docker', 30)):
            result = checker.check_container_security('timeout-container')
        
        assert result['accessible'] is False
        assert 'timed out' in result['error'].lower()

    def test_check_container_security_json_decode_error(self, checker):
        """Test container security check with JSON decode error."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "invalid json"
        
        with patch('subprocess.run', return_value=mock_result):
            result = checker.check_container_security('invalid-json-container')
        
        assert result['accessible'] is False
        assert 'parse' in result['error'].lower()

    def test_check_image_security_success(self, checker, sample_image_inspect):
        """Test successful image security check."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([sample_image_inspect])
        
        with patch('subprocess.run', return_value=mock_result):
            result = checker.check_image_security('nginx:1.21')
        
        assert result['image'] == 'nginx:1.21'
        assert result['accessible'] is True
        assert 'security_score' in result
        assert 'security_issues' in result
        assert 'metadata' in result

    def test_check_image_security_untrusted_registry(self, checker, sample_image_inspect):
        """Test image security check for untrusted registry."""
        sample_image_inspect['RepoTags'] = ['localhost/malicious:latest']
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([sample_image_inspect])
        
        with patch('subprocess.run', return_value=mock_result):
            result = checker.check_image_security('localhost/malicious:latest')
        
        assert result['security_score'] <= 70  # Should lose 30 points
        assert any('untrusted registry' in issue['issue'].lower() for issue in result['security_issues'])

    def test_check_image_security_old_image(self, checker, sample_image_inspect):
        """Test image security check for old image."""
        # Set image creation date to 2 years ago
        old_date = datetime.now(timezone.utc).replace(year=datetime.now().year - 2)
        sample_image_inspect['Created'] = old_date.isoformat().replace('+00:00', 'Z')
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([sample_image_inspect])
        
        with patch('subprocess.run', return_value=mock_result):
            result = checker.check_image_security('nginx:old')
        
        assert result['security_score'] <= 85  # Should lose 15 points
        assert any('days old' in issue['issue'] for issue in result['security_issues'])

    def test_check_image_security_latest_tag(self, checker, sample_image_inspect):
        """Test image security check for latest tag."""
        sample_image_inspect['RepoTags'] = ['nginx:latest']
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([sample_image_inspect])
        
        with patch('subprocess.run', return_value=mock_result):
            result = checker.check_image_security('nginx:latest')
        
        assert result['security_score'] <= 95  # Should lose 5 points
        assert any('latest tag' in issue['issue'].lower() for issue in result['security_issues'])

    def test_check_image_security_large_size(self, checker, sample_image_inspect):
        """Test image security check for large image size."""
        sample_image_inspect['Size'] = 2000000000  # 2GB
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([sample_image_inspect])
        
        with patch('subprocess.run', return_value=mock_result):
            result = checker.check_image_security('large-image:latest')
        
        assert result['security_score'] <= 95  # Should lose 5 points
        assert any('large image size' in issue['issue'].lower() for issue in result['security_issues'])

    def test_check_image_security_exposed_ports(self, checker, sample_image_inspect):
        """Test image security check with exposed ports."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([sample_image_inspect])
        
        with patch('subprocess.run', return_value=mock_result):
            result = checker.check_image_security('nginx:1.21')
        
        # Should have info about exposed ports
        assert any('exposed ports' in issue['issue'].lower() for issue in result['security_issues'])

    def test_check_image_security_docker_command_failed(self, checker):
        """Test image security check when Docker command fails."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "No such image: nonexistent"
        
        with patch('subprocess.run', return_value=mock_result):
            result = checker.check_image_security('nonexistent:latest')
        
        assert result['image'] == 'nonexistent:latest'
        assert result['accessible'] is False
        assert 'error' in result

    def test_check_docker_daemon_security_success(self, checker, sample_docker_info):
        """Test successful Docker daemon security check."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(sample_docker_info)
        
        with patch('subprocess.run', return_value=mock_result):
            result = checker.check_docker_daemon_security()
        
        assert result['accessible'] is True
        assert 'security_score' in result
        assert 'security_issues' in result
        assert 'daemon_info' in result

    def test_check_docker_daemon_security_root_daemon(self, checker, sample_docker_info):
        """Test Docker daemon security check for root daemon."""
        sample_docker_info['SecurityOptions'] = ['apparmor', 'seccomp']  # No rootless
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(sample_docker_info)
        
        with patch('subprocess.run', return_value=mock_result):
            result = checker.check_docker_daemon_security()
        
        assert result['security_score'] <= 90  # Should lose 10 points
        assert any('daemon running as root' in issue['issue'].lower() for issue in result['security_issues'])

    def test_check_docker_daemon_security_experimental(self, checker, sample_docker_info):
        """Test Docker daemon security check with experimental features."""
        sample_docker_info['ExperimentalBuild'] = True
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(sample_docker_info)
        
        with patch('subprocess.run', return_value=mock_result):
            result = checker.check_docker_daemon_security()
        
        assert result['security_score'] <= 95  # Should lose 5 points
        assert any('experimental' in issue['issue'].lower() for issue in result['security_issues'])

    def test_check_docker_daemon_security_insecure_storage_driver(self, checker, sample_docker_info):
        """Test Docker daemon security check with insecure storage driver."""
        sample_docker_info['Driver'] = 'devicemapper'
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(sample_docker_info)
        
        with patch('subprocess.run', return_value=mock_result):
            result = checker.check_docker_daemon_security()
        
        assert result['security_score'] <= 85  # Should lose 15 points
        assert any('storage driver' in issue['issue'].lower() for issue in result['security_issues'])

    def test_check_docker_daemon_security_insecure_registries(self, checker, sample_docker_info):
        """Test Docker daemon security check with insecure registries."""
        sample_docker_info['RegistryConfig'] = {
            'InsecureRegistryCIDRs': ['192.168.1.0/24']
        }
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(sample_docker_info)
        
        with patch('subprocess.run', return_value=mock_result):
            result = checker.check_docker_daemon_security()
        
        assert result['security_score'] <= 75  # Should lose 25 points
        assert any('insecure registries' in issue['issue'].lower() for issue in result['security_issues'])

    def test_check_docker_daemon_security_docker_command_failed(self, checker):
        """Test Docker daemon security check when command fails."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Cannot connect to Docker daemon"
        
        with patch('subprocess.run', return_value=mock_result):
            result = checker.check_docker_daemon_security()
        
        assert result['accessible'] is False
        assert 'error' in result

    def test_scan_docker_compose_security_valid_compose(self, checker):
        """Test scanning valid Docker Compose content."""
        compose_content = """
version: '3.8'
services:
  web:
    image: nginx:1.21
    user: nginx
    ports:
      - "80:80"
    volumes:
      - web-data:/data
  db:
    image: postgres:13
    user: postgres
    environment:
      POSTGRES_DB: myapp
volumes:
  web-data:
"""
        
        result = checker.scan_docker_compose_security(compose_content)
        
        assert result['valid'] is True
        assert 'security_score' in result
        assert 'security_issues' in result
        assert result['services_analyzed'] == 2

    def test_scan_docker_compose_security_privileged_service(self, checker):
        """Test scanning Docker Compose with privileged service."""
        compose_content = """
version: '3.8'
services:
  privileged-service:
    image: nginx
    privileged: true
"""
        
        result = checker.scan_docker_compose_security(compose_content)
        
        assert result['valid'] is True
        assert result['security_score'] <= 70  # Should lose 30 points
        assert any('privileged mode' in issue['issue'].lower() for issue in result['security_issues'])

    def test_scan_docker_compose_security_root_user(self, checker):
        """Test scanning Docker Compose with root user."""
        compose_content = """
version: '3.8'
services:
  root-service:
    image: nginx
    user: root
"""
        
        result = checker.scan_docker_compose_security(compose_content)
        
        assert result['valid'] is True
        assert result['security_score'] <= 85  # Should lose 15 points
        assert any('root user' in issue['issue'].lower() for issue in result['security_issues'])

    def test_scan_docker_compose_security_dangerous_bind_mount(self, checker):
        """Test scanning Docker Compose with dangerous bind mount."""
        compose_content = """
version: '3.8'
services:
  dangerous-mount:
    image: nginx
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
"""
        
        result = checker.scan_docker_compose_security(compose_content)
        
        assert result['valid'] is True
        assert result['security_score'] <= 80  # Should lose 20 points
        assert any('bind mount' in issue['issue'].lower() for issue in result['security_issues'])

    def test_scan_docker_compose_security_host_network(self, checker):
        """Test scanning Docker Compose with host network mode."""
        compose_content = """
version: '3.8'
services:
  host-network:
    image: nginx
    network_mode: host
"""
        
        result = checker.scan_docker_compose_security(compose_content)
        
        assert result['valid'] is True
        assert result['security_score'] <= 75  # Should lose 25 points
        assert any('host network' in issue['issue'].lower() for issue in result['security_issues'])

    def test_scan_docker_compose_security_dangerous_capabilities(self, checker):
        """Test scanning Docker Compose with dangerous capabilities."""
        compose_content = """
version: '3.8'
services:
  dangerous-caps:
    image: nginx
    cap_add:
      - SYS_ADMIN
      - SYS_MODULE
"""
        
        result = checker.scan_docker_compose_security(compose_content)
        
        assert result['valid'] is True
        assert result['security_score'] <= 80  # Should lose 20 points
        assert any('capabilities' in issue['issue'].lower() for issue in result['security_issues'])

    def test_scan_docker_compose_security_hardcoded_secrets_dict(self, checker):
        """Test scanning Docker Compose with hardcoded secrets in dict environment."""
        compose_content = """
version: '3.8'
services:
  secret-service:
    image: nginx
    environment:
      DATABASE_PASSWORD: mysecretpassword
      API_KEY: abcdef123456
"""
        
        result = checker.scan_docker_compose_security(compose_content)
        
        assert result['valid'] is True
        assert result['security_score'] <= 60  # Should lose 40 points (20 each)
        secret_issues = [issue for issue in result['security_issues'] if 'secret' in issue['issue'].lower()]
        assert len(secret_issues) == 2

    def test_scan_docker_compose_security_hardcoded_secrets_list(self, checker):
        """Test scanning Docker Compose with hardcoded secrets in list environment."""
        compose_content = """
version: '3.8'
services:
  secret-service:
    image: nginx
    environment:
      - DATABASE_PASSWORD=mysecretpassword
      - REGULAR_VAR=value
"""
        
        result = checker.scan_docker_compose_security(compose_content)
        
        assert result['valid'] is True
        assert result['security_score'] <= 80  # Should lose 20 points
        assert any('secret' in issue['issue'].lower() for issue in result['security_issues'])

    def test_scan_docker_compose_security_env_var_substitution(self, checker):
        """Test scanning Docker Compose with environment variable substitution (should be okay)."""
        compose_content = """
version: '3.8'
services:
  env-service:
    image: nginx
    environment:
      DATABASE_PASSWORD: ${DB_PASSWORD}
      API_KEY: ${API_KEY:-default}
"""
        
        result = checker.scan_docker_compose_security(compose_content)
        
        assert result['valid'] is True
        # Should not flag environment variable substitution as hardcoded secrets
        secret_issues = [issue for issue in result['security_issues'] if 'secret' in issue['issue'].lower()]
        assert len(secret_issues) == 0

    def test_scan_docker_compose_security_invalid_yaml(self, checker):
        """Test scanning invalid YAML content."""
        compose_content = """
invalid: yaml: content:
  - missing
    proper: structure
"""
        
        result = checker.scan_docker_compose_security(compose_content)
        
        assert result['valid'] is False
        assert 'error' in result

    def test_scan_docker_compose_security_not_dict(self, checker):
        """Test scanning YAML that's not a dictionary."""
        compose_content = """
- item1
- item2
"""
        
        result = checker.scan_docker_compose_security(compose_content)
        
        assert result['valid'] is False
        assert 'dictionary' in result['error']

    def test_scan_docker_compose_security_no_services(self, checker):
        """Test scanning Docker Compose without services."""
        compose_content = """
version: '3.8'
networks:
  default:
    driver: bridge
"""
        
        result = checker.scan_docker_compose_security(compose_content)
        
        assert result['valid'] is True
        assert result['services_analyzed'] == 0
        assert result['security_score'] == 100  # No services, no issues

    def test_get_security_recommendations(self, checker):
        """Test getting security recommendations."""
        recommendations = checker.get_security_recommendations()
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert any('official' in rec.lower() for rec in recommendations)
        assert any('root' in rec.lower() for rec in recommendations)
        assert any('privileged' in rec.lower() for rec in recommendations)

    def test_get_docker_security_checker_singleton(self):
        """Test the global Docker security checker singleton."""
        checker1 = get_docker_security_checker()
        checker2 = get_docker_security_checker()
        
        assert isinstance(checker1, DockerSecurityChecker)
        assert checker1 is checker2  # Should be the same instance

    def test_container_security_multiple_issues(self, checker, sample_container_inspect):
        """Test container with multiple security issues."""
        # Add multiple security issues
        sample_container_inspect['HostConfig']['Privileged'] = True
        sample_container_inspect['HostConfig']['NetworkMode'] = 'host'
        sample_container_inspect['Config']['User'] = 'root'
        sample_container_inspect['HostConfig']['CapAdd'] = ['SYS_ADMIN']
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([sample_container_inspect])
        
        with patch('subprocess.run', return_value=mock_result):
            result = checker.check_container_security('multiple-issues-container')
        
        # Should have multiple security issues and very low score
        assert len(result['security_issues']) >= 4
        assert result['security_score'] <= 30  # Multiple penalties

    def test_image_security_perfect_score(self, checker):
        """Test image with perfect security score."""
        perfect_image = {
            "Id": "sha256:perfect",
            "RepoTags": ["alpine:3.18.4"],  # Specific tag, not latest
            "Created": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),  # Recent
            "Size": 100000000,  # Small size < 1GB
            "Config": {
                "ExposedPorts": None
            }
        }
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([perfect_image])
        
        with patch('subprocess.run', return_value=mock_result):
            result = checker.check_image_security('alpine:3.18.4')
        
        assert result['security_score'] == 100
        # Should only have info-level issues or no issues
        critical_issues = [issue for issue in result['security_issues'] 
                         if issue['severity'] in ['critical', 'high', 'medium']]
        assert len(critical_issues) == 0