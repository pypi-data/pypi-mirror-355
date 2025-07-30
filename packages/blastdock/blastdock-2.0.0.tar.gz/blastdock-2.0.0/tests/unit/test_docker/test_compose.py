"""
Test suite for Docker Compose functionality
"""

import pytest
import os
import yaml
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path

from blastdock.docker.compose import ComposeManager
from blastdock.docker.errors import DockerComposeError


class TestComposeManager:
    """Test cases for ComposeManager class"""

    def test_init_default_values(self):
        """Test ComposeManager initialization with default values"""
        with patch('blastdock.docker.compose.get_docker_client'):
            manager = ComposeManager()
            assert manager.project_dir is None
            assert manager.project_name is None
            assert manager.docker_client is not None
            assert manager.logger is not None

    def test_init_with_parameters(self):
        """Test ComposeManager initialization with parameters"""
        with patch('blastdock.docker.compose.get_docker_client'):
            manager = ComposeManager(project_dir='/test/dir', project_name='test-project')
            assert manager.project_dir == '/test/dir'
            assert manager.project_name == 'test-project'

    @patch('os.path.isfile')
    def test_find_compose_file_found(self, mock_isfile):
        """Test finding compose file when it exists"""
        mock_isfile.side_effect = lambda path: path.endswith('docker-compose.yml')
        
        with patch('blastdock.docker.compose.get_docker_client'):
            manager = ComposeManager(project_dir='/test/dir')
            result = manager.find_compose_file()
            
            expected_path = '/test/dir/docker-compose.yml'
            assert result == expected_path

    @patch('os.path.isfile')
    def test_find_compose_file_not_found(self, mock_isfile):
        """Test finding compose file when none exist"""
        mock_isfile.return_value = False
        
        with patch('blastdock.docker.compose.get_docker_client'):
            manager = ComposeManager(project_dir='/test/dir')
            result = manager.find_compose_file()
            
            assert result is None

    @patch('blastdock.docker.compose.Path.exists')
    @patch('blastdock.docker.compose.open', new_callable=mock_open, read_data='version: "3.8"\nservices:\n  web:\n    image: nginx')
    def test_load_compose_file_success(self, mock_file, mock_exists):
        """Test successful compose file loading"""
        mock_exists.return_value = True
        
        with patch('blastdock.docker.compose.get_docker_client'):
            manager = ComposeManager(project_dir='/test/dir')
            result = manager.load_compose_file()
            
            assert result is not None
            assert 'version' in result
            assert 'services' in result
            assert result['version'] == '3.8'

    @patch('blastdock.docker.compose.Path.exists')
    def test_load_compose_file_not_found(self, mock_exists):
        """Test loading compose file when it doesn't exist"""
        mock_exists.return_value = False
        
        with patch('blastdock.docker.compose.get_docker_client'):
            manager = ComposeManager(project_dir='/test/dir')
            
            with pytest.raises(DockerComposeError):
                manager.load_compose_file()

    @patch('blastdock.docker.compose.Path.exists')
    @patch('blastdock.docker.compose.open', new_callable=mock_open, read_data='invalid: yaml: content')
    def test_load_compose_file_invalid_yaml(self, mock_file, mock_exists):
        """Test loading invalid YAML compose file"""
        mock_exists.return_value = True
        
        with patch('blastdock.docker.compose.get_docker_client'):
            manager = ComposeManager(project_dir='/test/dir')
            
            with pytest.raises(DockerComposeError):
                manager.load_compose_file()

    @patch('blastdock.docker.compose.subprocess.run')
    def test_up_success(self, mock_run):
        """Test successful compose up"""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Services started successfully",
            stderr=""
        )
        
        with patch('blastdock.docker.compose.get_docker_client'):
            manager = ComposeManager(project_dir='/test/dir', project_name='test-project')
            result = manager.up(detach=True)
            
            assert result['success'] is True
            assert 'Services started' in result['stdout']
            
            # Verify command structure
            args = mock_run.call_args[0][0]
            assert 'docker-compose' in args
            assert '-p' in args
            assert 'test-project' in args
            assert 'up' in args
            assert '-d' in args

    @patch('blastdock.docker.compose.subprocess.run')
    def test_up_with_services(self, mock_run):
        """Test compose up with specific services"""
        mock_run.return_value = Mock(returncode=0, stdout="Services started", stderr="")
        
        with patch('blastdock.docker.compose.get_docker_client'):
            manager = ComposeManager(project_dir='/test/dir')
            result = manager.up(services=['web', 'db'], build=True)
            
            assert result['success'] is True
            args = mock_run.call_args[0][0]
            assert 'up' in args
            assert '--build' in args
            assert 'web' in args
            assert 'db' in args

    @patch('blastdock.docker.compose.subprocess.run')
    def test_down_success(self, mock_run):
        """Test successful compose down"""
        mock_run.return_value = Mock(returncode=0, stdout="Services stopped", stderr="")
        
        with patch('blastdock.docker.compose.get_docker_client'):
            manager = ComposeManager(project_dir='/test/dir')
            result = manager.down(remove_volumes=True, remove_images='all')
            
            assert result['success'] is True
            args = mock_run.call_args[0][0]
            assert 'down' in args
            assert '-v' in args
            assert '--rmi' in args
            assert 'all' in args

    @patch('blastdock.docker.compose.subprocess.run')
    def test_build_success(self, mock_run):
        """Test successful compose build"""
        mock_run.return_value = Mock(returncode=0, stdout="Build completed", stderr="")
        
        with patch('blastdock.docker.compose.get_docker_client'):
            manager = ComposeManager(project_dir='/test/dir')
            result = manager.build(services=['web'], no_cache=True, parallel=True)
            
            assert result['success'] is True
            args = mock_run.call_args[0][0]
            assert 'build' in args
            assert '--no-cache' in args
            assert '--parallel' in args
            assert 'web' in args

    @patch('blastdock.docker.compose.subprocess.run')
    def test_pull_success(self, mock_run):
        """Test successful compose pull"""
        mock_run.return_value = Mock(returncode=0, stdout="Images pulled", stderr="")
        
        with patch('blastdock.docker.compose.get_docker_client'):
            manager = ComposeManager(project_dir='/test/dir')
            result = manager.pull(services=['web'], parallel=True)
            
            assert result['success'] is True
            args = mock_run.call_args[0][0]
            assert 'pull' in args
            assert '--parallel' in args
            assert 'web' in args

    @patch('blastdock.docker.compose.subprocess.run')
    def test_ps_success(self, mock_run):
        """Test successful compose ps"""
        mock_output = "Name        Command       State    Ports\n" \
                     "web_1       nginx         Up       80/tcp"
        mock_run.return_value = Mock(returncode=0, stdout=mock_output, stderr="")
        
        with patch('blastdock.docker.compose.get_docker_client'):
            manager = ComposeManager(project_dir='/test/dir')
            result = manager.ps(services=['web'], all=True)
            
            assert result['success'] is True
            assert 'web_1' in result['stdout']
            args = mock_run.call_args[0][0]
            assert 'ps' in args
            assert '-a' in args
            assert 'web' in args

    @patch('blastdock.docker.compose.subprocess.run')
    def test_logs_success(self, mock_run):
        """Test successful compose logs"""
        mock_logs = "web_1  | Starting nginx\nweb_1  | Ready to accept connections"
        mock_run.return_value = Mock(returncode=0, stdout=mock_logs, stderr="")
        
        with patch('blastdock.docker.compose.get_docker_client'):
            manager = ComposeManager(project_dir='/test/dir')
            result = manager.logs(services=['web'], follow=True, tail=100)
            
            assert result['success'] is True
            assert 'Starting nginx' in result['stdout']
            args = mock_run.call_args[0][0]
            assert 'logs' in args
            assert '--follow' in args
            assert '--tail' in args
            assert '100' in args
            assert 'web' in args

    @patch('blastdock.docker.compose.subprocess.run')
    def test_exec_success(self, mock_run):
        """Test successful compose exec"""
        mock_run.return_value = Mock(returncode=0, stdout="Command output", stderr="")
        
        with patch('blastdock.docker.compose.get_docker_client'):
            manager = ComposeManager(project_dir='/test/dir')
            result = manager.exec('web', ['ls', '-la'], interactive=True, tty=True)
            
            assert result['success'] is True
            args = mock_run.call_args[0][0]
            assert 'exec' in args
            assert '-it' in args
            assert 'web' in args
            assert 'ls' in args
            assert '-la' in args

    @patch('blastdock.docker.compose.subprocess.run')
    def test_run_success(self, mock_run):
        """Test successful compose run"""
        mock_run.return_value = Mock(returncode=0, stdout="Command output", stderr="")
        
        with patch('blastdock.docker.compose.get_docker_client'):
            manager = ComposeManager(project_dir='/test/dir')
            result = manager.run(
                'web', 
                ['python', 'manage.py', 'migrate'], 
                remove=True,
                environment={'DEBUG': 'true'}
            )
            
            assert result['success'] is True
            args = mock_run.call_args[0][0]
            assert 'run' in args
            assert '--rm' in args
            assert '-e' in args
            assert 'DEBUG=true' in args
            assert 'web' in args
            assert 'python' in args

    @patch('blastdock.docker.compose.subprocess.run')
    def test_stop_success(self, mock_run):
        """Test successful compose stop"""
        mock_run.return_value = Mock(returncode=0, stdout="Services stopped", stderr="")
        
        with patch('blastdock.docker.compose.get_docker_client'):
            manager = ComposeManager(project_dir='/test/dir')
            result = manager.stop(services=['web'], timeout=30)
            
            assert result['success'] is True
            args = mock_run.call_args[0][0]
            assert 'stop' in args
            assert '-t' in args
            assert '30' in args
            assert 'web' in args

    @patch('blastdock.docker.compose.subprocess.run')
    def test_restart_success(self, mock_run):
        """Test successful compose restart"""
        mock_run.return_value = Mock(returncode=0, stdout="Services restarted", stderr="")
        
        with patch('blastdock.docker.compose.get_docker_client'):
            manager = ComposeManager(project_dir='/test/dir')
            result = manager.restart(services=['web'], timeout=30)
            
            assert result['success'] is True
            args = mock_run.call_args[0][0]
            assert 'restart' in args
            assert '-t' in args
            assert '30' in args
            assert 'web' in args

    @patch('blastdock.docker.compose.subprocess.run')
    def test_scale_success(self, mock_run):
        """Test successful compose scale"""
        mock_run.return_value = Mock(returncode=0, stdout="Scaled services", stderr="")
        
        with patch('blastdock.docker.compose.get_docker_client'):
            manager = ComposeManager(project_dir='/test/dir')
            result = manager.scale({'web': 3, 'worker': 2})
            
            assert result['success'] is True
            args = mock_run.call_args[0][0]
            assert 'up' in args
            assert '--scale' in args
            assert 'web=3' in args
            assert 'worker=2' in args

    @patch('blastdock.docker.compose.subprocess.run')  
    def test_config_success(self, mock_run):
        """Test successful compose config"""
        mock_config = "version: '3.8'\nservices:\n  web:\n    image: nginx"
        mock_run.return_value = Mock(returncode=0, stdout=mock_config, stderr="")
        
        with patch('blastdock.docker.compose.get_docker_client'):
            manager = ComposeManager(project_dir='/test/dir')
            result = manager.config(quiet=True, resolve_image_digests=True)
            
            assert result['success'] is True
            assert 'version' in result['stdout']
            args = mock_run.call_args[0][0]
            assert 'config' in args
            assert '--quiet' in args
            assert '--resolve-image-digests' in args

    @patch('blastdock.docker.compose.subprocess.run')
    def test_validate_success(self, mock_run):
        """Test successful compose file validation"""
        mock_run.return_value = Mock(returncode=0, stdout="Configuration is valid", stderr="")
        
        with patch('blastdock.docker.compose.get_docker_client'):
            manager = ComposeManager(project_dir='/test/dir')
            result = manager.validate()
            
            assert result['success'] is True
            assert result['valid'] is True

    @patch('blastdock.docker.compose.subprocess.run')
    def test_validate_failure(self, mock_run):
        """Test compose file validation failure"""
        mock_run.return_value = Mock(
            returncode=1, 
            stdout="", 
            stderr="ERROR: Invalid service configuration"
        )
        
        with patch('blastdock.docker.compose.get_docker_client'):
            manager = ComposeManager(project_dir='/test/dir')
            result = manager.validate()
            
            assert result['success'] is False
            assert result['valid'] is False
            assert 'Invalid service' in result['stderr']

    @patch('blastdock.docker.compose.subprocess.run')
    def test_top_success(self, mock_run):
        """Test successful compose top"""
        mock_output = "web_1:\nPID   USER   COMMAND\n1234  root   nginx"
        mock_run.return_value = Mock(returncode=0, stdout=mock_output, stderr="")
        
        with patch('blastdock.docker.compose.get_docker_client'):
            manager = ComposeManager(project_dir='/test/dir')
            result = manager.top()
            
            assert result['success'] is True
            assert 'nginx' in result['stdout']
            args = mock_run.call_args[0][0]
            assert 'top' in args

    @patch('blastdock.docker.compose.subprocess.run')
    def test_port_success(self, mock_run):
        """Test successful compose port"""
        mock_run.return_value = Mock(returncode=0, stdout="0.0.0.0:8080", stderr="")
        
        with patch('blastdock.docker.compose.get_docker_client'):
            manager = ComposeManager(project_dir='/test/dir')
            result = manager.port('web', 80, protocol='tcp')
            
            assert result['success'] is True
            assert '8080' in result['stdout']
            args = mock_run.call_args[0][0]
            assert 'port' in args
            assert 'web' in args
            assert '80/tcp' in args

    @patch('blastdock.docker.compose.subprocess.run')
    def test_pause_success(self, mock_run):
        """Test successful compose pause"""
        mock_run.return_value = Mock(returncode=0, stdout="Services paused", stderr="")
        
        with patch('blastdock.docker.compose.get_docker_client'):
            manager = ComposeManager(project_dir='/test/dir')
            result = manager.pause(services=['web'])
            
            assert result['success'] is True
            args = mock_run.call_args[0][0]
            assert 'pause' in args
            assert 'web' in args

    @patch('blastdock.docker.compose.subprocess.run')
    def test_unpause_success(self, mock_run):
        """Test successful compose unpause"""
        mock_run.return_value = Mock(returncode=0, stdout="Services unpaused", stderr="")
        
        with patch('blastdock.docker.compose.get_docker_client'):
            manager = ComposeManager(project_dir='/test/dir')
            result = manager.unpause(services=['web'])
            
            assert result['success'] is True
            args = mock_run.call_args[0][0]
            assert 'unpause' in args
            assert 'web' in args

    @patch('blastdock.docker.compose.subprocess.run')
    def test_kill_success(self, mock_run):
        """Test successful compose kill"""
        mock_run.return_value = Mock(returncode=0, stdout="Services killed", stderr="")
        
        with patch('blastdock.docker.compose.get_docker_client'):
            manager = ComposeManager(project_dir='/test/dir')
            result = manager.kill(services=['web'], signal='SIGTERM')
            
            assert result['success'] is True
            args = mock_run.call_args[0][0]
            assert 'kill' in args
            assert '-s' in args
            assert 'SIGTERM' in args
            assert 'web' in args

    @patch('blastdock.docker.compose.subprocess.run')
    def test_command_failure(self, mock_run):
        """Test compose command failure handling"""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="Error: Service not found"
        )
        
        with patch('blastdock.docker.compose.get_docker_client'):
            manager = ComposeManager(project_dir='/test/dir')
            result = manager.up()
            
            assert result['success'] is False
            assert 'Service not found' in result['stderr']

    @patch('blastdock.docker.compose.subprocess.run')
    def test_timeout_handling(self, mock_run):
        """Test timeout handling"""
        mock_run.side_effect = subprocess.TimeoutExpired(['docker-compose', 'up'], 30)
        
        with patch('blastdock.docker.compose.get_docker_client'):
            manager = ComposeManager(project_dir='/test/dir')
            
            with pytest.raises(DockerComposeError):
                manager.up(timeout=30)

    def test_get_compose_command_base(self):
        """Test base compose command generation"""
        with patch('blastdock.docker.compose.get_docker_client'):
            manager = ComposeManager(project_dir='/test/dir', project_name='test-project')
            cmd = manager._get_compose_command(['up'])
            
            assert 'docker-compose' in cmd
            assert '-p' in cmd
            assert 'test-project' in cmd
            assert 'up' in cmd

    def test_get_compose_command_with_file(self):
        """Test compose command with custom file"""
        with patch('blastdock.docker.compose.get_docker_client'):
            manager = ComposeManager(project_dir='/test/dir')
            cmd = manager._get_compose_command(['up'], compose_file='/custom/docker-compose.yml')
            
            assert '-f' in cmd
            assert '/custom/docker-compose.yml' in cmd

    def test_environment_variable_handling(self):
        """Test environment variable handling"""
        with patch('blastdock.docker.compose.get_docker_client'):
            manager = ComposeManager(project_dir='/test/dir')
            
            # Test environment variable substitution
            with patch.dict(os.environ, {'TEST_VAR': 'test_value'}):
                env_vars = manager._resolve_environment_variables({'VAR': '${TEST_VAR}'})
                assert env_vars['VAR'] == 'test_value'

    def test_service_health_check(self):
        """Test service health checking"""
        with patch('blastdock.docker.compose.get_docker_client'):
            with patch('blastdock.docker.compose.subprocess.run') as mock_run:
                mock_run.return_value = Mock(
                    returncode=0,
                    stdout='web_1   Up   healthy',
                    stderr=""
                )
                
                manager = ComposeManager(project_dir='/test/dir')
                health = manager.check_service_health('web')
                
                assert health['healthy'] is True

    def test_context_manager(self):
        """Test ComposeManager as context manager"""
        with patch('blastdock.docker.compose.get_docker_client'):
            with ComposeManager(project_dir='/test/dir') as manager:
                assert manager.project_dir == '/test/dir'
                
            # Verify cleanup operations would happen here


class TestComposeService:
    """Test cases for ComposeService class"""

    def test_service_initialization(self):
        """Test service object initialization"""
        service_config = {
            'image': 'nginx:latest',
            'ports': ['80:8080'],
            'environment': {'ENV_VAR': 'value'}
        }
        
        service = ComposeService('web', service_config)
        assert service.name == 'web'
        assert service.config == service_config
        assert service.image == 'nginx:latest'

    def test_service_validation(self):
        """Test service configuration validation"""
        valid_config = {
            'image': 'nginx:latest',
            'ports': ['80:8080']
        }
        
        service = ComposeService('web', valid_config)
        assert service.validate() is True

    def test_service_validation_failure(self):
        """Test service validation with invalid config"""
        invalid_config = {}  # Missing required image
        
        service = ComposeService('web', invalid_config)
        assert service.validate() is False

    def test_service_ports_parsing(self):
        """Test port configuration parsing"""
        config = {
            'image': 'nginx',
            'ports': ['80:8080', '443:8443']
        }
        
        service = ComposeService('web', config)
        ports = service.get_ports()
        assert len(ports) == 2
        assert {'host': '8080', 'container': '80'} in ports

    def test_service_volumes_parsing(self):
        """Test volume configuration parsing"""
        config = {
            'image': 'nginx',
            'volumes': ['/host/path:/container/path', 'named_volume:/data']
        }
        
        service = ComposeService('web', config)
        volumes = service.get_volumes()
        assert len(volumes) == 2
        assert any(v['host'] == '/host/path' for v in volumes)

    def test_service_environment_parsing(self):
        """Test environment variable parsing"""
        config = {
            'image': 'nginx',
            'environment': {
                'VAR1': 'value1',
                'VAR2': 'value2'
            }
        }
        
        service = ComposeService('web', config)
        env = service.get_environment()
        assert env['VAR1'] == 'value1'
        assert env['VAR2'] == 'value2'

    def test_service_dependencies(self):
        """Test service dependency parsing"""
        config = {
            'image': 'web-app',
            'depends_on': ['db', 'redis']
        }
        
        service = ComposeService('web', config)
        deps = service.get_dependencies()
        assert 'db' in deps
        assert 'redis' in deps

    def test_service_networks(self):
        """Test service network configuration"""
        config = {
            'image': 'nginx',
            'networks': ['frontend', 'backend']
        }
        
        service = ComposeService('web', config)
        networks = service.get_networks()
        assert 'frontend' in networks
        assert 'backend' in networks


class TestComposeValidator:
    """Test cases for ComposeValidator class"""

    def test_validate_version(self):
        """Test compose file version validation"""
        validator = ComposeValidator()
        
        assert validator.validate_version('3.8') is True
        assert validator.validate_version('2.4') is True
        assert validator.validate_version('1.0') is False

    def test_validate_services(self):
        """Test services section validation"""
        services = {
            'web': {'image': 'nginx:latest'},
            'db': {'image': 'postgres:13'}
        }
        
        validator = ComposeValidator()
        result = validator.validate_services(services)
        assert result['valid'] is True
        assert len(result['errors']) == 0

    def test_validate_services_invalid(self):
        """Test services validation with invalid config"""
        services = {
            'web': {},  # Missing image
            'db': {'image': 'postgres:13'}
        }
        
        validator = ComposeValidator()
        result = validator.validate_services(services)
        assert result['valid'] is False
        assert len(result['errors']) > 0

    def test_validate_networks(self):
        """Test networks section validation"""
        networks = {
            'frontend': {'driver': 'bridge'},
            'backend': {'external': True}
        }
        
        validator = ComposeValidator()
        result = validator.validate_networks(networks)
        assert result['valid'] is True

    def test_validate_volumes(self):
        """Test volumes section validation"""
        volumes = {
            'db_data': {'driver': 'local'},
            'app_data': {}
        }
        
        validator = ComposeValidator()
        result = validator.validate_volumes(volumes)
        assert result['valid'] is True

    def test_validate_full_compose_file(self):
        """Test full compose file validation"""
        compose_data = {
            'version': '3.8',
            'services': {
                'web': {
                    'image': 'nginx:latest',
                    'ports': ['80:8080']
                }
            }
        }
        
        validator = ComposeValidator()
        result = validator.validate(compose_data)
        assert result['valid'] is True
        assert len(result['errors']) == 0

    def test_validate_compose_file_with_errors(self):
        """Test compose file validation with errors"""
        compose_data = {
            'version': '1.0',  # Invalid version
            'services': {
                'web': {}  # Missing image
            }
        }
        
        validator = ComposeValidator()
        result = validator.validate(compose_data)
        assert result['valid'] is False
        assert len(result['errors']) > 0

    def test_validate_security_settings(self):
        """Test security-related validation"""
        services = {
            'web': {
                'image': 'nginx:latest',
                'privileged': True,  # Security concern
                'user': 'root'  # Security concern
            }
        }
        
        validator = ComposeValidator()
        result = validator.validate_security(services)
        assert len(result['warnings']) > 0

    def test_validate_resource_limits(self):
        """Test resource limits validation"""
        services = {
            'web': {
                'image': 'nginx:latest',
                'deploy': {
                    'resources': {
                        'limits': {
                            'memory': '512M',
                            'cpus': '0.5'
                        }
                    }
                }
            }
        }
        
        validator = ComposeValidator()
        result = validator.validate_resources(services)
        assert result['valid'] is True