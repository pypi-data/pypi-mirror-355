"""
Test suite for domain data models
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from blastdock.models.domain import (
    DomainType, DomainStatus, DNSRecord, DomainConfiguration,
    DomainManager, SSLConfiguration, DomainValidation
)


class TestDomainType:
    """Test cases for DomainType enum"""

    def test_domain_type_values(self):
        """Test domain type enum values"""
        assert DomainType.CUSTOM == "custom"
        assert DomainType.SUBDOMAIN == "subdomain"
        assert DomainType.WILDCARD == "wildcard"
        assert DomainType.LOCAL == "local"

    def test_domain_type_categorization(self):
        """Test domain type categorization"""
        external_types = [DomainType.CUSTOM, DomainType.SUBDOMAIN, DomainType.WILDCARD]
        local_types = [DomainType.LOCAL]
        
        assert DomainType.CUSTOM in external_types
        assert DomainType.LOCAL in local_types


class TestDomainStatus:
    """Test cases for DomainStatus enum"""

    def test_domain_status_values(self):
        """Test domain status enum values"""
        assert DomainStatus.AVAILABLE == "available"
        assert DomainStatus.RESERVED == "reserved"
        assert DomainStatus.IN_USE == "in_use"
        assert DomainStatus.INVALID == "invalid"
        assert DomainStatus.DNS_ERROR == "dns_error"
        assert DomainStatus.UNREACHABLE == "unreachable"

    def test_domain_status_operational(self):
        """Test operational domain statuses"""
        operational = [DomainStatus.AVAILABLE, DomainStatus.IN_USE]
        problematic = [DomainStatus.INVALID, DomainStatus.DNS_ERROR, DomainStatus.UNREACHABLE]
        
        assert DomainStatus.AVAILABLE in operational
        assert DomainStatus.DNS_ERROR in problematic


class TestDNSRecord:
    """Test cases for DNSRecord model"""

    def test_dns_record_creation(self):
        """Test DNS record creation"""
        record = DNSRecord(
            record_type="A",
            name="example.com",
            value="192.168.1.1",
            ttl=300
        )
        
        assert record.record_type == "A"
        assert record.name == "example.com"
        assert record.value == "192.168.1.1"
        assert record.ttl == 300

    def test_dns_record_types(self):
        """Test different DNS record types"""
        records = [
            DNSRecord(record_type="A", name="example.com", value="192.168.1.1"),
            DNSRecord(record_type="AAAA", name="example.com", value="2001:db8::1"),
            DNSRecord(record_type="CNAME", name="www.example.com", value="example.com"),
            DNSRecord(record_type="MX", name="example.com", value="mail.example.com"),
            DNSRecord(record_type="TXT", name="example.com", value="v=spf1 include:_spf.google.com ~all")
        ]
        
        for record in records:
            assert record.record_type in ["A", "AAAA", "CNAME", "MX", "TXT"]

    def test_dns_record_validation(self):
        """Test DNS record validation"""
        # Valid A record
        valid_a = DNSRecord(record_type="A", name="example.com", value="192.168.1.1")
        assert valid_a.is_valid()
        
        # Invalid A record (bad IP)
        invalid_a = DNSRecord(record_type="A", name="example.com", value="invalid-ip")
        assert not invalid_a.is_valid()

    def test_dns_record_serialization(self):
        """Test DNS record serialization"""
        record = DNSRecord(
            record_type="A",
            name="test.example.com",
            value="10.0.0.1",
            ttl=600
        )
        
        data = record.dict()
        assert data['record_type'] == "A"
        assert data['name'] == "test.example.com"
        assert data['value'] == "10.0.0.1"
        assert data['ttl'] == 600

    def test_dns_record_is_ipv4(self):
        """Test checking if record is IPv4"""
        ipv4_record = DNSRecord(record_type="A", name="example.com", value="192.168.1.1")
        ipv6_record = DNSRecord(record_type="AAAA", name="example.com", value="2001:db8::1")
        
        assert ipv4_record.is_ipv4() is True
        assert ipv6_record.is_ipv4() is False

    def test_dns_record_is_ipv6(self):
        """Test checking if record is IPv6"""
        ipv4_record = DNSRecord(record_type="A", name="example.com", value="192.168.1.1")
        ipv6_record = DNSRecord(record_type="AAAA", name="example.com", value="2001:db8::1")
        
        assert ipv4_record.is_ipv6() is False
        assert ipv6_record.is_ipv6() is True


class TestDomainConfiguration:
    """Test cases for DomainConfiguration model"""

    def test_domain_configuration_creation(self):
        """Test domain configuration creation"""
        config = DomainConfiguration(
            domain="example.com",
            domain_type=DomainType.CUSTOM,
            status=DomainStatus.AVAILABLE,
            project_name="test-project",
            service_name="web"
        )
        
        assert config.domain == "example.com"
        assert config.domain_type == DomainType.CUSTOM
        assert config.status == DomainStatus.AVAILABLE
        assert config.project_name == "test-project"
        assert config.service_name == "web"

    def test_domain_configuration_defaults(self):
        """Test domain configuration with defaults"""
        config = DomainConfiguration(domain="test.local")
        
        assert config.domain == "test.local"
        assert config.domain_type == DomainType.LOCAL
        assert config.status == DomainStatus.AVAILABLE
        assert config.ssl_enabled is False
        assert config.auto_redirect is False

    def test_domain_validation_valid_domains(self):
        """Test domain validation with valid domains"""
        valid_domains = [
            "example.com",
            "sub.example.com",
            "test-site.example.org",
            "localhost",
            "app.local"
        ]
        
        for domain in valid_domains:
            config = DomainConfiguration(domain=domain)
            assert config.domain == domain

    def test_domain_validation_invalid_domains(self):
        """Test domain validation with invalid domains"""
        invalid_domains = [
            "",
            "invalid..domain",
            "domain with spaces",
            "domain.toolongtobevalid" * 10,
            ".invalid-start",
            "invalid-end."
        ]
        
        for domain in invalid_domains:
            with pytest.raises(ValueError):
                DomainConfiguration(domain=domain)

    def test_domain_configuration_subdomain_detection(self):
        """Test automatic subdomain type detection"""
        config = DomainConfiguration(domain="api.example.com")
        assert config.is_subdomain() is True
        
        config = DomainConfiguration(domain="example.com")
        assert config.is_subdomain() is False

    def test_domain_configuration_wildcard_detection(self):
        """Test wildcard domain detection"""
        wildcard_config = DomainConfiguration(
            domain="*.example.com",
            domain_type=DomainType.WILDCARD
        )
        
        regular_config = DomainConfiguration(domain="app.example.com")
        
        assert wildcard_config.is_wildcard() is True
        assert regular_config.is_wildcard() is False

    def test_domain_configuration_local_detection(self):
        """Test local domain detection"""
        local_domains = ["localhost", "app.local", "test.localhost"]
        external_domains = ["example.com", "app.example.com"]
        
        for domain in local_domains:
            config = DomainConfiguration(domain=domain)
            assert config.is_local() is True
        
        for domain in external_domains:
            config = DomainConfiguration(domain=domain)
            assert config.is_local() is False

    def test_domain_configuration_ssl_settings(self):
        """Test SSL configuration settings"""
        config = DomainConfiguration(
            domain="secure.example.com",
            ssl_enabled=True,
            force_https=True,
            ssl_certificate_path="/path/to/cert.pem",
            ssl_key_path="/path/to/key.pem"
        )
        
        assert config.ssl_enabled is True
        assert config.force_https is True
        assert config.ssl_certificate_path == "/path/to/cert.pem"
        assert config.ssl_key_path == "/path/to/key.pem"

    def test_domain_configuration_dns_records(self):
        """Test DNS records association"""
        config = DomainConfiguration(domain="example.com")
        
        # Add DNS records
        a_record = DNSRecord(record_type="A", name="example.com", value="192.168.1.1")
        cname_record = DNSRecord(record_type="CNAME", name="www.example.com", value="example.com")
        
        config.add_dns_record(a_record)
        config.add_dns_record(cname_record)
        
        assert len(config.dns_records) == 2
        assert any(r.record_type == "A" for r in config.dns_records)
        assert any(r.record_type == "CNAME" for r in config.dns_records)

    def test_domain_configuration_get_primary_ip(self):
        """Test getting primary IP address"""
        config = DomainConfiguration(domain="example.com")
        
        # Add A record
        a_record = DNSRecord(record_type="A", name="example.com", value="192.168.1.1")
        config.add_dns_record(a_record)
        
        primary_ip = config.get_primary_ip()
        assert primary_ip == "192.168.1.1"

    def test_domain_configuration_last_checked(self):
        """Test last checked timestamp tracking"""
        config = DomainConfiguration(domain="example.com")
        
        # Initially None
        assert config.last_checked is None
        
        # Update last checked
        now = datetime.now()
        config.update_last_checked()
        
        assert config.last_checked is not None
        assert (config.last_checked - now).total_seconds() < 1


class TestDomainManager:
    """Test cases for DomainManager model"""

    def test_domain_manager_creation(self):
        """Test domain manager creation"""
        manager = DomainManager()
        
        assert isinstance(manager.domains, dict)
        assert isinstance(manager.reservations, list)
        assert manager.default_domain == "localhost"

    def test_domain_manager_add_domain(self):
        """Test adding domain to manager"""
        manager = DomainManager()
        
        config = DomainConfiguration(
            domain="app.example.com",
            project_name="test-project",
            service_name="web"
        )
        
        manager.add_domain(config)
        
        assert "app.example.com" in manager.domains
        assert manager.domains["app.example.com"] == config

    def test_domain_manager_remove_domain(self):
        """Test removing domain from manager"""
        manager = DomainManager()
        
        config = DomainConfiguration(domain="app.example.com")
        manager.add_domain(config)
        
        removed = manager.remove_domain("app.example.com")
        
        assert removed == config
        assert "app.example.com" not in manager.domains

    def test_domain_manager_find_available_subdomain(self):
        """Test finding available subdomain"""
        manager = DomainManager()
        
        # Add existing subdomains
        manager.add_domain(DomainConfiguration(domain="app1.example.com"))
        manager.add_domain(DomainConfiguration(domain="app2.example.com"))
        
        available = manager.find_available_subdomain("example.com", "app")
        assert available == "app3.example.com"

    def test_domain_manager_get_project_domains(self):
        """Test getting domains for project"""
        manager = DomainManager()
        
        manager.add_domain(DomainConfiguration(
            domain="web.example.com",
            project_name="test-project"
        ))
        manager.add_domain(DomainConfiguration(
            domain="api.example.com",
            project_name="test-project"
        ))
        manager.add_domain(DomainConfiguration(
            domain="other.example.com",
            project_name="other-project"
        ))
        
        project_domains = manager.get_project_domains("test-project")
        assert len(project_domains) == 2
        domain_names = [d.domain for d in project_domains]
        assert "web.example.com" in domain_names
        assert "api.example.com" in domain_names

    def test_domain_manager_validate_domain(self):
        """Test domain validation"""
        manager = DomainManager()
        
        # Valid domain
        result = manager.validate_domain("valid.example.com")
        assert result['valid'] is True
        
        # Invalid domain
        result = manager.validate_domain("invalid..domain")
        assert result['valid'] is False
        assert len(result['errors']) > 0

    def test_domain_manager_check_domain_availability(self):
        """Test checking domain availability"""
        manager = DomainManager()
        
        # Available domain
        assert manager.is_domain_available("new.example.com") is True
        
        # Add domain and check again
        manager.add_domain(DomainConfiguration(domain="new.example.com"))
        assert manager.is_domain_available("new.example.com") is False

    def test_domain_manager_generate_traefik_rules(self):
        """Test generating Traefik routing rules"""
        manager = DomainManager()
        
        config = DomainConfiguration(
            domain="app.example.com",
            project_name="test-project",
            service_name="web"
        )
        manager.add_domain(config)
        
        rules = manager.generate_traefik_rules(config)
        assert isinstance(rules, dict)
        assert 'rule' in rules
        assert 'app.example.com' in rules['rule']

    def test_domain_manager_ssl_certificate_management(self):
        """Test SSL certificate management"""
        manager = DomainManager()
        
        config = DomainConfiguration(
            domain="secure.example.com",
            ssl_enabled=True
        )
        
        # Generate certificate paths
        cert_info = manager.get_ssl_certificate_info(config)
        assert 'certificate_path' in cert_info
        assert 'key_path' in cert_info
        assert 'ca_path' in cert_info


class TestSSLConfiguration:
    """Test cases for SSLConfiguration model"""

    def test_ssl_configuration_creation(self):
        """Test SSL configuration creation"""
        ssl_config = SSLConfiguration(
            enabled=True,
            certificate_path="/path/to/cert.pem",
            key_path="/path/to/key.pem",
            ca_path="/path/to/ca.pem"
        )
        
        assert ssl_config.enabled is True
        assert ssl_config.certificate_path == "/path/to/cert.pem"
        assert ssl_config.key_path == "/path/to/key.pem"
        assert ssl_config.ca_path == "/path/to/ca.pem"

    def test_ssl_configuration_letsencrypt(self):
        """Test Let's Encrypt SSL configuration"""
        ssl_config = SSLConfiguration(
            enabled=True,
            use_letsencrypt=True,
            letsencrypt_email="admin@example.com"
        )
        
        assert ssl_config.use_letsencrypt is True
        assert ssl_config.letsencrypt_email == "admin@example.com"

    def test_ssl_configuration_validation(self):
        """Test SSL configuration validation"""
        # Valid configuration
        valid_config = SSLConfiguration(
            enabled=True,
            certificate_path="/valid/cert.pem",
            key_path="/valid/key.pem"
        )
        assert valid_config.is_valid()
        
        # Invalid configuration (enabled but no paths)
        invalid_config = SSLConfiguration(enabled=True)
        assert not invalid_config.is_valid()

    def test_ssl_configuration_self_signed(self):
        """Test self-signed certificate configuration"""
        ssl_config = SSLConfiguration(
            enabled=True,
            self_signed=True,
            self_signed_days=365
        )
        
        assert ssl_config.self_signed is True
        assert ssl_config.self_signed_days == 365

    def test_ssl_configuration_expiry_check(self):
        """Test SSL certificate expiry checking"""
        ssl_config = SSLConfiguration(
            enabled=True,
            certificate_path="/path/to/cert.pem"
        )
        
        # Mock certificate expiry check
        with patch.object(ssl_config, 'check_certificate_expiry') as mock_check:
            mock_check.return_value = datetime.now() + timedelta(days=30)
            
            expiry = ssl_config.get_certificate_expiry()
            assert expiry is not None
            assert expiry > datetime.now()


class TestDomainValidation:
    """Test cases for DomainValidation model"""

    def test_domain_validation_creation(self):
        """Test domain validation creation"""
        validation = DomainValidation(
            domain="example.com",
            validation_type="dns",
            status="pending",
            challenge_token="abc123"
        )
        
        assert validation.domain == "example.com"
        assert validation.validation_type == "dns"
        assert validation.status == "pending"
        assert validation.challenge_token == "abc123"

    def test_domain_validation_dns_challenge(self):
        """Test DNS challenge validation"""
        validation = DomainValidation(
            domain="example.com",
            validation_type="dns",
            challenge_token="dns_challenge_token"
        )
        
        dns_record = validation.get_dns_challenge_record()
        assert dns_record['record_type'] == "TXT"
        assert "_acme-challenge" in dns_record['name']
        assert dns_record['value'] == "dns_challenge_token"

    def test_domain_validation_http_challenge(self):
        """Test HTTP challenge validation"""
        validation = DomainValidation(
            domain="example.com",
            validation_type="http",
            challenge_token="http_challenge_token"
        )
        
        challenge_url = validation.get_http_challenge_url()
        assert "example.com/.well-known/acme-challenge/" in challenge_url

    def test_domain_validation_completion(self):
        """Test domain validation completion"""
        validation = DomainValidation(
            domain="example.com",
            validation_type="dns",
            status="pending"
        )
        
        # Mark as completed
        validation.mark_completed()
        
        assert validation.status == "completed"
        assert validation.completed_at is not None

    def test_domain_validation_failure(self):
        """Test domain validation failure"""
        validation = DomainValidation(
            domain="example.com",
            validation_type="dns",
            status="pending"
        )
        
        # Mark as failed
        validation.mark_failed("DNS record not found")
        
        assert validation.status == "failed"
        assert validation.error_message == "DNS record not found"
        assert validation.failed_at is not None

    def test_domain_validation_retry(self):
        """Test domain validation retry"""
        validation = DomainValidation(
            domain="example.com",
            validation_type="dns",
            status="failed",
            retry_count=2
        )
        
        # Retry validation
        validation.retry()
        
        assert validation.status == "pending"
        assert validation.retry_count == 3
        assert validation.last_retry_at is not None

    def test_domain_validation_expiry(self):
        """Test domain validation expiry"""
        # Expired validation
        expired_validation = DomainValidation(
            domain="example.com",
            validation_type="dns",
            created_at=datetime.now() - timedelta(hours=25)  # Older than 24 hours
        )
        
        # Fresh validation
        fresh_validation = DomainValidation(
            domain="example.com",
            validation_type="dns",
            created_at=datetime.now() - timedelta(hours=1)
        )
        
        assert expired_validation.is_expired() is True
        assert fresh_validation.is_expired() is False