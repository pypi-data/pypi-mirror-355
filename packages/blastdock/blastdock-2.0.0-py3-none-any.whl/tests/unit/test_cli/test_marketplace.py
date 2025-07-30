"""
Tests for marketplace CLI commands
"""

import pytest
from unittest.mock import Mock, patch
from click.testing import CliRunner

from blastdock.cli.marketplace import marketplace_group


class TestMarketplaceCommands:
    """Test marketplace CLI commands"""

    def test_marketplace_help(self, cli_runner):
        """Test marketplace help command"""
        result = cli_runner.invoke(marketplace_group, ['--help'])
        assert result.exit_code == 0
        assert 'Template marketplace commands' in result.output

    @patch('blastdock.cli.marketplace.TemplateMarketplace')
    def test_marketplace_search_success(self, mock_marketplace_class, cli_runner):
        """Test successful marketplace search"""
        mock_marketplace = Mock()
        mock_marketplace.search.return_value = [
            Mock(
                id='wordpress',
                display_name='WordPress',
                category=Mock(value='CMS'),
                rating=4.5,
                downloads=1000,
                traefik_compatible=True
            )
        ]
        mock_marketplace_class.return_value = mock_marketplace
        
        result = cli_runner.invoke(marketplace_group, ['search', 'wordpress'])
        assert result.exit_code == 0
        assert 'wordpress' in result.output.lower()

    @patch('blastdock.cli.marketplace.TemplateMarketplace')
    def test_marketplace_search_no_results(self, mock_marketplace_class, cli_runner):
        """Test marketplace search with no results"""
        mock_marketplace = Mock()
        mock_marketplace.search.return_value = []
        mock_marketplace_class.return_value = mock_marketplace
        
        result = cli_runner.invoke(marketplace_group, ['search', 'nonexistent'])
        assert result.exit_code == 0
        assert 'No templates found' in result.output

    @patch('blastdock.cli.marketplace.TemplateMarketplace')
    def test_marketplace_info_success(self, mock_marketplace_class, cli_runner):
        """Test successful template info"""
        mock_template = Mock()
        mock_template.id = 'wordpress'
        mock_template.display_name = 'WordPress'
        mock_template.description = 'WordPress CMS'
        mock_template.version = '1.0.0'
        mock_template.author = 'Test Author'
        mock_template.category = Mock(value='CMS')
        mock_template.source = 'official'
        mock_template.rating = 4.5
        mock_template.downloads = 1000
        mock_template.stars = 50
        mock_template.services = ['wordpress', 'mysql']
        mock_template.traefik_compatible = True
        mock_template.validation_score = 95
        mock_template.security_score = 90
        mock_template.tags = ['cms', 'blog']
        mock_template.repository_url = 'https://github.com/example/wordpress'
        mock_template.documentation_url = 'https://docs.example.com/wordpress'
        
        mock_marketplace = Mock()
        mock_marketplace.get_template.return_value = mock_template
        mock_marketplace_class.return_value = mock_marketplace
        
        result = cli_runner.invoke(marketplace_group, ['info', 'wordpress'])
        assert result.exit_code == 0
        assert 'WordPress' in result.output

    @patch('blastdock.cli.marketplace.TemplateMarketplace')
    def test_marketplace_info_not_found(self, mock_marketplace_class, cli_runner):
        """Test template info for non-existent template"""
        mock_marketplace = Mock()
        mock_marketplace.get_template.return_value = None
        mock_marketplace_class.return_value = mock_marketplace
        
        result = cli_runner.invoke(marketplace_group, ['info', 'nonexistent'])
        assert result.exit_code == 0
        assert 'not found' in result.output

    @patch('blastdock.cli.marketplace.TemplateMarketplace')
    def test_marketplace_featured(self, mock_marketplace_class, cli_runner):
        """Test featured templates command"""
        mock_template = Mock()
        mock_template.display_name = 'Featured Template'
        mock_template.description = 'A featured template'
        mock_template.id = 'featured'
        mock_template.rating = 5.0
        mock_template.downloads = 2000
        mock_template.category = Mock(value='Popular')
        
        mock_marketplace = Mock()
        mock_marketplace.get_featured_templates.return_value = [mock_template]
        mock_marketplace_class.return_value = mock_marketplace
        
        result = cli_runner.invoke(marketplace_group, ['featured'])
        assert result.exit_code == 0
        assert 'Featured Templates' in result.output

    @patch('blastdock.cli.marketplace.TemplateMarketplace')
    def test_marketplace_categories(self, mock_marketplace_class, cli_runner):
        """Test categories listing"""
        from blastdock.marketplace.marketplace import TemplateCategory
        
        mock_marketplace = Mock()
        mock_marketplace.get_categories.return_value = {
            TemplateCategory.CMS: 5,
            TemplateCategory.DATABASE: 3
        }
        mock_marketplace.get_stats.return_value = {
            'total_templates': 8,
            'total_downloads': 5000,
            'traefik_compatible': 6
        }
        mock_marketplace_class.return_value = mock_marketplace
        
        result = cli_runner.invoke(marketplace_group, ['categories'])
        assert result.exit_code == 0
        assert 'Template Categories' in result.output

    @patch('blastdock.cli.marketplace.TemplateInstaller')
    def test_marketplace_install_success(self, mock_installer_class, cli_runner):
        """Test successful template installation"""
        mock_installer = Mock()
        mock_installer.install_template.return_value = {
            'success': True,
            'template_name': 'wordpress',
            'version': '1.0.0',
            'path': '/path/to/template',
            'validation_score': 95,
            'traefik_compatible': True
        }
        mock_installer_class.return_value = mock_installer
        
        result = cli_runner.invoke(marketplace_group, ['install', 'wordpress'])
        assert result.exit_code == 0
        assert 'Successfully installed' in result.output

    @patch('blastdock.cli.marketplace.TemplateInstaller')
    def test_marketplace_install_failure(self, mock_installer_class, cli_runner):
        """Test failed template installation"""
        mock_installer = Mock()
        mock_installer.install_template.return_value = {
            'success': False,
            'error': 'Template validation failed'
        }
        mock_installer_class.return_value = mock_installer
        
        result = cli_runner.invoke(marketplace_group, ['install', 'invalid'])
        assert result.exit_code == 0
        assert 'Installation failed' in result.output

    @patch('blastdock.cli.marketplace.TemplateInstaller')
    def test_marketplace_list_installed(self, mock_installer_class, cli_runner):
        """Test listing installed templates"""
        mock_installer = Mock()
        mock_installer.list_installed_templates.return_value = [
            {
                'name': 'WordPress',
                'template_id': 'wordpress',
                'version': '1.0.0',
                'source': 'official',
                'validation_score': 95,
                'traefik_compatible': True
            }
        ]
        mock_installer_class.return_value = mock_installer
        
        result = cli_runner.invoke(marketplace_group, ['list', '--installed'])
        assert result.exit_code == 0
        assert 'Installed Templates' in result.output

    @patch('blastdock.cli.marketplace.TemplateMarketplace')
    def test_marketplace_list_all(self, mock_marketplace_class, cli_runner):
        """Test listing all marketplace templates"""
        mock_template = Mock()
        mock_template.category = Mock(value='CMS')
        mock_template.id = 'wordpress'
        mock_template.display_name = 'WordPress'
        mock_template.downloads = 1000
        mock_template.rating = 4.5
        
        mock_marketplace = Mock()
        mock_marketplace.search.return_value = [mock_template]
        mock_marketplace_class.return_value = mock_marketplace
        
        result = cli_runner.invoke(marketplace_group, ['list'])
        assert result.exit_code == 0
        assert 'Marketplace Templates' in result.output

    @patch('blastdock.cli.marketplace.TemplateInstaller')
    def test_marketplace_uninstall(self, mock_installer_class, cli_runner):
        """Test template uninstallation"""
        mock_installer = Mock()
        mock_installer.uninstall_template.return_value = {'success': True}
        mock_installer_class.return_value = mock_installer
        
        result = cli_runner.invoke(marketplace_group, ['uninstall', 'wordpress', '--yes'])
        assert result.exit_code == 0

    @patch('blastdock.cli.marketplace.TemplateInstaller')
    def test_marketplace_update(self, mock_installer_class, cli_runner):
        """Test template update"""
        mock_installer = Mock()
        mock_installer.update_template.return_value = {
            'success': True,
            'version': '1.1.0'
        }
        mock_installer_class.return_value = mock_installer
        
        result = cli_runner.invoke(marketplace_group, ['update', 'wordpress'])
        assert result.exit_code == 0
        assert 'Successfully updated' in result.output
