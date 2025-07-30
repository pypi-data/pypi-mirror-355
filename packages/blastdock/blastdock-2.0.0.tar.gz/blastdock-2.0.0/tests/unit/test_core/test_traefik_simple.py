"""
Simplified working Traefik tests
"""

import pytest
from unittest.mock import Mock, patch

@patch('blastdock.core.traefik.get_config')
def test_traefik_integrator_imports(mock_config):
    """Test that TraefikIntegrator can be imported and initialized"""
    mock_config.return_value = Mock()
    
    from blastdock.core.traefik import TraefikIntegrator
    integrator = TraefikIntegrator()
    assert integrator is not None

@patch('blastdock.core.traefik.get_config')
def test_traefik_process_compose_basic(mock_config):
    """Test basic compose processing"""
    mock_config.return_value = Mock()
    
    from blastdock.core.traefik import TraefikIntegrator
    integrator = TraefikIntegrator()
    
    compose_data = {'version': '3.8', 'services': {'web': {'image': 'nginx'}}}
    result = integrator.process_compose(compose_data, 'test', {}, {})
    
    assert 'services' in result
    assert 'web' in result['services']

@patch('blastdock.core.traefik.get_config')
def test_traefik_should_enable(mock_config):
    """Test Traefik enablement logic"""
    mock_config.return_value = Mock()
    
    from blastdock.core.traefik import TraefikIntegrator
    integrator = TraefikIntegrator()
    
    # Service with ports
    service_with_ports = {'image': 'nginx', 'ports': ['80:80']}
    result = integrator._should_enable_traefik(service_with_ports)
    assert isinstance(result, bool)
    
    # Service without ports
    service_without_ports = {'image': 'mysql'}
    result = integrator._should_enable_traefik(service_without_ports)
    assert result is False

@patch('blastdock.core.traefik.get_config')
def test_traefik_extract_port(mock_config):
    """Test port extraction"""
    mock_config.return_value = Mock()
    
    from blastdock.core.traefik import TraefikIntegrator
    integrator = TraefikIntegrator()
    
    # Service with port mapping
    service = {'ports': ['8080:80']}
    port = integrator._extract_port_from_service(service)
    assert port == 80
    
    # Service without ports
    service_no_ports = {'image': 'nginx'}
    port = integrator._extract_port_from_service(service_no_ports)
    assert port is None
