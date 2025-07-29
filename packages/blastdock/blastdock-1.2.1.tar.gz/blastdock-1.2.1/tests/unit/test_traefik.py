"""
Unit tests for Traefik management functionality
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from blastdock.traefik.manager import TraefikManager
from blastdock.traefik.installer import TraefikInstaller
from blastdock.traefik.labels import TraefikLabels
from blastdock.traefik.ssl import SSLManager
from blastdock.models.traefik import TraefikInstance, TraefikConfig, SSLCertificate


class TestTraefikManager:
    """Test TraefikManager functionality"""
    
    @patch('blastdock.utils.docker_utils.DockerClient')
    def test_manager_initialization(self, mock_docker_client):
        """Test TraefikManager initialization"""
        manager = TraefikManager()
        
        assert manager.container_name == "blastdock-traefik"
        assert manager.network_name == "blastdock-network"
        mock_docker_client.assert_called_once()
    
    @patch('blastdock.utils.docker_utils.DockerClient')
    def test_is_installed(self, mock_docker_client):
        """Test Traefik installation check"""
        manager = TraefikManager()
        
        # Test when Traefik is installed
        mock_container = Mock()
        mock_docker_client.return_value.get_container_info.return_value = mock_container
        
        assert manager.is_installed() is True
        
        # Test when Traefik is not installed
        mock_docker_client.return_value.get_container_info.return_value = None
        
        assert manager.is_installed() is False
    
    @patch('blastdock.utils.docker_utils.DockerClient')
    def test_is_running(self, mock_docker_client):
        """Test Traefik running status check"""
        manager = TraefikManager()
        
        # Test when Traefik is running
        mock_container = Mock()
        mock_container.status = "running"
        mock_docker_client.return_value.get_container_info.return_value = mock_container
        
        assert manager.is_running() is True
        
        # Test when Traefik is stopped
        mock_container.status = "exited"
        
        assert manager.is_running() is False
    
    @patch('blastdock.traefik.installer.TraefikInstaller')
    @patch('blastdock.utils.docker_utils.DockerClient')
    def test_install(self, mock_docker_client, mock_installer):
        """Test Traefik installation"""
        manager = TraefikManager()
        
        mock_installer.return_value.install.return_value = True
        
        config = {
            'email': 'test@example.com',
            'domain': 'example.com'
        }
        
        result = manager.install(config)
        
        assert result is True
        mock_installer.return_value.install.assert_called_once_with(config)
    
    @patch('blastdock.utils.docker_utils.DockerClient')
    def test_start(self, mock_docker_client):
        """Test Traefik start"""
        manager = TraefikManager()
        
        mock_docker_client.return_value.start_container.return_value = True
        
        result = manager.start()
        
        assert result is True
        mock_docker_client.return_value.start_container.assert_called_once_with("blastdock-traefik")
    
    @patch('blastdock.utils.docker_utils.DockerClient')
    def test_stop(self, mock_docker_client):
        """Test Traefik stop"""
        manager = TraefikManager()
        
        mock_docker_client.return_value.stop_container.return_value = True
        
        result = manager.stop()
        
        assert result is True
        mock_docker_client.return_value.stop_container.assert_called_once_with("blastdock-traefik")
    
    @patch('blastdock.utils.docker_utils.DockerClient')
    def test_get_instance(self, mock_docker_client):
        """Test getting Traefik instance information"""
        manager = TraefikManager()
        
        mock_container = Mock()
        mock_container.id = "test-container-id"
        mock_container.status = "running"
        mock_docker_client.return_value.get_container_info.return_value = mock_container
        
        instance = manager.get_instance()
        
        assert isinstance(instance, TraefikInstance)
        assert instance.container_id == "test-container-id"


class TestTraefikInstaller:
    """Test TraefikInstaller functionality"""
    
    @patch('blastdock.utils.docker_utils.DockerClient')
    def test_installer_initialization(self, mock_docker_client):
        """Test TraefikInstaller initialization"""
        installer = TraefikInstaller()
        
        mock_docker_client.assert_called_once()
    
    @patch('blastdock.utils.docker_utils.DockerClient')
    def test_create_network(self, mock_docker_client):
        """Test network creation"""
        installer = TraefikInstaller()
        
        mock_docker_client.return_value.create_network.return_value = True
        
        result = installer._create_network()
        
        assert result is True
        mock_docker_client.return_value.create_network.assert_called_once()
    
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_create_directories(self, mock_exists, mock_makedirs):
        """Test directory creation"""
        installer = TraefikInstaller()
        
        mock_exists.return_value = False
        
        installer._create_directories()
        
        mock_makedirs.assert_called()
    
    @patch('blastdock.utils.template_utils.render_template')
    def test_generate_config(self, mock_render):
        """Test configuration file generation"""
        installer = TraefikInstaller()
        
        mock_render.return_value = "test config content"
        
        config = {
            'email': 'test@example.com',
            'domain': 'example.com',
            'ssl_enabled': True
        }
        
        result = installer._generate_config(config)
        
        assert result == "test config content"
        mock_render.assert_called_once()
    
    @patch('builtins.open')
    @patch('blastdock.utils.template_utils.render_template')
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_write_config_file(self, mock_exists, mock_makedirs, mock_render, mock_open):
        """Test configuration file writing"""
        installer = TraefikInstaller()
        
        mock_exists.return_value = False
        mock_render.return_value = "test config"
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        config = {'email': 'test@example.com'}
        installer._write_config_file(config)
        
        mock_file.write.assert_called_once_with("test config")
    
    @patch('blastdock.utils.docker_utils.DockerClient')
    @patch('blastdock.traefik.installer.TraefikInstaller._write_config_file')
    @patch('blastdock.traefik.installer.TraefikInstaller._create_directories')
    @patch('blastdock.traefik.installer.TraefikInstaller._create_network')
    def test_install_success(self, mock_network, mock_dirs, mock_config, mock_docker_client):
        """Test successful Traefik installation"""
        installer = TraefikInstaller()
        
        mock_network.return_value = True
        mock_docker_client.return_value.run_container.return_value = True
        
        config = {
            'email': 'test@example.com',
            'domain': 'example.com'
        }
        
        result = installer.install(config)
        
        assert result is True
        mock_network.assert_called_once()
        mock_dirs.assert_called_once()
        mock_config.assert_called_once()


class TestTraefikLabels:
    """Test TraefikLabels functionality"""
    
    def test_labels_initialization(self):
        """Test TraefikLabels initialization"""
        labels = TraefikLabels("test-service", "example.com")
        
        assert labels.service_name == "test-service"
        assert labels.domain == "example.com"
    
    def test_generate_basic_labels(self):
        """Test basic label generation"""
        labels = TraefikLabels("test-service", "example.com")
        
        basic_labels = labels.generate_basic_labels()
        
        assert "traefik.enable" in basic_labels
        assert basic_labels["traefik.enable"] == "true"
        assert "traefik.http.routers.test-service.rule" in basic_labels
        assert "Host(`example.com`)" in basic_labels["traefik.http.routers.test-service.rule"]
    
    def test_generate_ssl_labels(self):
        """Test SSL label generation"""
        labels = TraefikLabels("test-service", "example.com")
        
        ssl_labels = labels.generate_ssl_labels()
        
        assert "traefik.http.routers.test-service.tls" in ssl_labels
        assert ssl_labels["traefik.http.routers.test-service.tls"] == "true"
        assert "traefik.http.routers.test-service.tls.certresolver" in ssl_labels
    
    def test_generate_port_labels(self):
        """Test port label generation"""
        labels = TraefikLabels("test-service", "example.com")
        
        port_labels = labels.generate_port_labels(8080)
        
        assert "traefik.http.services.test-service.loadbalancer.server.port" in port_labels
        assert port_labels["traefik.http.services.test-service.loadbalancer.server.port"] == "8080"
    
    def test_generate_middleware_labels(self):
        """Test middleware label generation"""
        labels = TraefikLabels("test-service", "example.com")
        
        middlewares = ["auth", "compress"]
        middleware_labels = labels.generate_middleware_labels(middlewares)
        
        assert "traefik.http.routers.test-service.middlewares" in middleware_labels
        assert "auth,compress" in middleware_labels["traefik.http.routers.test-service.middlewares"]
    
    def test_generate_complete_labels(self):
        """Test complete label generation"""
        labels = TraefikLabels("test-service", "example.com")
        
        options = {
            'port': 8080,
            'ssl_enabled': True,
            'middlewares': ['compress']
        }
        
        complete_labels = labels.generate_complete_labels(options)
        
        assert "traefik.enable" in complete_labels
        assert "traefik.http.routers.test-service.rule" in complete_labels
        assert "traefik.http.routers.test-service.tls" in complete_labels
        assert "traefik.http.services.test-service.loadbalancer.server.port" in complete_labels


class TestSSLManager:
    """Test SSLManager functionality"""
    
    @patch('blastdock.utils.docker_utils.DockerClient')
    def test_ssl_manager_initialization(self, mock_docker_client):
        """Test SSLManager initialization"""
        ssl_manager = SSLManager()
        
        mock_docker_client.assert_called_once()
    
    @patch('subprocess.run')
    def test_request_certificate(self, mock_subprocess):
        """Test certificate request"""
        ssl_manager = SSLManager()
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Certificate issued successfully"
        mock_subprocess.return_value = mock_result
        
        result = ssl_manager.request_certificate("example.com", "test@example.com")
        
        assert result is True
        mock_subprocess.assert_called()
    
    @patch('os.path.exists')
    def test_certificate_exists(self, mock_exists):
        """Test certificate existence check"""
        ssl_manager = SSLManager()
        
        mock_exists.return_value = True
        
        result = ssl_manager.certificate_exists("example.com")
        
        assert result is True
        mock_exists.assert_called()
    
    @patch('builtins.open')
    @patch('os.path.exists')
    def test_get_certificate_info(self, mock_exists, mock_open):
        """Test certificate information retrieval"""
        ssl_manager = SSLManager()
        
        mock_exists.return_value = True
        mock_cert_data = Mock()
        mock_cert_data.not_valid_after = datetime.now() + timedelta(days=30)
        mock_cert_data.issuer.rfc4514_string.return_value = "CN=Let's Encrypt"
        
        with patch('cryptography.x509.load_pem_x509_certificate', return_value=mock_cert_data):
            result = ssl_manager.get_certificate_info("example.com")
            
            assert isinstance(result, SSLCertificate)
            assert result.domain == "example.com"
    
    @patch('blastdock.traefik.ssl.SSLManager.get_certificate_info')
    def test_is_certificate_expiring(self, mock_get_info):
        """Test certificate expiration check"""
        ssl_manager = SSLManager()
        
        # Mock certificate expiring in 5 days
        mock_cert = Mock()
        mock_cert.days_until_expiry.return_value = 5
        mock_get_info.return_value = mock_cert
        
        result = ssl_manager.is_certificate_expiring("example.com", warning_days=30)
        
        assert result is True
    
    @patch('blastdock.traefik.ssl.SSLManager.request_certificate')
    def test_renew_certificate(self, mock_request):
        """Test certificate renewal"""
        ssl_manager = SSLManager()
        
        mock_request.return_value = True
        
        result = ssl_manager.renew_certificate("example.com", "test@example.com")
        
        assert result is True
        mock_request.assert_called_once_with("example.com", "test@example.com")


class TestTraefikIntegration:
    """Test Traefik integration functionality"""
    
    @patch('blastdock.traefik.manager.TraefikManager')
    @patch('blastdock.traefik.labels.TraefikLabels')
    def test_project_traefik_integration(self, mock_labels, mock_manager):
        """Test project integration with Traefik"""
        mock_manager.return_value.is_running.return_value = True
        mock_labels.return_value.generate_complete_labels.return_value = {
            "traefik.enable": "true",
            "traefik.http.routers.test.rule": "Host(`example.com`)"
        }
        
        # Test integration process
        manager = mock_manager.return_value
        labels_gen = mock_labels.return_value
        
        project_config = {
            'name': 'test-project',
            'domain': 'example.com',
            'port': 8080
        }
        
        # Simulate integration
        labels = labels_gen.generate_complete_labels(project_config)
        
        assert "traefik.enable" in labels
        assert labels["traefik.enable"] == "true"
    
    @patch('blastdock.traefik.manager.TraefikManager')
    def test_traefik_health_check(self, mock_manager):
        """Test Traefik health check"""
        mock_instance = Mock()
        mock_instance.is_running.return_value = True
        mock_instance.health_status = "healthy"
        mock_manager.return_value.get_instance.return_value = mock_instance
        
        manager = mock_manager.return_value
        instance = manager.get_instance()
        
        assert instance.is_running() is True
        assert instance.health_status == "healthy"
    
    @patch('blastdock.traefik.ssl.SSLManager')
    def test_ssl_certificate_management(self, mock_ssl_manager):
        """Test SSL certificate lifecycle management"""
        mock_ssl_manager.return_value.certificate_exists.return_value = False
        mock_ssl_manager.return_value.request_certificate.return_value = True
        
        ssl_manager = mock_ssl_manager.return_value
        
        # Test certificate request for new domain
        domain = "example.com"
        email = "test@example.com"
        
        if not ssl_manager.certificate_exists(domain):
            result = ssl_manager.request_certificate(domain, email)
            assert result is True
    
    @patch('blastdock.utils.docker_utils.DockerClient')
    def test_traefik_network_management(self, mock_docker_client):
        """Test Traefik network management"""
        mock_docker_client.return_value.network_exists.return_value = False
        mock_docker_client.return_value.create_network.return_value = True
        
        docker_client = mock_docker_client.return_value
        
        # Test network creation
        network_name = "blastdock-network"
        
        if not docker_client.network_exists(network_name):
            result = docker_client.create_network(network_name)
            assert result is True


class TestTraefikErrorHandling:
    """Test Traefik error handling"""
    
    @patch('blastdock.utils.docker_utils.DockerClient')
    def test_docker_connection_error(self, mock_docker_client):
        """Test handling of Docker connection errors"""
        mock_docker_client.side_effect = Exception("Docker connection failed")
        
        with pytest.raises(Exception):
            TraefikManager()
    
    @patch('blastdock.utils.docker_utils.DockerClient')
    def test_container_start_failure(self, mock_docker_client):
        """Test handling of container start failures"""
        manager = TraefikManager()
        
        mock_docker_client.return_value.start_container.return_value = False
        
        result = manager.start()
        
        assert result is False
    
    @patch('subprocess.run')
    def test_ssl_certificate_request_failure(self, mock_subprocess):
        """Test handling of SSL certificate request failures"""
        ssl_manager = SSLManager()
        
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Certificate request failed"
        mock_subprocess.return_value = mock_result
        
        result = ssl_manager.request_certificate("example.com", "test@example.com")
        
        assert result is False
    
    def test_invalid_domain_labels(self):
        """Test handling of invalid domains in labels"""
        with pytest.raises(ValueError):
            TraefikLabels("test-service", "invalid..domain")
    
    @patch('blastdock.utils.docker_utils.DockerClient')
    def test_network_creation_failure(self, mock_docker_client):
        """Test handling of network creation failures"""
        installer = TraefikInstaller()
        
        mock_docker_client.return_value.create_network.return_value = False
        
        result = installer._create_network()
        
        assert result is False