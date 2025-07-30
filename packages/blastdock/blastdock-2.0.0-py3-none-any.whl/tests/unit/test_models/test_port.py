"""
Test suite for port data models
"""

import pytest
from datetime import datetime
from unittest.mock import patch

from blastdock.models.port import (
    PortStatus, PortType, PortAllocation, PortRange, 
    PortManager, PortConflict, PortReservation
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

    def test_port_status_comparison(self):
        """Test port status comparison"""
        assert PortStatus.AVAILABLE == PortStatus.AVAILABLE
        assert PortStatus.AVAILABLE != PortStatus.RESERVED


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

    def test_port_type_categories(self):
        """Test port type categorization"""
        web_ports = [PortType.HTTP, PortType.HTTPS]
        data_ports = [PortType.DATABASE, PortType.CACHE]
        assert PortType.HTTP in web_ports
        assert PortType.DATABASE in data_ports


class TestPortAllocation:
    """Test cases for PortAllocation model"""

    def test_port_allocation_creation(self):
        """Test port allocation creation with valid data"""
        allocation = PortAllocation(
            port=8080,
            status=PortStatus.AVAILABLE,
            port_type=PortType.HTTP,
            project_name="test-project",
            service_name="web"
        )
        
        assert allocation.port == 8080
        assert allocation.status == PortStatus.AVAILABLE
        assert allocation.port_type == PortType.HTTP
        assert allocation.project_name == "test-project"
        assert allocation.service_name == "web"
        assert allocation.allocated_at is not None

    def test_port_allocation_defaults(self):
        """Test port allocation with default values"""
        allocation = PortAllocation(port=3000)
        
        assert allocation.port == 3000
        assert allocation.status == PortStatus.AVAILABLE
        assert allocation.port_type == PortType.CUSTOM
        assert allocation.project_name is None
        assert allocation.service_name is None

    def test_port_validation_valid_ports(self):
        """Test port validation with valid port numbers"""
        valid_ports = [80, 443, 3000, 8080, 9000, 65535]
        
        for port in valid_ports:
            allocation = PortAllocation(port=port)
            assert allocation.port == port

    def test_port_validation_invalid_ports(self):
        """Test port validation with invalid port numbers"""
        invalid_ports = [0, -1, 65536, 70000]
        
        for port in invalid_ports:
            with pytest.raises(ValueError):
                PortAllocation(port=port)

    def test_reserved_port_validation(self):
        """Test reserved port validation"""
        # System ports (typically 1-1023) should be flagged
        with pytest.raises(ValueError):
            PortAllocation(port=22, status=PortStatus.AVAILABLE)
        
        # But should work with SYSTEM_RESERVED status
        allocation = PortAllocation(port=22, status=PortStatus.SYSTEM_RESERVED)
        assert allocation.port == 22

    def test_port_allocation_serialization(self):
        """Test port allocation JSON serialization"""
        allocation = PortAllocation(
            port=8080,
            status=PortStatus.IN_USE,
            port_type=PortType.HTTP,
            project_name="test-app"
        )
        
        data = allocation.dict()
        assert data['port'] == 8080
        assert data['status'] == 'in_use'
        assert data['port_type'] == 'http'
        assert data['project_name'] == 'test-app'

    def test_port_allocation_from_dict(self):
        """Test creating port allocation from dictionary"""
        data = {
            'port': 5432,
            'status': 'reserved',
            'port_type': 'database',
            'project_name': 'db-project',
            'service_name': 'postgres'
        }
        
        allocation = PortAllocation(**data)
        assert allocation.port == 5432
        assert allocation.status == PortStatus.RESERVED
        assert allocation.port_type == PortType.DATABASE

    def test_port_allocation_update(self):
        """Test updating port allocation"""
        allocation = PortAllocation(port=8080)
        
        # Update status
        allocation.status = PortStatus.IN_USE
        allocation.project_name = "new-project"
        
        assert allocation.status == PortStatus.IN_USE
        assert allocation.project_name == "new-project"

    def test_port_allocation_is_available(self):
        """Test checking if port is available"""
        available_allocation = PortAllocation(port=8080, status=PortStatus.AVAILABLE)
        used_allocation = PortAllocation(port=8081, status=PortStatus.IN_USE)
        
        assert available_allocation.is_available() is True
        assert used_allocation.is_available() is False

    def test_port_allocation_is_system_port(self):
        """Test checking if port is a system port"""
        system_port = PortAllocation(port=80, status=PortStatus.SYSTEM_RESERVED)
        user_port = PortAllocation(port=8080)
        
        assert system_port.is_system_port() is True
        assert user_port.is_system_port() is False


class TestPortRange:
    """Test cases for PortRange model"""

    def test_port_range_creation(self):
        """Test port range creation"""
        port_range = PortRange(
            start_port=8000,
            end_port=8999,
            description="Development ports"
        )
        
        assert port_range.start_port == 8000
        assert port_range.end_port == 8999
        assert port_range.description == "Development ports"

    def test_port_range_validation(self):
        """Test port range validation"""
        # Valid range
        port_range = PortRange(start_port=8000, end_port=9000)
        assert port_range.start_port < port_range.end_port
        
        # Invalid range (start > end)
        with pytest.raises(ValueError):
            PortRange(start_port=9000, end_port=8000)

    def test_port_range_contains(self):
        """Test checking if port is in range"""
        port_range = PortRange(start_port=8000, end_port=8999)
        
        assert port_range.contains(8500) is True
        assert port_range.contains(7999) is False
        assert port_range.contains(9000) is False

    def test_port_range_size(self):
        """Test getting port range size"""
        port_range = PortRange(start_port=8000, end_port=8999)
        assert port_range.size() == 1000

    def test_port_range_overlap(self):
        """Test checking range overlap"""
        range1 = PortRange(start_port=8000, end_port=8999)
        range2 = PortRange(start_port=8500, end_port=9500)
        range3 = PortRange(start_port=9000, end_port=9999)
        
        assert range1.overlaps(range2) is True
        assert range1.overlaps(range3) is False

    def test_port_range_get_available_ports(self):
        """Test getting available ports in range"""
        port_range = PortRange(start_port=8000, end_port=8005)
        used_ports = {8001, 8003}
        
        available = port_range.get_available_ports(used_ports)
        assert available == {8000, 8002, 8004, 8005}


class TestPortManager:
    """Test cases for PortManager model"""

    def test_port_manager_creation(self):
        """Test port manager creation"""
        manager = PortManager()
        
        assert isinstance(manager.allocations, dict)
        assert isinstance(manager.reservations, list)
        assert isinstance(manager.ranges, list)

    def test_port_manager_allocate_port(self):
        """Test allocating a port"""
        manager = PortManager()
        
        allocation = manager.allocate_port(
            port=8080,
            project_name="test-project",
            service_name="web",
            port_type=PortType.HTTP
        )
        
        assert allocation.port == 8080
        assert allocation.status == PortStatus.IN_USE
        assert 8080 in manager.allocations

    def test_port_manager_allocate_conflict(self):
        """Test allocating already allocated port"""
        manager = PortManager()
        
        # First allocation
        manager.allocate_port(8080, "project1", "web")
        
        # Second allocation should conflict
        with pytest.raises(ValueError):
            manager.allocate_port(8080, "project2", "web")

    def test_port_manager_release_port(self):
        """Test releasing a port"""
        manager = PortManager()
        
        # Allocate then release
        manager.allocate_port(8080, "test-project", "web")
        assert 8080 in manager.allocations
        
        manager.release_port(8080)
        assert 8080 not in manager.allocations

    def test_port_manager_find_available_port(self):
        """Test finding available port"""
        manager = PortManager()
        
        # Allocate some ports
        manager.allocate_port(8080, "project1", "web")
        manager.allocate_port(8081, "project1", "api")
        
        # Find next available
        available = manager.find_available_port(start_port=8080)
        assert available == 8082

    def test_port_manager_find_available_in_range(self):
        """Test finding available port in specific range"""
        manager = PortManager()
        manager.add_range(PortRange(start_port=9000, end_port=9010))
        
        # Allocate some ports in range
        manager.allocate_port(9000, "project1", "web")
        manager.allocate_port(9002, "project1", "db")
        
        available = manager.find_available_port_in_range(9000, 9010)
        assert available == 9001

    def test_port_manager_get_project_ports(self):
        """Test getting all ports for a project"""
        manager = PortManager()
        
        manager.allocate_port(8080, "test-project", "web")
        manager.allocate_port(8081, "test-project", "api")
        manager.allocate_port(8082, "other-project", "web")
        
        project_ports = manager.get_project_ports("test-project")
        assert len(project_ports) == 2
        assert 8080 in [p.port for p in project_ports]
        assert 8081 in [p.port for p in project_ports]

    def test_port_manager_release_project_ports(self):
        """Test releasing all ports for a project"""
        manager = PortManager()
        
        manager.allocate_port(8080, "test-project", "web")
        manager.allocate_port(8081, "test-project", "api")
        manager.allocate_port(8082, "other-project", "web")
        
        released = manager.release_project_ports("test-project")
        assert len(released) == 2
        assert len(manager.allocations) == 1
        assert 8082 in manager.allocations

    def test_port_manager_add_reservation(self):
        """Test adding port reservation"""
        manager = PortManager()
        
        reservation = PortReservation(
            port=9000,
            project_name="future-project",
            expires_at=datetime.now()
        )
        
        manager.add_reservation(reservation)
        assert len(manager.reservations) == 1
        assert manager.is_port_reserved(9000) is True

    def test_port_manager_cleanup_expired_reservations(self):
        """Test cleaning up expired reservations"""
        manager = PortManager()
        
        # Add expired reservation
        expired_reservation = PortReservation(
            port=9000,
            project_name="old-project",
            expires_at=datetime(2020, 1, 1)
        )
        manager.add_reservation(expired_reservation)
        
        # Add valid reservation
        valid_reservation = PortReservation(
            port=9001,
            project_name="current-project",
            expires_at=datetime(2030, 1, 1)
        )
        manager.add_reservation(valid_reservation)
        
        cleaned = manager.cleanup_expired_reservations()
        assert cleaned == 1
        assert len(manager.reservations) == 1
        assert manager.reservations[0].port == 9001

    def test_port_manager_get_statistics(self):
        """Test getting port usage statistics"""
        manager = PortManager()
        
        manager.allocate_port(8080, "project1", "web", PortType.HTTP)
        manager.allocate_port(5432, "project1", "db", PortType.DATABASE)
        manager.allocate_port(6379, "project2", "cache", PortType.CACHE)
        
        stats = manager.get_statistics()
        assert stats['total_allocated'] == 3
        assert stats['by_type']['http'] == 1
        assert stats['by_type']['database'] == 1
        assert stats['by_type']['cache'] == 1
        assert stats['by_project']['project1'] == 2
        assert stats['by_project']['project2'] == 1


class TestPortConflict:
    """Test cases for PortConflict model"""

    def test_port_conflict_creation(self):
        """Test port conflict creation"""
        conflict = PortConflict(
            port=8080,
            existing_project="project1",
            existing_service="web",
            requested_project="project2",
            requested_service="api"
        )
        
        assert conflict.port == 8080
        assert conflict.existing_project == "project1"
        assert conflict.requested_project == "project2"
        assert conflict.detected_at is not None

    def test_port_conflict_resolution_suggestions(self):
        """Test getting conflict resolution suggestions"""
        conflict = PortConflict(
            port=8080,
            existing_project="project1",
            existing_service="web",
            requested_project="project2",
            requested_service="api"
        )
        
        suggestions = conflict.get_resolution_suggestions()
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert any("alternative port" in suggestion.lower() for suggestion in suggestions)

    def test_port_conflict_severity(self):
        """Test conflict severity assessment"""
        # System port conflict
        system_conflict = PortConflict(
            port=80,
            existing_project="system",
            existing_service="nginx",
            requested_project="project1",
            requested_service="web"
        )
        
        # User port conflict
        user_conflict = PortConflict(
            port=8080,
            existing_project="project1",
            existing_service="web",
            requested_project="project2",
            requested_service="api"
        )
        
        assert system_conflict.get_severity() == "high"
        assert user_conflict.get_severity() == "medium"


class TestPortReservation:
    """Test cases for PortReservation model"""

    def test_port_reservation_creation(self):
        """Test port reservation creation"""
        expires_at = datetime(2024, 12, 31)
        reservation = PortReservation(
            port=9000,
            project_name="future-project",
            expires_at=expires_at,
            reason="Upcoming deployment"
        )
        
        assert reservation.port == 9000
        assert reservation.project_name == "future-project"
        assert reservation.expires_at == expires_at
        assert reservation.reason == "Upcoming deployment"

    def test_port_reservation_is_expired(self):
        """Test checking if reservation is expired"""
        expired_reservation = PortReservation(
            port=9000,
            project_name="old-project",
            expires_at=datetime(2020, 1, 1)
        )
        
        future_reservation = PortReservation(
            port=9001,
            project_name="future-project",
            expires_at=datetime(2030, 1, 1)
        )
        
        assert expired_reservation.is_expired() is True
        assert future_reservation.is_expired() is False

    def test_port_reservation_extend(self):
        """Test extending reservation"""
        reservation = PortReservation(
            port=9000,
            project_name="project",
            expires_at=datetime(2024, 1, 1)
        )
        
        new_expiry = datetime(2024, 6, 1)
        reservation.extend(new_expiry)
        
        assert reservation.expires_at == new_expiry

    def test_port_reservation_time_remaining(self):
        """Test getting time remaining on reservation"""
        future_date = datetime(2030, 1, 1)
        reservation = PortReservation(
            port=9000,
            project_name="project",
            expires_at=future_date
        )
        
        remaining = reservation.time_remaining()
        assert remaining.days > 0