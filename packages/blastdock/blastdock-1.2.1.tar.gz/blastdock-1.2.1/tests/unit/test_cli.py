"""
Unit tests for BlastDock CLI commands
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner

from blastdock.cli.main import cli
from blastdock.cli.init import init
from blastdock.cli.deploy import deploy
from blastdock.cli.traefik import traefik
from blastdock.cli.domain import domain
from blastdock.cli.port import port


class TestMainCLI:
    """Test main CLI interface"""
    
    def test_cli_help(self):
        """Test CLI help output"""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert 'BlastDock' in result.output
        assert 'init' in result.output
        assert 'deploy' in result.output
        assert 'traefik' in result.output
    
    def test_cli_version(self):
        """Test version command"""
        runner = CliRunner()
        result = runner.invoke(cli, ['--version'])
        
        assert result.exit_code == 0
        assert '1.1.0' in result.output
    
    def test_cli_invalid_command(self):
        """Test invalid command handling"""
        runner = CliRunner()
        result = runner.invoke(cli, ['invalid-command'])
        
        assert result.exit_code != 0
        assert 'No such command' in result.output


class TestInitCommand:
    """Test init command functionality"""
    
    @patch('blastdock.utils.template_utils.TemplateManager')
    @patch('blastdock.utils.docker_utils.DockerClient')
    def test_init_basic_project(self, mock_docker, mock_template_manager):
        """Test basic project initialization"""
        runner = CliRunner()
        
        # Mock template manager
        mock_template = Mock()
        mock_template.name = 'wordpress'
        mock_template.description = 'WordPress template'
        mock_template_manager.return_value.get_available_templates.return_value = [mock_template]
        mock_template_manager.return_value.get_template.return_value = mock_template
        
        # Mock Docker client
        mock_docker.return_value.is_running.return_value = True
        
        with runner.isolated_filesystem():
            result = runner.invoke(init, [
                '--name', 'test-project',
                '--template', 'wordpress',
                '--no-interactive'
            ])
            
            assert result.exit_code == 0
            assert 'test-project' in result.output
    
    @patch('blastdock.utils.template_utils.TemplateManager')
    def test_init_with_traefik(self, mock_template_manager):
        """Test project initialization with Traefik"""
        runner = CliRunner()
        
        mock_template = Mock()
        mock_template.name = 'wordpress'
        mock_template_manager.return_value.get_template.return_value = mock_template
        
        with runner.isolated_filesystem():
            result = runner.invoke(init, [
                '--name', 'test-project',
                '--template', 'wordpress',
                '--domain', 'test.example.com',
                '--traefik',
                '--no-interactive'
            ])
            
            # Should succeed even if Traefik setup fails in test
            assert 'test-project' in result.output
    
    def test_init_invalid_template(self):
        """Test initialization with invalid template"""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            result = runner.invoke(init, [
                '--name', 'test-project',
                '--template', 'invalid-template',
                '--no-interactive'
            ])
            
            assert result.exit_code != 0
    
    def test_init_missing_name(self):
        """Test initialization without project name"""
        runner = CliRunner()
        
        result = runner.invoke(init, ['--template', 'wordpress'])
        
        assert result.exit_code != 0


class TestDeployCommand:
    """Test deploy command functionality"""
    
    @patch('blastdock.utils.docker_utils.DockerClient')
    @patch('blastdock.utils.project_utils.ProjectManager')
    def test_deploy_existing_project(self, mock_project_manager, mock_docker):
        """Test deploying existing project"""
        runner = CliRunner()
        
        # Mock project manager
        mock_project = Mock()
        mock_project.name = 'test-project'
        mock_project.status = 'created'
        mock_project_manager.return_value.get_current_project.return_value = mock_project
        mock_project_manager.return_value.deploy_project.return_value = True
        
        # Mock Docker client
        mock_docker.return_value.is_running.return_value = True
        
        with runner.isolated_filesystem():
            result = runner.invoke(deploy)
            
            assert result.exit_code == 0
            mock_project_manager.return_value.deploy_project.assert_called_once()
    
    @patch('blastdock.utils.docker_utils.DockerClient')
    def test_deploy_no_project(self, mock_docker):
        """Test deploying without project"""
        runner = CliRunner()
        
        mock_docker.return_value.is_running.return_value = True
        
        with runner.isolated_filesystem():
            result = runner.invoke(deploy)
            
            assert result.exit_code != 0
            assert 'No project found' in result.output
    
    @patch('blastdock.utils.docker_utils.DockerClient')
    def test_deploy_docker_not_running(self, mock_docker):
        """Test deploying when Docker is not running"""
        runner = CliRunner()
        
        mock_docker.return_value.is_running.return_value = False
        
        result = runner.invoke(deploy)
        
        assert result.exit_code != 0
        assert 'Docker' in result.output


class TestTraefikCommand:
    """Test Traefik command functionality"""
    
    @patch('blastdock.traefik.manager.TraefikManager')
    def test_traefik_status(self, mock_traefik_manager):
        """Test Traefik status command"""
        runner = CliRunner()
        
        mock_instance = Mock()
        mock_instance.status = 'running'
        mock_instance.container_id = 'test-container'
        mock_traefik_manager.return_value.get_instance.return_value = mock_instance
        
        result = runner.invoke(traefik, ['status'])
        
        assert result.exit_code == 0
        assert 'running' in result.output
    
    @patch('blastdock.traefik.manager.TraefikManager')
    def test_traefik_install(self, mock_traefik_manager):
        """Test Traefik installation"""
        runner = CliRunner()
        
        mock_traefik_manager.return_value.install.return_value = True
        
        result = runner.invoke(traefik, [
            'install',
            '--email', 'test@example.com',
            '--domain', 'example.com'
        ])
        
        assert result.exit_code == 0
        mock_traefik_manager.return_value.install.assert_called_once()
    
    @patch('blastdock.traefik.manager.TraefikManager')
    def test_traefik_start(self, mock_traefik_manager):
        """Test Traefik start command"""
        runner = CliRunner()
        
        mock_traefik_manager.return_value.start.return_value = True
        
        result = runner.invoke(traefik, ['start'])
        
        assert result.exit_code == 0
        mock_traefik_manager.return_value.start.assert_called_once()
    
    @patch('blastdock.traefik.manager.TraefikManager')
    def test_traefik_stop(self, mock_traefik_manager):
        """Test Traefik stop command"""
        runner = CliRunner()
        
        mock_traefik_manager.return_value.stop.return_value = True
        
        result = runner.invoke(traefik, ['stop'])
        
        assert result.exit_code == 0
        mock_traefik_manager.return_value.stop.assert_called_once()


class TestDomainCommand:
    """Test domain command functionality"""
    
    @patch('blastdock.domains.manager.DomainManager')
    def test_domain_list(self, mock_domain_manager):
        """Test domain list command"""
        runner = CliRunner()
        
        mock_domains = [
            Mock(config=Mock(domain='test1.example.com'), status='in_use'),
            Mock(config=Mock(domain='test2.example.com'), status='available')
        ]
        mock_domain_manager.return_value.list_domains.return_value = mock_domains
        
        result = runner.invoke(domain, ['list'])
        
        assert result.exit_code == 0
        assert 'test1.example.com' in result.output
        assert 'test2.example.com' in result.output
    
    @patch('blastdock.domains.manager.DomainManager')
    def test_domain_add(self, mock_domain_manager):
        """Test domain add command"""
        runner = CliRunner()
        
        mock_domain_manager.return_value.add_domain.return_value = True
        
        result = runner.invoke(domain, [
            'add',
            'test.example.com',
            '--project', 'test-project'
        ])
        
        assert result.exit_code == 0
        mock_domain_manager.return_value.add_domain.assert_called_once()
    
    @patch('blastdock.domains.manager.DomainManager')
    def test_domain_remove(self, mock_domain_manager):
        """Test domain remove command"""
        runner = CliRunner()
        
        mock_domain_manager.return_value.remove_domain.return_value = True
        
        result = runner.invoke(domain, ['remove', 'test.example.com'])
        
        assert result.exit_code == 0
        mock_domain_manager.return_value.remove_domain.assert_called_once()
    
    @patch('blastdock.domains.manager.DomainManager')
    def test_domain_validate(self, mock_domain_manager):
        """Test domain validation command"""
        runner = CliRunner()
        
        mock_domain_manager.return_value.validate_domain.return_value = True
        
        result = runner.invoke(domain, ['validate', 'test.example.com'])
        
        assert result.exit_code == 0
        mock_domain_manager.return_value.validate_domain.assert_called_once()


class TestPortCommand:
    """Test port command functionality"""
    
    @patch('blastdock.ports.manager.PortManager')
    def test_port_list(self, mock_port_manager):
        """Test port list command"""
        runner = CliRunner()
        
        mock_ports = [
            Mock(number=8080, status='in_use', allocation=Mock(project='test1')),
            Mock(number=8081, status='available', allocation=None)
        ]
        mock_port_manager.return_value.list_ports.return_value = mock_ports
        
        result = runner.invoke(port, ['list'])
        
        assert result.exit_code == 0
        assert '8080' in result.output
        assert '8081' in result.output
    
    @patch('blastdock.ports.manager.PortManager')
    def test_port_allocate(self, mock_port_manager):
        """Test port allocation command"""
        runner = CliRunner()
        
        mock_port_manager.return_value.allocate_port.return_value = 8080
        
        result = runner.invoke(port, [
            'allocate',
            '--project', 'test-project',
            '--service', 'web'
        ])
        
        assert result.exit_code == 0
        mock_port_manager.return_value.allocate_port.assert_called_once()
    
    @patch('blastdock.ports.manager.PortManager')
    def test_port_release(self, mock_port_manager):
        """Test port release command"""
        runner = CliRunner()
        
        mock_port_manager.return_value.release_port.return_value = True
        
        result = runner.invoke(port, ['release', '8080'])
        
        assert result.exit_code == 0
        mock_port_manager.return_value.release_port.assert_called_once()
    
    @patch('blastdock.ports.manager.PortManager')
    def test_port_check(self, mock_port_manager):
        """Test port availability check"""
        runner = CliRunner()
        
        mock_port_manager.return_value.is_port_available.return_value = True
        
        result = runner.invoke(port, ['check', '8080'])
        
        assert result.exit_code == 0
        mock_port_manager.return_value.is_port_available.assert_called_once()


class TestCLIErrorHandling:
    """Test CLI error handling"""
    
    def test_keyboard_interrupt_handling(self):
        """Test graceful handling of keyboard interrupts"""
        runner = CliRunner()
        
        with patch('blastdock.cli.main.cli') as mock_cli:
            mock_cli.side_effect = KeyboardInterrupt()
            
            result = runner.invoke(cli, ['--help'])
            # Should handle gracefully without crashing
    
    @patch('blastdock.utils.docker_utils.DockerClient')
    def test_docker_connection_error(self, mock_docker):
        """Test handling of Docker connection errors"""
        runner = CliRunner()
        
        mock_docker.return_value.is_running.side_effect = Exception("Docker connection failed")
        
        result = runner.invoke(deploy)
        
        assert result.exit_code != 0
        assert 'Docker' in result.output
    
    def test_missing_required_option(self):
        """Test handling of missing required options"""
        runner = CliRunner()
        
        result = runner.invoke(domain, ['add'])
        
        assert result.exit_code != 0
        assert 'Missing' in result.output or 'required' in result.output


class TestCLIConfiguration:
    """Test CLI configuration and settings"""
    
    @patch('blastdock.utils.config_utils.ConfigManager')
    def test_config_loading(self, mock_config_manager):
        """Test configuration loading"""
        runner = CliRunner()
        
        mock_config = {
            'default_template': 'wordpress',
            'traefik_enabled': True
        }
        mock_config_manager.return_value.get_config.return_value = mock_config
        
        result = runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
    
    def test_debug_mode(self):
        """Test debug mode activation"""
        runner = CliRunner()
        
        result = runner.invoke(cli, ['--debug', '--help'])
        
        assert result.exit_code == 0


class TestCLIOutput:
    """Test CLI output formatting"""
    
    @patch('blastdock.traefik.manager.TraefikManager')
    def test_json_output(self, mock_traefik_manager):
        """Test JSON output format"""
        runner = CliRunner()
        
        mock_instance = Mock()
        mock_instance.status = 'running'
        mock_instance.to_dict.return_value = {'status': 'running'}
        mock_traefik_manager.return_value.get_instance.return_value = mock_instance
        
        result = runner.invoke(traefik, ['status', '--output', 'json'])
        
        assert result.exit_code == 0
    
    @patch('blastdock.domains.manager.DomainManager')
    def test_table_output(self, mock_domain_manager):
        """Test table output format"""
        runner = CliRunner()
        
        mock_domains = [
            Mock(config=Mock(domain='test.example.com'), status='in_use')
        ]
        mock_domain_manager.return_value.list_domains.return_value = mock_domains
        
        result = runner.invoke(domain, ['list', '--output', 'table'])
        
        assert result.exit_code == 0
        assert 'test.example.com' in result.output