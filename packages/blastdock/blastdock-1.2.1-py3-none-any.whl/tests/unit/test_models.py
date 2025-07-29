"""
Unit tests for BlastDock data models
"""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from blastdock.models.project import Project, ProjectConfig, ProjectStatus, TraefikIntegration
from blastdock.models.template import Template, TemplateConfig, TemplateField, FieldType
from blastdock.models.traefik import TraefikInstance, TraefikConfig, SSLCertificate, SSLCertificateStatus
from blastdock.models.domain import Domain, DomainConfig, DomainType, DomainStatus
from blastdock.models.port import Port, PortAllocation, PortStatus, PortType


class TestProjectModels:
    """Test project-related models"""
    
    def test_project_config_creation(self):
        """Test ProjectConfig creation with valid data"""
        config = ProjectConfig(
            name="test-project",
            template="wordpress",
            services={"wordpress": {"image": "wordpress:latest"}},
            environment={"WORDPRESS_DB_PASSWORD": "secret"}
        )
        
        assert config.name == "test-project"
        assert config.template == "wordpress"
        assert config.version == "1.0"
        assert isinstance(config.created_at, datetime)
        assert config.services["wordpress"]["image"] == "wordpress:latest"
    
    def test_project_config_validation(self):
        """Test ProjectConfig validation"""
        # Test invalid project name
        with pytest.raises(ValidationError):
            ProjectConfig(name="invalid-name-", template="wordpress")
        
        # Test valid project name
        config = ProjectConfig(name="valid-name-123", template="wordpress")
        assert config.name == "valid-name-123"
    
    def test_traefik_integration(self):
        """Test TraefikIntegration model"""
        traefik = TraefikIntegration(
            enabled=True,
            domain="example.com",
            ssl_enabled=True,
            labels={"traefik.enable": "true"}
        )
        
        assert traefik.enabled is True
        assert traefik.domain == "example.com"
        assert traefik.ssl_enabled is True
        assert traefik.labels["traefik.enable"] == "true"
    
    def test_project_methods(self, sample_project):
        """Test Project model methods"""
        # Test is_running
        assert not sample_project.is_running()
        sample_project.status = ProjectStatus.RUNNING
        assert sample_project.is_running()
        
        # Test has_traefik
        assert not sample_project.has_traefik()
        sample_project.config.traefik = TraefikIntegration(enabled=True)
        assert sample_project.has_traefik()
        
        # Test get_primary_domain
        assert sample_project.get_primary_domain() is None
        sample_project.domains = ["test.example.com", "www.example.com"]
        assert sample_project.get_primary_domain() == "test.example.com"
        
        # Test get_access_url
        sample_project.config.traefik.ssl_enabled = True
        assert sample_project.get_access_url() == "https://test.example.com"


class TestTemplateModels:
    """Test template-related models"""
    
    def test_template_field_creation(self):
        """Test TemplateField creation"""
        field = TemplateField(
            name="port",
            type=FieldType.PORT,
            description="HTTP port",
            default=8080,
            required=True,
            min_value=1024,
            max_value=65535
        )
        
        assert field.name == "port"
        assert field.type == FieldType.PORT
        assert field.default == 8080
        assert field.required is True
    
    def test_template_field_choice_validation(self):
        """Test TemplateField choice validation"""
        # Valid choice field
        field = TemplateField(
            name="environment",
            type=FieldType.CHOICE,
            description="Environment",
            choices=["development", "staging", "production"]
        )
        assert field.choices == ["development", "staging", "production"]
        
        # Invalid choice field without choices
        with pytest.raises(ValidationError):
            TemplateField(
                name="environment",
                type=FieldType.CHOICE,
                description="Environment"
            )
    
    def test_template_config_creation(self, sample_template_config):
        """Test TemplateConfig creation"""
        assert sample_template_config.name == "wordpress"
        assert sample_template_config.description == "WordPress with MySQL database"
        assert "wordpress" in sample_template_config.services
        assert "mysql" in sample_template_config.services
    
    def test_template_methods(self, sample_template):
        """Test Template model methods"""
        # Test get_service_names
        services = sample_template.get_service_names()
        assert "wordpress" in services
        assert "mysql" in services
        
        # Test get_primary_service
        primary = sample_template.get_primary_service()
        assert primary == "wordpress"
        
        # Test supports_traefik
        assert not sample_template.supports_traefik()
        
        # Test get_required_fields
        required = sample_template.get_required_fields()
        assert "wordpress_port" in required
        assert "mysql_user" in required
        assert "mysql_password" in required
    
    def test_template_field_validation(self, sample_template):
        """Test template field validation"""
        # Test valid port
        assert sample_template.validate_field_value("wordpress_port", 8080) is True
        
        # Test invalid port
        assert sample_template.validate_field_value("wordpress_port", 70000) is False
        
        # Test valid string
        assert sample_template.validate_field_value("mysql_user", "wordpress") is True
        
        # Test email validation
        field = TemplateField(name="email", type=FieldType.EMAIL, description="Email")
        sample_template.config.fields["email"] = field
        assert sample_template.validate_field_value("email", "test@example.com") is True
        assert sample_template.validate_field_value("email", "invalid-email") is False


class TestTraefikModels:
    """Test Traefik-related models"""
    
    def test_ssl_certificate_creation(self):
        """Test SSLCertificate creation"""
        cert = SSLCertificate(
            domain="example.com",
            status=SSLCertificateStatus.VALID,
            issued_at=datetime.now() - timedelta(days=30),
            expires_at=datetime.now() + timedelta(days=60),
            issuer="Let's Encrypt",
            is_valid=True,
            is_trusted=True
        )
        
        assert cert.domain == "example.com"
        assert cert.status == SSLCertificateStatus.VALID
        assert cert.is_valid is True
    
    def test_ssl_certificate_expiry_methods(self):
        """Test SSL certificate expiry methods"""
        # Certificate expiring in 5 days
        cert = SSLCertificate(
            domain="example.com",
            status=SSLCertificateStatus.VALID,
            expires_at=datetime.now() + timedelta(days=5)
        )
        
        assert cert.days_until_expiry() == 5
        assert cert.is_expiring_soon(warning_days=30) is True
        assert cert.needs_renewal(renewal_days=7) is True
        
        # Certificate expiring in 45 days
        cert.expires_at = datetime.now() + timedelta(days=45)
        assert cert.days_until_expiry() == 45
        assert cert.is_expiring_soon(warning_days=30) is False
        assert cert.needs_renewal(renewal_days=7) is False
    
    def test_traefik_config_methods(self, sample_traefik_config):
        """Test TraefikConfig methods"""
        from blastdock.models.traefik import SSLCertificate, SSLCertificateStatus
        
        # Add test certificates
        cert1 = SSLCertificate(
            domain="example.com",
            status=SSLCertificateStatus.VALID,
            expires_at=datetime.now() + timedelta(days=5),
            is_valid=True
        )
        cert2 = SSLCertificate(
            domain="test.example.com", 
            status=SSLCertificateStatus.VALID,
            expires_at=datetime.now() + timedelta(days=60),
            is_valid=False
        )
        
        sample_traefik_config.certificates = [cert1, cert2]
        
        # Test get_certificate
        found_cert = sample_traefik_config.get_certificate("example.com")
        assert found_cert is not None
        assert found_cert.domain == "example.com"
        
        # Test get_expiring_certificates
        expiring = sample_traefik_config.get_expiring_certificates(warning_days=30)
        assert len(expiring) == 1
        assert expiring[0].domain == "example.com"
        
        # Test get_invalid_certificates
        invalid = sample_traefik_config.get_invalid_certificates()
        assert len(invalid) == 1
        assert invalid[0].domain == "test.example.com"
    
    def test_traefik_instance_methods(self, sample_traefik_instance):
        """Test TraefikInstance methods"""
        # Test is_running
        assert sample_traefik_instance.is_running() is True
        
        # Test get_dashboard_url
        url = sample_traefik_instance.get_dashboard_url()
        assert url == "https://example.com"  # Uses SSL and default domain
        
        # Test update_statistics
        sample_traefik_instance.update_statistics()
        assert sample_traefik_instance.total_services == 0
        assert sample_traefik_instance.total_routers == 0


class TestDomainModels:
    """Test domain-related models"""
    
    def test_domain_config_validation(self):
        """Test DomainConfig validation"""
        # Valid domain
        config = DomainConfig(
            domain="example.com",
            type=DomainType.CUSTOM,
            project="test-project"
        )
        assert config.domain == "example.com"
        
        # Invalid domain format
        with pytest.raises(ValidationError):
            DomainConfig(
                domain="invalid..domain",
                type=DomainType.CUSTOM,
                project="test-project"
            )
    
    def test_domain_methods(self, sample_domain):
        """Test Domain model methods"""
        # Test status checks
        assert sample_domain.is_in_use() is True
        assert sample_domain.is_available() is False
        
        # Test domain type checks
        assert sample_domain.is_subdomain() is True
        assert sample_domain.is_local() is False
        
        # Test parent domain extraction
        parent = sample_domain.get_parent_domain()
        assert parent == "example.com"
        
        # Test subdomain part extraction
        subdomain = sample_domain.get_subdomain_part()
        assert subdomain == "test"
        
        # Test access URL generation
        url = sample_domain.get_access_url()
        assert url == "https://test.example.com"
        
        url_http = sample_domain.get_access_url(ssl=False)
        assert url_http == "http://test.example.com"
    
    def test_domain_ssl_methods(self, sample_domain):
        """Test domain SSL-related methods"""
        # Test SSL expiry check
        sample_domain.ssl_expires_at = datetime.now() + timedelta(days=5)
        assert sample_domain.needs_ssl_renewal(warning_days=30) is True
        
        sample_domain.ssl_expires_at = datetime.now() + timedelta(days=45)
        assert sample_domain.needs_ssl_renewal(warning_days=30) is False


class TestPortModels:
    """Test port-related models"""
    
    def test_port_allocation_validation(self):
        """Test PortAllocation validation"""
        # Valid port allocation
        allocation = PortAllocation(
            port=8080,
            project="test-project",
            service="web",
            type=PortType.HTTP
        )
        assert allocation.port == 8080
        assert allocation.type == PortType.HTTP
        
        # Invalid port number
        with pytest.raises(ValidationError):
            PortAllocation(
                port=70000,  # Invalid port
                project="test-project",
                service="web"
            )
    
    def test_port_methods(self, sample_port):
        """Test Port model methods"""
        # Test status checks
        assert sample_port.is_allocated() is True
        assert sample_port.is_available() is False
        
        # Test allocation info
        assert sample_port.get_allocated_project() == "test-project"
        assert sample_port.get_allocated_service() == "wordpress"
        
        # Test system port check
        system_port = Port(number=80, status=PortStatus.SYSTEM_RESERVED)
        assert system_port.is_system_port() is True
        
        regular_port = Port(number=8080, status=PortStatus.AVAILABLE)
        assert regular_port.is_system_port() is False
    
    def test_port_reservation_expiry(self):
        """Test port reservation expiry"""
        from blastdock.models.port import PortReservation
        
        # Non-expiring reservation
        reservation = PortReservation(
            port=8080,
            reason="Test reservation",
            permanent=True
        )
        assert reservation.is_expired() is False
        
        # Expired reservation
        reservation = PortReservation(
            port=8080,
            reason="Test reservation",
            expires_at=datetime.now() - timedelta(hours=1)
        )
        assert reservation.is_expired() is True
        
        # Non-expired reservation
        reservation = PortReservation(
            port=8080,
            reason="Test reservation",
            expires_at=datetime.now() + timedelta(hours=1)
        )
        assert reservation.is_expired() is False