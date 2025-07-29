"""
Pytest configuration and fixtures for BlastDock tests
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock
import pytest
import docker

# Add the blastdock package to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from blastdock.models.project import Project, ProjectConfig, ProjectStatus
from blastdock.models.template import Template, TemplateConfig
from blastdock.models.traefik import TraefikInstance, TraefikConfig, TraefikStatus
from blastdock.models.domain import Domain, DomainConfig, DomainType, DomainStatus
from blastdock.models.port import Port, PortAllocation, PortStatus


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_docker_client():
    """Mock Docker client for testing"""
    mock_client = Mock()
    mock_client.ping.return_value = True
    mock_client.containers = Mock()
    mock_client.networks = Mock()
    mock_client.volumes = Mock()
    mock_client.images = Mock()
    
    # Mock container operations
    mock_container = Mock()
    mock_container.id = "test-container-id"
    mock_container.name = "test-container"
    mock_container.status = "running"
    mock_container.image.tags = ["test:latest"]
    mock_container.ports = {"80/tcp": [{"HostPort": "8080"}]}
    mock_container.labels = {}
    mock_container.attrs = {
        'State': {'Status': 'running'},
        'Created': '2024-01-01T00:00:00Z',
        'NetworkSettings': {}
    }
    
    mock_client.containers.list.return_value = [mock_container]
    mock_client.containers.get.return_value = mock_container
    
    # Mock network operations
    mock_network = Mock()
    mock_network.id = "test-network-id"
    mock_network.name = "blastdock-network"
    mock_network.attrs = {'Driver': 'bridge', 'Scope': 'local'}
    
    mock_client.networks.list.return_value = [mock_network]
    mock_client.networks.get.return_value = mock_network
    
    return mock_client


@pytest.fixture
def sample_project_config():
    """Sample project configuration for testing"""
    return ProjectConfig(
        name="test-project",
        template="wordpress",
        services={
            "wordpress": {
                "image": "wordpress:latest",
                "ports": ["8080:80"],
                "environment": {
                    "WORDPRESS_DB_HOST": "mysql",
                    "WORDPRESS_DB_USER": "wordpress",
                    "WORDPRESS_DB_PASSWORD": "password"
                }
            },
            "mysql": {
                "image": "mysql:8.0",
                "environment": {
                    "MYSQL_DATABASE": "wordpress",
                    "MYSQL_USER": "wordpress",
                    "MYSQL_PASSWORD": "password",
                    "MYSQL_ROOT_PASSWORD": "rootpassword"
                }
            }
        },
        environment={
            "WORDPRESS_DB_PASSWORD": "password",
            "MYSQL_ROOT_PASSWORD": "rootpassword"
        },
        ports={
            "wordpress": 8080,
            "mysql": 3306
        }
    )


@pytest.fixture
def sample_project(sample_project_config, temp_dir):
    """Sample project instance for testing"""
    project_path = temp_dir / "test-project"
    project_path.mkdir(exist_ok=True)
    
    return Project(
        config=sample_project_config,
        status=ProjectStatus.CREATED,
        path=str(project_path)
    )


@pytest.fixture
def sample_template_config():
    """Sample template configuration for testing"""
    return TemplateConfig(
        name="wordpress",
        description="WordPress with MySQL database",
        version="1.0",
        category="web",
        services={
            "wordpress": {
                "image": "wordpress:latest",
                "ports": ["${wordpress_port}:80"],
                "environment": {
                    "WORDPRESS_DB_HOST": "mysql",
                    "WORDPRESS_DB_USER": "${mysql_user}",
                    "WORDPRESS_DB_PASSWORD": "${mysql_password}"
                },
                "depends_on": ["mysql"]
            },
            "mysql": {
                "image": "mysql:8.0",
                "environment": {
                    "MYSQL_DATABASE": "${mysql_database}",
                    "MYSQL_USER": "${mysql_user}",
                    "MYSQL_PASSWORD": "${mysql_password}",
                    "MYSQL_ROOT_PASSWORD": "${mysql_root_password}"
                },
                "volumes": ["mysql_data:/var/lib/mysql"]
            }
        },
        fields={
            "wordpress_port": {
                "name": "wordpress_port",
                "type": "port",
                "description": "WordPress HTTP port",
                "default": 8080,
                "required": True
            },
            "mysql_user": {
                "name": "mysql_user",
                "type": "string",
                "description": "MySQL username",
                "default": "wordpress",
                "required": True
            },
            "mysql_password": {
                "name": "mysql_password",
                "type": "password",
                "description": "MySQL password",
                "required": True
            }
        }
    )


@pytest.fixture
def sample_template(sample_template_config, temp_dir):
    """Sample template instance for testing"""
    template_path = temp_dir / "wordpress.yml"
    
    return Template(
        config=sample_template_config,
        file_path=str(template_path),
        is_valid=True
    )


@pytest.fixture
def sample_traefik_config():
    """Sample Traefik configuration for testing"""
    return TraefikConfig(
        email="test@example.com",
        default_domain="example.com",
        dashboard_enabled=True,
        ssl_enabled=True
    )


@pytest.fixture
def sample_traefik_instance(sample_traefik_config):
    """Sample Traefik instance for testing"""
    return TraefikInstance(
        config=sample_traefik_config,
        status=TraefikStatus.RUNNING,
        container_id="traefik-container-id",
        network_exists=True,
        dashboard_accessible=True
    )


@pytest.fixture
def sample_domain_config():
    """Sample domain configuration for testing"""
    return DomainConfig(
        domain="test.example.com",
        type=DomainType.SUBDOMAIN,
        project="test-project",
        ssl_enabled=True
    )


@pytest.fixture
def sample_domain(sample_domain_config):
    """Sample domain instance for testing"""
    return Domain(
        config=sample_domain_config,
        status=DomainStatus.IN_USE,
        resolved_ip="192.168.1.1",
        dns_propagated=True,
        ssl_valid=True
    )


@pytest.fixture
def sample_port_allocation():
    """Sample port allocation for testing"""
    return PortAllocation(
        port=8080,
        project="test-project",
        service="wordpress",
        in_use=True,
        description="WordPress HTTP port"
    )


@pytest.fixture
def sample_port(sample_port_allocation):
    """Sample port instance for testing"""
    return Port(
        number=8080,
        status=PortStatus.IN_USE,
        allocation=sample_port_allocation,
        is_listening=True
    )


@pytest.fixture
def mock_subprocess():
    """Mock subprocess for testing external commands"""
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = "success"
    mock_result.stderr = ""
    
    with pytest.mock.patch('subprocess.run', return_value=mock_result) as mock:
        yield mock


@pytest.fixture
def mock_requests():
    """Mock requests for testing HTTP operations"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {'content-type': 'application/json'}
    mock_response.json.return_value = {'status': 'ok'}
    mock_response.text = '{"status": "ok"}'
    mock_response.elapsed.total_seconds.return_value = 0.1
    
    with pytest.mock.patch('requests.get', return_value=mock_response) as mock_get, \
         pytest.mock.patch('requests.post', return_value=mock_response) as mock_post, \
         pytest.mock.patch('requests.head', return_value=mock_response) as mock_head:
        yield {
            'get': mock_get,
            'post': mock_post,
            'head': mock_head,
            'response': mock_response
        }


@pytest.fixture
def mock_dns():
    """Mock DNS resolution for testing"""
    with pytest.mock.patch('socket.gethostbyname', return_value='192.168.1.1') as mock:
        yield mock


@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Cleanup test files after each test"""
    yield
    # Clean up any test files created during tests
    test_files = [
        'test-project',
        'test_deploys',
        '.test_blastdock'
    ]
    
    for file_path in test_files:
        if os.path.exists(file_path):
            if os.path.isdir(file_path):
                shutil.rmtree(file_path, ignore_errors=True)
            else:
                os.remove(file_path)


# Test markers
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "docker: mark test as requiring Docker"
    )
    config.addinivalue_line(
        "markers", "network: mark test as requiring network access"
    )


# Skip tests based on environment
def pytest_collection_modifyitems(config, items):
    """Modify test collection based on environment"""
    # Skip Docker tests if Docker is not available
    try:
        docker.from_env().ping()
        docker_available = True
    except:
        docker_available = False
    
    if not docker_available:
        skip_docker = pytest.mark.skip(reason="Docker not available")
        for item in items:
            if "docker" in item.keywords:
                item.add_marker(skip_docker)
    
    # Skip network tests if running in CI without network
    if os.getenv('CI') and not os.getenv('ALLOW_NETWORK_TESTS'):
        skip_network = pytest.mark.skip(reason="Network tests disabled in CI")
        for item in items:
            if "network" in item.keywords:
                item.add_marker(skip_network)