"""
Integration tests for complete deployment workflows
"""

import pytest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import Mock, patch

from blastdock.cli.main import cli
from blastdock.utils.project_utils import ProjectManager
from blastdock.traefik.manager import TraefikManager
from blastdock.domains.manager import DomainManager
from blastdock.ports.manager import PortManager


@pytest.mark.integration
class TestBasicDeploymentWorkflow:
    """Test basic deployment workflow without Traefik"""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for tests"""
        temp_dir = tempfile.mkdtemp()
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        yield Path(temp_dir)
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @patch('blastdock.utils.docker_utils.DockerClient')
    @patch('blastdock.utils.template_utils.TemplateManager')
    def test_complete_basic_workflow(self, mock_template_manager, mock_docker_client, temp_workspace):
        """Test complete workflow: init -> deploy -> status -> stop"""
        from click.testing import CliRunner
        
        # Setup mocks
        mock_template = Mock()
        mock_template.name = 'wordpress'
        mock_template.get_service_names.return_value = ['wordpress', 'mysql']
        mock_template_manager.return_value.get_template.return_value = mock_template
        mock_template_manager.return_value.get_available_templates.return_value = [mock_template]
        
        mock_docker_client.return_value.is_running.return_value = True
        mock_docker_client.return_value.run_compose.return_value = True
        
        runner = CliRunner()
        
        # Step 1: Initialize project
        result = runner.invoke(cli, [
            'init',
            '--name', 'test-project',
            '--template', 'wordpress',
            '--no-interactive'
        ])
        
        assert result.exit_code == 0
        assert 'test-project' in result.output
        
        # Verify project structure was created
        assert (temp_workspace / 'test-project').exists()
        assert (temp_workspace / 'test-project' / 'docker-compose.yml').exists()
        
        # Step 2: Deploy project
        os.chdir(temp_workspace / 'test-project')
        
        result = runner.invoke(cli, ['deploy'])
        
        assert result.exit_code == 0
        
        # Step 3: Check status
        result = runner.invoke(cli, ['status'])
        
        assert result.exit_code == 0
        
        # Step 4: Stop project
        result = runner.invoke(cli, ['stop'])
        
        assert result.exit_code == 0


@pytest.mark.integration
@pytest.mark.docker
class TestTraefikDeploymentWorkflow:
    """Test deployment workflow with Traefik integration"""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for tests"""
        temp_dir = tempfile.mkdtemp()
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        yield Path(temp_dir)
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @patch('blastdock.utils.docker_utils.DockerClient')
    @patch('blastdock.utils.template_utils.TemplateManager')
    @patch('blastdock.traefik.manager.TraefikManager')
    @patch('blastdock.domains.manager.DomainManager')
    @patch('blastdock.ports.manager.PortManager')
    def test_complete_traefik_workflow(self, mock_port_manager, mock_domain_manager, 
                                     mock_traefik_manager, mock_template_manager, 
                                     mock_docker_client, temp_workspace):
        """Test complete workflow with Traefik: install traefik -> init project -> deploy"""
        from click.testing import CliRunner
        
        # Setup mocks
        mock_template = Mock()
        mock_template.name = 'wordpress'
        mock_template.supports_traefik.return_value = True
        mock_template_manager.return_value.get_template.return_value = mock_template
        
        mock_docker_client.return_value.is_running.return_value = True
        mock_docker_client.return_value.run_compose.return_value = True
        
        mock_traefik_manager.return_value.is_installed.return_value = False
        mock_traefik_manager.return_value.install.return_value = True
        mock_traefik_manager.return_value.is_running.return_value = True
        
        mock_domain_manager.return_value.validate_domain.return_value = True
        mock_domain_manager.return_value.add_domain.return_value = True
        
        mock_port_manager.return_value.allocate_port.return_value = 8080
        mock_port_manager.return_value.is_port_available.return_value = True
        
        runner = CliRunner()
        
        # Step 1: Install Traefik
        result = runner.invoke(cli, [
            'traefik', 'install',
            '--email', 'test@example.com',
            '--domain', 'example.com'
        ])
        
        assert result.exit_code == 0
        mock_traefik_manager.return_value.install.assert_called_once()
        
        # Step 2: Initialize project with Traefik
        result = runner.invoke(cli, [
            'init',
            '--name', 'test-project',
            '--template', 'wordpress',
            '--domain', 'test.example.com',
            '--traefik',
            '--no-interactive'
        ])
        
        assert result.exit_code == 0
        
        # Verify Traefik labels were added
        compose_file = temp_workspace / 'test-project' / 'docker-compose.yml'
        assert compose_file.exists()
        
        # Step 3: Deploy with Traefik
        os.chdir(temp_workspace / 'test-project')
        
        result = runner.invoke(cli, ['deploy'])
        
        assert result.exit_code == 0
        
        # Step 4: Check Traefik status
        result = runner.invoke(cli, ['traefik', 'status'])
        
        assert result.exit_code == 0
    
    @patch('blastdock.utils.docker_utils.DockerClient')
    @patch('blastdock.traefik.manager.TraefikManager')
    def test_traefik_ssl_workflow(self, mock_traefik_manager, mock_docker_client, temp_workspace):
        """Test SSL certificate management workflow"""
        from click.testing import CliRunner
        
        # Setup mocks
        mock_docker_client.return_value.is_running.return_value = True
        mock_traefik_manager.return_value.is_running.return_value = True
        
        mock_ssl_manager = Mock()
        mock_ssl_manager.certificate_exists.return_value = False
        mock_ssl_manager.request_certificate.return_value = True
        mock_traefik_manager.return_value.ssl_manager = mock_ssl_manager
        
        runner = CliRunner()
        
        # Request SSL certificate
        result = runner.invoke(cli, [
            'traefik', 'ssl', 'request',
            '--domain', 'test.example.com',
            '--email', 'test@example.com'
        ])
        
        assert result.exit_code == 0
        
        # List SSL certificates
        result = runner.invoke(cli, ['traefik', 'ssl', 'list'])
        
        assert result.exit_code == 0


@pytest.mark.integration
@pytest.mark.network
class TestDomainManagementWorkflow:
    """Test domain management workflow"""
    
    @patch('blastdock.domains.manager.DomainManager')
    @patch('blastdock.domains.validator.DomainValidator')
    def test_domain_lifecycle_workflow(self, mock_validator, mock_domain_manager):
        """Test complete domain lifecycle: add -> validate -> configure -> remove"""
        from click.testing import CliRunner
        
        # Setup mocks
        mock_validator.return_value.validate_domain.return_value = True
        mock_validator.return_value.check_dns_resolution.return_value = True
        
        mock_domain = Mock()
        mock_domain.config.domain = 'test.example.com'
        mock_domain.status = 'available'
        mock_domain_manager.return_value.add_domain.return_value = True
        mock_domain_manager.return_value.list_domains.return_value = [mock_domain]
        mock_domain_manager.return_value.remove_domain.return_value = True
        
        runner = CliRunner()
        
        # Step 1: Add domain
        result = runner.invoke(cli, [
            'domain', 'add',
            'test.example.com',
            '--project', 'test-project'
        ])
        
        assert result.exit_code == 0
        mock_domain_manager.return_value.add_domain.assert_called()
        
        # Step 2: Validate domain
        result = runner.invoke(cli, [
            'domain', 'validate',
            'test.example.com'
        ])
        
        assert result.exit_code == 0
        
        # Step 3: List domains
        result = runner.invoke(cli, ['domain', 'list'])
        
        assert result.exit_code == 0
        assert 'test.example.com' in result.output
        
        # Step 4: Remove domain
        result = runner.invoke(cli, [
            'domain', 'remove',
            'test.example.com'
        ])
        
        assert result.exit_code == 0
        mock_domain_manager.return_value.remove_domain.assert_called()


@pytest.mark.integration
class TestPortManagementWorkflow:
    """Test port management workflow"""
    
    @patch('blastdock.ports.manager.PortManager')
    def test_port_lifecycle_workflow(self, mock_port_manager):
        """Test complete port lifecycle: allocate -> check -> release"""
        from click.testing import CliRunner
        
        # Setup mocks
        mock_port = Mock()
        mock_port.number = 8080
        mock_port.status = 'available'
        mock_port_manager.return_value.allocate_port.return_value = 8080
        mock_port_manager.return_value.list_ports.return_value = [mock_port]
        mock_port_manager.return_value.is_port_available.return_value = True
        mock_port_manager.return_value.release_port.return_value = True
        
        runner = CliRunner()
        
        # Step 1: Check port availability
        result = runner.invoke(cli, ['port', 'check', '8080'])
        
        assert result.exit_code == 0
        
        # Step 2: Allocate port
        result = runner.invoke(cli, [
            'port', 'allocate',
            '--project', 'test-project',
            '--service', 'web'
        ])
        
        assert result.exit_code == 0
        mock_port_manager.return_value.allocate_port.assert_called()
        
        # Step 3: List ports
        result = runner.invoke(cli, ['port', 'list'])
        
        assert result.exit_code == 0
        
        # Step 4: Release port
        result = runner.invoke(cli, ['port', 'release', '8080'])
        
        assert result.exit_code == 0
        mock_port_manager.return_value.release_port.assert_called()


@pytest.mark.integration
@pytest.mark.slow
class TestMigrationWorkflow:
    """Test migration workflow for existing projects"""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace with existing project"""
        temp_dir = tempfile.mkdtemp()
        original_cwd = os.getcwd()
        
        # Create existing project structure
        project_dir = Path(temp_dir) / 'existing-project'
        project_dir.mkdir()
        
        # Create basic docker-compose.yml
        compose_content = """
version: '3.8'
services:
  web:
    image: nginx:latest
    ports:
      - "8080:80"
"""
        (project_dir / 'docker-compose.yml').write_text(compose_content)
        
        os.chdir(temp_dir)
        yield Path(temp_dir)
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @patch('blastdock.utils.docker_utils.DockerClient')
    @patch('blastdock.traefik.manager.TraefikManager')
    @patch('blastdock.migration.migrator.TraefikMigrator')
    def test_traefik_migration_workflow(self, mock_migrator, mock_traefik_manager, 
                                      mock_docker_client, temp_workspace):
        """Test migrating existing project to Traefik"""
        from click.testing import CliRunner
        
        # Setup mocks
        mock_docker_client.return_value.is_running.return_value = True
        mock_traefik_manager.return_value.is_running.return_value = True
        
        mock_migrator.return_value.can_migrate.return_value = True
        mock_migrator.return_value.create_backup.return_value = True
        mock_migrator.return_value.migrate_project.return_value = True
        
        runner = CliRunner()
        
        # Change to existing project directory
        os.chdir(temp_workspace / 'existing-project')
        
        # Step 1: Check migration compatibility
        result = runner.invoke(cli, ['migrate', 'check'])
        
        assert result.exit_code == 0
        
        # Step 2: Create backup
        result = runner.invoke(cli, ['migrate', 'backup'])
        
        assert result.exit_code == 0
        mock_migrator.return_value.create_backup.assert_called()
        
        # Step 3: Migrate to Traefik
        result = runner.invoke(cli, [
            'migrate', 'to-traefik',
            '--domain', 'existing.example.com'
        ])
        
        assert result.exit_code == 0
        mock_migrator.return_value.migrate_project.assert_called()


@pytest.mark.integration
class TestErrorRecoveryWorkflow:
    """Test error recovery and rollback workflows"""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for tests"""
        temp_dir = tempfile.mkdtemp()
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        yield Path(temp_dir)
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @patch('blastdock.utils.docker_utils.DockerClient')
    @patch('blastdock.utils.template_utils.TemplateManager')
    def test_deployment_failure_recovery(self, mock_template_manager, mock_docker_client, temp_workspace):
        """Test recovery from deployment failures"""
        from click.testing import CliRunner
        
        # Setup mocks
        mock_template = Mock()
        mock_template.name = 'wordpress'
        mock_template_manager.return_value.get_template.return_value = mock_template
        
        mock_docker_client.return_value.is_running.return_value = True
        mock_docker_client.return_value.run_compose.side_effect = Exception("Deployment failed")
        
        runner = CliRunner()
        
        # Initialize project
        result = runner.invoke(cli, [
            'init',
            '--name', 'test-project',
            '--template', 'wordpress',
            '--no-interactive'
        ])
        
        assert result.exit_code == 0
        
        # Attempt deployment (should fail)
        os.chdir(temp_workspace / 'test-project')
        
        result = runner.invoke(cli, ['deploy'])
        
        assert result.exit_code != 0
        
        # Test cleanup after failure
        result = runner.invoke(cli, ['cleanup'])
        
        # Should handle gracefully
        assert result.exit_code == 0 or "cleanup" in result.output.lower()
    
    @patch('blastdock.traefik.manager.TraefikManager')
    def test_traefik_recovery_workflow(self, mock_traefik_manager):
        """Test recovery from Traefik issues"""
        from click.testing import CliRunner
        
        # Setup mocks for failed Traefik
        mock_traefik_manager.return_value.is_running.return_value = False
        mock_traefik_manager.return_value.start.return_value = False
        mock_traefik_manager.return_value.restart.return_value = True
        
        runner = CliRunner()
        
        # Check Traefik status (should show not running)
        result = runner.invoke(cli, ['traefik', 'status'])
        
        assert result.exit_code == 0
        
        # Try to start (should fail)
        result = runner.invoke(cli, ['traefik', 'start'])
        
        # May fail but should handle gracefully
        
        # Try restart (should succeed)
        result = runner.invoke(cli, ['traefik', 'restart'])
        
        assert result.exit_code == 0
        mock_traefik_manager.return_value.restart.assert_called()


@pytest.mark.integration
@pytest.mark.performance
class TestPerformanceWorkflow:
    """Test performance aspects of workflows"""
    
    @patch('blastdock.utils.template_utils.TemplateManager')
    def test_template_loading_performance(self, mock_template_manager):
        """Test template loading performance"""
        from click.testing import CliRunner
        import time
        
        # Create many mock templates
        mock_templates = []
        for i in range(100):
            template = Mock()
            template.name = f'template-{i}'
            template.description = f'Template {i}'
            mock_templates.append(template)
        
        mock_template_manager.return_value.get_available_templates.return_value = mock_templates
        
        runner = CliRunner()
        
        # Measure template listing time
        start_time = time.time()
        
        result = runner.invoke(cli, ['templates'])
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert result.exit_code == 0
        assert duration < 5.0  # Should complete within 5 seconds
    
    @patch('blastdock.utils.docker_utils.DockerClient')
    def test_container_operations_performance(self, mock_docker_client):
        """Test container operations performance"""
        from click.testing import CliRunner
        import time
        
        mock_docker_client.return_value.is_running.return_value = True
        mock_docker_client.return_value.list_containers.return_value = []
        
        runner = CliRunner()
        
        # Measure status check time
        start_time = time.time()
        
        result = runner.invoke(cli, ['status'])
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert result.exit_code == 0
        assert duration < 3.0  # Should complete within 3 seconds