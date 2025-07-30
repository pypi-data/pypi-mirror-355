"""
Simple test suite for port data models
"""

import pytest
from datetime import datetime, timedelta

from blastdock.models.port import (
    PortStatus, PortType, PortAllocation, PortReservation, 
    PortConflict, PortConfig, Port
)


class TestPortStatus:
    """Test cases for PortStatus enum"""

    def test_port_status_values(self):
        """Test port status enum values"""
        assert PortStatus.AVAILABLE == "available"
        assert PortStatus.RESERVED == "reserved"
        assert PortStatus.IN_USE == "in_use"
        assert PortStatus.CONFLICTED == "conflicted"
        assert PortStatus.SYSTEM_RESERVED == "system_reserved"


class TestPortType:
    """Test cases for PortType enum"""

    def test_port_type_values(self):
        """Test port type enum values"""
        assert PortType.HTTP == "http"
        assert PortType.HTTPS == "https"
        assert PortType.DATABASE == "database"
        assert PortType.CACHE == "cache"
        assert PortType.CUSTOM == "custom"
        assert PortType.SYSTEM == "system"


class TestPortAllocation:
    """Test cases for PortAllocation model"""

    def test_port_allocation_creation(self):
        """Test port allocation creation with valid data"""
        allocation = PortAllocation(
            port=8080,
            project="test-project",
            service="web",
            type=PortType.HTTP
        )
        
        assert allocation.port == 8080
        assert allocation.project == "test-project"
        assert allocation.service == "web"
        assert allocation.type == PortType.HTTP
        assert allocation.allocated_at is not None
        assert allocation.in_use is False

    def test_port_allocation_defaults(self):
        """Test port allocation with default values"""
        allocation = PortAllocation(port=3000, project="test", service="app")
        
        assert allocation.port == 3000
        assert allocation.type == PortType.CUSTOM
        assert allocation.in_use is False
        assert allocation.last_used is None
        assert allocation.process_id is None

    def test_port_validation_valid_ports(self):
        """Test port validation with valid port numbers"""
        valid_ports = [80, 443, 3000, 8080, 9000, 65535]
        
        for port in valid_ports:
            allocation = PortAllocation(port=port, project="test", service="app")
            assert allocation.port == port

    def test_port_validation_invalid_ports(self):
        """Test port validation with invalid port numbers"""
        invalid_ports = [0, -1, 65536, 70000]
        
        for port in invalid_ports:
            with pytest.raises(ValueError):
                PortAllocation(port=port, project="test", service="app")

    def test_port_allocation_serialization(self):
        """Test port allocation JSON serialization"""
        allocation = PortAllocation(
            port=8080,
            project="test-app",
            service="web",
            type=PortType.HTTP
        )
        
        data = allocation.dict()
        assert data['port'] == 8080
        assert data['project'] == 'test-app'
        assert data['service'] == 'web'
        assert data['type'] == 'http'

    def test_port_allocation_tags(self):
        """Test port allocation with tags"""
        allocation = PortAllocation(
            port=8080,
            project="test",
            service="web",
            tags=["frontend", "public"]
        )
        
        assert "frontend" in allocation.tags
        assert "public" in allocation.tags
        assert len(allocation.tags) == 2


class TestPortReservation:
    """Test cases for PortReservation model"""

    def test_port_reservation_creation(self):
        """Test port reservation creation"""
        reservation = PortReservation(
            port=9000,
            reason="Future deployment",
            reserved_by="admin"
        )
        
        assert reservation.port == 9000
        assert reservation.reason == "Future deployment"
        assert reservation.reserved_by == "admin"
        assert reservation.reserved_at is not None
        assert reservation.permanent is False

    def test_port_reservation_expiration_check(self):
        """Test checking if reservation is expired"""
        # Expired reservation
        expired_reservation = PortReservation(
            port=9000,
            reason="Test",
            expires_at=datetime.now() - timedelta(hours=1)
        )
        
        # Future reservation
        future_reservation = PortReservation(
            port=9001,
            reason="Test",
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        # Permanent reservation
        permanent_reservation = PortReservation(
            port=9002,
            reason="Test",
            permanent=True
        )
        
        assert expired_reservation.is_expired() is True
        assert future_reservation.is_expired() is False
        assert permanent_reservation.is_expired() is False

    def test_port_reservation_priority(self):
        """Test port reservation priority"""
        high_priority = PortReservation(
            port=9000,
            reason="Critical service",
            priority=10
        )
        
        low_priority = PortReservation(
            port=9001,
            reason="Test service",
            priority=1
        )
        
        assert high_priority.priority == 10
        assert low_priority.priority == 1


class TestPortConflict:
    """Test cases for PortConflict model"""

    def test_port_conflict_creation(self):
        """Test port conflict creation"""
        conflict = PortConflict(
            port=8080,
            existing_service="nginx",
            conflicting_service="apache"
        )
        
        assert conflict.port == 8080
        assert conflict.existing_service == "nginx"
        assert conflict.conflicting_service == "apache"


class TestPortConfig:
    """Test cases for PortConfig model"""

    def test_port_config_creation(self):
        """Test port config creation"""
        config = PortConfig(
            default_range_start=8000,
            default_range_end=9000,
            reserved_ports=[22, 80, 443]
        )
        
        assert config.default_range_start == 8000
        assert config.default_range_end == 9000
        assert 22 in config.reserved_ports
        assert 80 in config.reserved_ports
        assert 443 in config.reserved_ports

    def test_port_config_validation(self):
        """Test port config validation"""
        # Valid config
        valid_config = PortConfig(
            default_range_start=8000,
            default_range_end=9000
        )
        assert valid_config.default_range_start < valid_config.default_range_end

    def test_port_config_defaults(self):
        """Test port config default values"""
        config = PortConfig()
        
        assert config.default_range_start >= 1024  # Should avoid system ports
        assert config.default_range_end <= 65535
        assert len(config.reserved_ports) > 0  # Should have some reserved ports


class TestPort:
    """Test cases for Port model"""

    def test_port_creation(self):
        """Test port creation"""
        port = Port(
            number=8080,
            status=PortStatus.AVAILABLE,
            type=PortType.HTTP
        )
        
        assert port.number == 8080
        assert port.status == PortStatus.AVAILABLE
        assert port.type == PortType.HTTP

    def test_port_assignment(self):
        """Test port assignment"""
        port = Port(
            number=8080,
            status=PortStatus.AVAILABLE,
            type=PortType.HTTP
        )
        
        # Assign port
        port.assign_to_project("test-project", "web-service")
        
        assert port.status == PortStatus.IN_USE
        assert port.assigned_project == "test-project"
        assert port.assigned_service == "web-service"
        assert port.assigned_at is not None

    def test_port_release(self):
        """Test port release"""
        port = Port(
            number=8080,
            status=PortStatus.IN_USE,
            type=PortType.HTTP,
            assigned_project="test-project",
            assigned_service="web-service"
        )
        
        # Release port
        port.release()
        
        assert port.status == PortStatus.AVAILABLE
        assert port.assigned_project is None
        assert port.assigned_service is None

    def test_port_is_available(self):
        """Test checking if port is available"""
        available_port = Port(number=8080, status=PortStatus.AVAILABLE)
        used_port = Port(number=8081, status=PortStatus.IN_USE)
        reserved_port = Port(number=8082, status=PortStatus.RESERVED)
        
        assert available_port.is_available() is True
        assert used_port.is_available() is False
        assert reserved_port.is_available() is False

    def test_port_is_system_port(self):
        """Test checking if port is a system port"""
        system_port = Port(number=80, type=PortType.SYSTEM)
        user_port = Port(number=8080, type=PortType.HTTP)
        
        assert system_port.is_system_port() is True
        assert user_port.is_system_port() is False

    def test_port_conflict_detection(self):
        """Test port conflict detection"""
        port = Port(
            number=8080,
            status=PortStatus.IN_USE,
            assigned_project="project1",
            assigned_service="web"
        )
        
        # Try to assign to different project
        conflict = port.check_conflict("project2", "api")
        
        assert conflict is not None
        assert conflict.port == 8080
        assert conflict.existing_service == "web"
        assert conflict.conflicting_service == "api"