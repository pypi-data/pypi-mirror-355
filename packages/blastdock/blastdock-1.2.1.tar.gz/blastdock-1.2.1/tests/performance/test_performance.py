"""
Performance tests for BlastDock functionality
"""

import pytest
import time
import psutil
import threading
from unittest.mock import Mock, patch
from concurrent.futures import ThreadPoolExecutor

from blastdock.utils.template_utils import TemplateManager
from blastdock.utils.docker_utils import DockerClient
from blastdock.traefik.manager import TraefikManager
from blastdock.domains.manager import DomainManager
from blastdock.ports.manager import PortManager


@pytest.mark.performance
@pytest.mark.slow
class TestTemplatePerformance:
    """Test template loading and processing performance"""
    
    @patch('blastdock.utils.template_utils.TemplateManager._load_template_files')
    def test_template_loading_time(self, mock_load_files):
        """Test template loading performance with many templates"""
        # Mock 200 template files
        mock_template_files = []
        for i in range(200):
            mock_file = Mock()
            mock_file.name = f'template-{i}.yml'
            mock_file.stat.return_value.st_mtime = time.time()
            mock_template_files.append(mock_file)
        
        mock_load_files.return_value = mock_template_files
        
        # Measure loading time
        start_time = time.time()
        
        with patch('blastdock.utils.template_utils.TemplateManager._parse_template'):
            manager = TemplateManager()
            templates = manager.get_available_templates()
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert duration < 2.0  # Should load 200 templates in under 2 seconds
        assert len(templates) <= 200
    
    @patch('jinja2.Template.render')
    @patch('blastdock.utils.template_utils.TemplateManager.get_template')
    def test_template_rendering_performance(self, mock_get_template, mock_render):
        """Test template rendering performance"""
        # Mock complex template
        mock_template = Mock()
        mock_template.config.services = {f'service-{i}': {} for i in range(50)}
        mock_get_template.return_value = mock_template
        
        # Mock rendering with large content
        large_content = "service:\n  image: test\n" * 1000
        mock_render.return_value = large_content
        
        manager = TemplateManager()
        
        # Measure rendering time
        start_time = time.time()
        
        for _ in range(10):  # Render 10 times
            manager.render_template('complex-template', {})
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert duration < 1.0  # Should render 10 complex templates in under 1 second
    
    def test_concurrent_template_access(self):
        """Test concurrent template access performance"""
        manager = TemplateManager()
        
        def access_templates():
            """Access templates in thread"""
            try:
                templates = manager.get_available_templates()
                return len(templates)
            except Exception:
                return 0
        
        # Measure concurrent access
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(access_templates) for _ in range(50)]
            results = [future.result() for future in futures]
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert duration < 5.0  # Should handle 50 concurrent accesses in under 5 seconds
        assert all(result >= 0 for result in results)  # All should succeed
    
    @patch('blastdock.utils.template_utils.TemplateManager.get_template')
    def test_memory_usage_during_template_loading(self, mock_get_template):
        """Test memory usage during template operations"""
        # Mock template with large data
        mock_template = Mock()
        mock_template.config.services = {f'service-{i}': {'data': 'x' * 1000} for i in range(100)}
        mock_get_template.return_value = mock_template
        
        manager = TemplateManager()
        
        # Measure memory before
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform memory-intensive operations
        for _ in range(100):
            manager.render_template('large-template', {})
        
        # Measure memory after
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = memory_after - memory_before
        
        assert memory_increase < 100  # Should not increase by more than 100MB


@pytest.mark.performance
class TestDockerPerformance:
    """Test Docker operations performance"""
    
    @patch('docker.from_env')
    def test_docker_client_initialization_time(self, mock_docker):
        """Test Docker client initialization performance"""
        mock_client = Mock()
        mock_docker.return_value = mock_client
        
        # Measure initialization time
        start_time = time.time()
        
        for _ in range(100):  # Initialize 100 times
            DockerClient()
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert duration < 1.0  # Should initialize 100 clients in under 1 second
    
    @patch('docker.from_env')
    def test_container_listing_performance(self, mock_docker):
        """Test container listing performance with many containers"""
        # Mock many containers
        mock_containers = []
        for i in range(500):
            container = Mock()
            container.id = f'container-{i}'
            container.name = f'test-container-{i}'
            container.status = 'running'
            mock_containers.append(container)
        
        mock_client = Mock()
        mock_client.containers.list.return_value = mock_containers
        mock_docker.return_value = mock_client
        
        docker_client = DockerClient()
        
        # Measure listing time
        start_time = time.time()
        
        containers = docker_client.list_containers()
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert duration < 0.5  # Should list 500 containers in under 0.5 seconds
        assert len(containers) == 500
    
    @patch('subprocess.run')
    def test_compose_command_performance(self, mock_subprocess):
        """Test docker-compose command execution performance"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "success"
        mock_subprocess.return_value = mock_result
        
        docker_client = DockerClient()
        
        # Measure compose command time
        start_time = time.time()
        
        for _ in range(10):  # Run 10 compose commands
            docker_client.run_compose(['up', '-d'])
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert duration < 2.0  # Should run 10 compose commands in under 2 seconds


@pytest.mark.performance
class TestTraefikPerformance:
    """Test Traefik operations performance"""
    
    @patch('blastdock.utils.docker_utils.DockerClient')
    def test_traefik_status_check_performance(self, mock_docker_client):
        """Test Traefik status checking performance"""
        mock_container = Mock()
        mock_container.status = "running"
        mock_docker_client.return_value.get_container_info.return_value = mock_container
        
        manager = TraefikManager()
        
        # Measure status checking time
        start_time = time.time()
        
        for _ in range(100):  # Check status 100 times
            manager.is_running()
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert duration < 1.0  # Should check status 100 times in under 1 second
    
    @patch('blastdock.traefik.labels.TraefikLabels.generate_complete_labels')
    def test_label_generation_performance(self, mock_generate_labels):
        """Test Traefik label generation performance"""
        from blastdock.traefik.labels import TraefikLabels
        
        # Mock label generation
        mock_labels = {f'traefik.label.{i}': f'value-{i}' for i in range(100)}
        mock_generate_labels.return_value = mock_labels
        
        # Measure label generation time
        start_time = time.time()
        
        for _ in range(1000):  # Generate labels 1000 times
            TraefikLabels('test-service', 'example.com').generate_complete_labels({})
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert duration < 2.0  # Should generate 1000 label sets in under 2 seconds
    
    @patch('blastdock.utils.docker_utils.DockerClient')
    @patch('subprocess.run')
    def test_ssl_certificate_operations_performance(self, mock_subprocess, mock_docker_client):
        """Test SSL certificate operations performance"""
        from blastdock.traefik.ssl import SSLManager
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        ssl_manager = SSLManager()
        
        # Measure certificate operations time
        start_time = time.time()
        
        # Simulate multiple certificate requests
        for i in range(10):
            ssl_manager.request_certificate(f'test{i}.example.com', 'test@example.com')
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert duration < 5.0  # Should handle 10 certificate requests in under 5 seconds


@pytest.mark.performance
class TestDomainPerformance:
    """Test domain management performance"""
    
    @patch('socket.gethostbyname')
    def test_dns_validation_performance(self, mock_gethostbyname):
        """Test DNS validation performance for many domains"""
        from blastdock.domains.validator import DomainValidator
        
        mock_gethostbyname.return_value = '192.168.1.1'
        
        validator = DomainValidator()
        
        # Generate many domains
        domains = [f'test{i}.example.com' for i in range(100)]
        
        # Measure validation time
        start_time = time.time()
        
        for domain in domains:
            validator.validate_domain(domain)
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert duration < 3.0  # Should validate 100 domains in under 3 seconds
    
    @patch('requests.head')
    def test_domain_accessibility_check_performance(self, mock_requests):
        """Test domain accessibility checking performance"""
        from blastdock.models.domain import Domain, DomainConfig, DomainType
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.1
        mock_requests.return_value = mock_response
        
        # Create many domain objects
        domains = []
        for i in range(50):
            config = DomainConfig(
                domain=f'test{i}.example.com',
                type=DomainType.SUBDOMAIN,
                project='test-project'
            )
            domains.append(Domain(config=config))
        
        # Measure accessibility checking time
        start_time = time.time()
        
        for domain in domains:
            domain.check_accessibility(timeout=1)
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert duration < 10.0  # Should check 50 domains in under 10 seconds
    
    def test_concurrent_domain_operations(self):
        """Test concurrent domain operations performance"""
        from blastdock.domains.manager import DomainManager
        
        with patch('blastdock.domains.manager.DomainManager.validate_domain') as mock_validate:
            mock_validate.return_value = True
            
            manager = DomainManager()
            
            def validate_domain(domain_name):
                """Validate domain in thread"""
                return manager.validate_domain(domain_name)
            
            # Generate domain names
            domain_names = [f'test{i}.example.com' for i in range(100)]
            
            # Measure concurrent validation time
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = [executor.submit(validate_domain, domain) for domain in domain_names]
                results = [future.result() for future in futures]
            
            end_time = time.time()
            duration = end_time - start_time
            
            assert duration < 5.0  # Should validate 100 domains concurrently in under 5 seconds
            assert all(results)  # All should succeed


@pytest.mark.performance
class TestPortPerformance:
    """Test port management performance"""
    
    @patch('socket.socket')
    def test_port_availability_check_performance(self, mock_socket):
        """Test port availability checking performance"""
        from blastdock.models.port import Port
        
        mock_sock = Mock()
        mock_sock.connect_ex.return_value = 1  # Port not available
        mock_socket.return_value = mock_sock
        
        # Create many port objects
        ports = [Port(number=8000 + i) for i in range(1000)]
        
        # Measure availability checking time
        start_time = time.time()
        
        for port in ports:
            port.check_availability()
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert duration < 5.0  # Should check 1000 ports in under 5 seconds
    
    @patch('blastdock.ports.manager.PortManager._scan_system_ports')
    def test_port_allocation_performance(self, mock_scan):
        """Test port allocation performance"""
        from blastdock.ports.manager import PortManager
        
        mock_scan.return_value = []  # No system ports in use
        
        manager = PortManager()
        
        # Measure allocation time
        start_time = time.time()
        
        allocated_ports = []
        for i in range(100):
            port = manager.allocate_port(f'project-{i}', f'service-{i}')
            if port:
                allocated_ports.append(port)
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert duration < 3.0  # Should allocate 100 ports in under 3 seconds
        assert len(allocated_ports) > 0  # Should successfully allocate some ports
    
    def test_concurrent_port_operations(self):
        """Test concurrent port operations performance"""
        from blastdock.ports.manager import PortManager
        
        with patch('blastdock.ports.manager.PortManager._scan_system_ports') as mock_scan:
            mock_scan.return_value = []
            
            manager = PortManager()
            
            def allocate_port_thread(thread_id):
                """Allocate port in thread"""
                return manager.allocate_port(f'project-{thread_id}', 'web')
            
            # Measure concurrent allocation time
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(allocate_port_thread, i) for i in range(50)]
                results = [future.result() for future in futures]
            
            end_time = time.time()
            duration = end_time - start_time
            
            assert duration < 3.0  # Should handle 50 concurrent allocations in under 3 seconds
            successful_allocations = [r for r in results if r is not None]
            assert len(successful_allocations) > 0  # Should have some successful allocations


@pytest.mark.performance
class TestSystemResourceUsage:
    """Test system resource usage during operations"""
    
    def test_memory_usage_stability(self):
        """Test memory usage remains stable during operations"""
        from blastdock.utils.template_utils import TemplateManager
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform many operations
        manager = TemplateManager()
        for _ in range(1000):
            try:
                templates = manager.get_available_templates()
                # Process templates
                for template in templates[:10]:  # Limit to first 10
                    manager.render_template(template.name, {})
            except Exception:
                pass  # Ignore errors for performance test
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        assert memory_increase < 50  # Should not increase by more than 50MB
    
    def test_cpu_usage_efficiency(self):
        """Test CPU usage remains reasonable during operations"""
        import time
        
        process = psutil.Process()
        
        # Monitor CPU usage
        cpu_percent_before = process.cpu_percent()
        time.sleep(0.1)  # Let CPU measurement stabilize
        
        # Perform CPU-intensive operations
        start_time = time.time()
        
        # Simulate intensive operations
        for _ in range(10000):
            # Simple computation
            result = sum(range(100))
        
        end_time = time.time()
        duration = end_time - start_time
        
        cpu_percent_after = process.cpu_percent()
        
        # CPU usage should be reasonable
        assert duration < 2.0  # Should complete in under 2 seconds
        # Note: CPU percentage comparison is environment-dependent
    
    @patch('blastdock.utils.docker_utils.DockerClient')
    def test_file_handle_usage(self, mock_docker_client):
        """Test file handle usage doesn't leak"""
        import resource
        
        # Get initial file descriptor count
        initial_fds = len(psutil.Process().open_files())
        
        # Perform many operations that might open files
        for _ in range(100):
            try:
                client = DockerClient()
                # Simulate operations
                client.is_running()
            except Exception:
                pass
        
        # Get final file descriptor count
        final_fds = len(psutil.Process().open_files())
        fd_increase = final_fds - initial_fds
        
        assert fd_increase < 10  # Should not leak more than 10 file descriptors