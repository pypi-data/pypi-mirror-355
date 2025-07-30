"""
Test suite for Docker error handling
"""

import pytest
from unittest.mock import Mock, patch

from blastdock.docker.errors import (
    DockerError,
    DockerNotFoundError,
    DockerNotRunningError,
    DockerConnectionError,
    DockerComposeError,
    ContainerError,
    ImageError,
    NetworkError,
    VolumeError,
    create_docker_error
)


class TestDockerError:
    """Test cases for DockerError base class"""

    def test_docker_error_initialization(self):
        """Test DockerError initialization"""
        error = DockerError(
            message="Test error",
            details="Error details",
            suggestions=["Fix 1", "Fix 2"]
        )
        
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.details == "Error details"
        assert error.suggestions == ["Fix 1", "Fix 2"]

    def test_docker_error_without_details(self):
        """Test DockerError without details"""
        error = DockerError("Test error")
        
        assert error.message == "Test error"
        assert error.details is None
        assert error.suggestions == []


class TestDockerNotFoundError:
    """Test cases for DockerNotFoundError"""

    def test_docker_not_found_error(self):
        """Test DockerNotFoundError initialization"""
        error = DockerNotFoundError()
        
        assert "Docker not found" in str(error)
        assert error.details is not None
        assert len(error.suggestions) > 0
        assert any("Install Docker" in s for s in error.suggestions)

    def test_docker_not_found_custom_message(self):
        """Test DockerNotFoundError with custom message"""
        error = DockerNotFoundError("Custom Docker not found message")
        
        assert str(error) == "Custom Docker not found message"


class TestDockerNotRunningError:
    """Test cases for DockerNotRunningError"""

    def test_docker_not_running_error(self):
        """Test DockerNotRunningError initialization"""
        error = DockerNotRunningError()
        
        assert "Docker daemon not running" in str(error)
        assert error.details is not None
        assert len(error.suggestions) > 0
        assert any("Start Docker" in s for s in error.suggestions)


class TestDockerConnectionError:
    """Test cases for DockerConnectionError"""

    def test_docker_connection_error(self):
        """Test DockerConnectionError initialization"""
        error = DockerConnectionError()
        
        assert "Cannot connect to Docker daemon" in str(error)
        assert error.details is not None
        assert len(error.suggestions) > 0


class TestDockerComposeError:
    """Test cases for DockerComposeError"""

    def test_docker_compose_error(self):
        """Test DockerComposeError initialization"""
        error = DockerComposeError("Compose file invalid")
        
        assert str(error) == "Compose file invalid"
        assert isinstance(error, DockerError)


class TestContainerError:
    """Test cases for ContainerError"""

    def test_container_error(self):
        """Test ContainerError initialization"""
        error = ContainerError("Container failed to start")
        
        assert str(error) == "Container failed to start"
        assert isinstance(error, DockerError)

    def test_container_error_with_details(self):
        """Test ContainerError with details"""
        error = ContainerError(
            "Container failed",
            details="Exit code: 1",
            suggestions=["Check logs", "Verify configuration"]
        )
        
        assert error.details == "Exit code: 1"
        assert len(error.suggestions) == 2


class TestImageError:
    """Test cases for ImageError"""

    def test_image_error(self):
        """Test ImageError initialization"""
        error = ImageError("Image not found: nginx:latest")
        
        assert "nginx:latest" in str(error)
        assert isinstance(error, DockerError)


class TestNetworkError:
    """Test cases for NetworkError"""

    def test_network_error(self):
        """Test NetworkError initialization"""
        error = NetworkError("Network bridge not found")
        
        assert "bridge" in str(error)
        assert isinstance(error, DockerError)


class TestVolumeError:
    """Test cases for VolumeError"""

    def test_volume_error(self):
        """Test VolumeError initialization"""
        error = VolumeError("Volume data not found")
        
        assert "data" in str(error)
        assert isinstance(error, DockerError)


class TestCreateDockerError:
    """Test cases for create_docker_error function"""

    def test_create_docker_not_found_error(self):
        """Test creating DockerNotFoundError from stderr"""
        stderr = "docker: command not found"
        error = create_docker_error(stderr, "docker ps")
        
        assert isinstance(error, DockerNotFoundError)

    def test_create_docker_not_running_error(self):
        """Test creating DockerNotRunningError from stderr"""
        stderr = "Cannot connect to the Docker daemon at unix:///var/run/docker.sock"
        error = create_docker_error(stderr, "docker ps")
        
        assert isinstance(error, DockerNotRunningError)

    def test_create_docker_connection_error(self):
        """Test creating DockerConnectionError from stderr"""
        stderr = "error during connect: This error may indicate that the docker daemon is not running"
        error = create_docker_error(stderr, "docker ps")
        
        assert isinstance(error, DockerConnectionError)

    def test_create_container_error(self):
        """Test creating ContainerError from stderr"""
        stderr = "Error response from daemon: Container abc123 is not running"
        error = create_docker_error(stderr, "docker stop abc123")
        
        assert isinstance(error, ContainerError)
        assert "abc123" in str(error)

    def test_create_image_error(self):
        """Test creating ImageError from stderr"""
        stderr = "Unable to find image 'nginx:latest' locally"
        error = create_docker_error(stderr, "docker run nginx:latest")
        
        assert isinstance(error, ImageError)
        assert "nginx:latest" in str(error)

    def test_create_network_error(self):
        """Test creating NetworkError from stderr"""
        stderr = "Error response from daemon: network mynet not found"
        error = create_docker_error(stderr, "docker network rm mynet")
        
        assert isinstance(error, NetworkError)
        assert "mynet" in str(error)

    def test_create_volume_error(self):
        """Test creating VolumeError from stderr"""
        stderr = "Error response from daemon: get myvol: no such volume"
        error = create_docker_error(stderr, "docker volume inspect myvol")
        
        assert isinstance(error, VolumeError)
        assert "myvol" in str(error)

    def test_create_compose_error(self):
        """Test creating DockerComposeError from stderr"""
        stderr = "ERROR: The Compose file './docker-compose.yml' is invalid"
        error = create_docker_error(stderr, "docker-compose up")
        
        assert isinstance(error, DockerComposeError)
        assert "invalid" in str(error)

    def test_create_generic_docker_error(self):
        """Test creating generic DockerError for unknown errors"""
        stderr = "Some unexpected error occurred"
        error = create_docker_error(stderr, "docker info")
        
        assert isinstance(error, DockerError)
        assert not isinstance(error, (DockerNotFoundError, DockerNotRunningError, ContainerError))
        assert "Some unexpected error occurred" in str(error)

    def test_create_error_with_empty_stderr(self):
        """Test creating error with empty stderr"""
        error = create_docker_error("", "docker ps")
        
        assert isinstance(error, DockerError)
        assert "Unknown Docker error" in str(error)