"""Comprehensive tests for core template_manager module."""

import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock, mock_open
import pytest
import yaml

from blastdock.core.template_manager import TemplateManager


class TestTemplateManager:
    """Test suite for TemplateManager."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def manager(self, temp_dir):
        """Create a TemplateManager instance with temp templates directory."""
        with patch('blastdock.core.template_manager.os.path.dirname') as mock_dirname:
            # Mock the directory path calculation
            mock_dirname.return_value = temp_dir
            manager = TemplateManager()
            manager.templates_dir = temp_dir
            return manager

    @pytest.fixture
    def sample_template_data(self):
        """Sample template data for testing."""
        return {
            'template_info': {
                'name': 'test-template',
                'description': 'A test template',
                'version': '1.0.0'
            },
            'fields': {
                'project_name': {
                    'type': 'string',
                    'description': 'Project name',
                    'required': True
                },
                'domain': {
                    'type': 'domain',
                    'description': 'Domain name',
                    'default': 'localhost'
                },
                'port': {
                    'type': 'port',
                    'description': 'Port number',
                    'default': 8080
                },
                'admin_password': {
                    'type': 'password',
                    'description': 'Admin password',
                    'default': 'auto'
                },
                'enable_ssl': {
                    'type': 'boolean',
                    'description': 'Enable SSL',
                    'default': False
                }
            },
            'compose': {
                'version': '3.8',
                'services': {
                    'web': {
                        'image': 'nginx:latest',
                        'ports': ['{{ port }}:80'],
                        'environment': {
                            'DOMAIN': '{{ domain }}'
                        }
                    }
                }
            }
        }

    def test_init(self, temp_dir):
        """Test TemplateManager initialization."""
        with patch('blastdock.core.template_manager.os.path.dirname') as mock_dirname:
            mock_dirname.return_value = temp_dir
            manager = TemplateManager()
            
            assert manager.templates_dir is not None
            assert manager.jinja_env is not None

    def test_list_templates_success(self, manager, temp_dir):
        """Test listing templates successfully."""
        # Create test template files
        template_files = ['nginx.yml', 'wordpress.yaml', 'mysql.yml', 'readme.txt']
        for filename in template_files:
            with open(os.path.join(temp_dir, filename), 'w') as f:
                f.write('test content')
        
        templates = manager.list_templates()
        
        # Should only include .yml and .yaml files, sorted
        expected = ['mysql', 'nginx', 'wordpress']
        assert templates == expected

    def test_list_templates_empty_directory(self, manager, temp_dir):
        """Test listing templates when directory is empty."""
        templates = manager.list_templates()
        
        assert templates == []

    def test_list_templates_directory_not_exists(self, manager):
        """Test listing templates when directory doesn't exist."""
        manager.templates_dir = '/nonexistent/path'
        
        templates = manager.list_templates()
        
        assert templates == []

    def test_template_exists_true(self, manager, temp_dir):
        """Test template_exists when template exists."""
        template_name = 'nginx'
        template_file = os.path.join(temp_dir, f'{template_name}.yml')
        
        # Create the template file
        with open(template_file, 'w') as f:
            f.write('test content')
        
        result = manager.template_exists(template_name)
        
        assert result is True

    def test_template_exists_false(self, manager):
        """Test template_exists when template doesn't exist."""
        template_name = 'nonexistent'
        
        result = manager.template_exists(template_name)
        
        assert result is False

    def test_get_template_info_success(self, manager, temp_dir, sample_template_data):
        """Test getting template info successfully."""
        template_name = 'test-template'
        template_file = os.path.join(temp_dir, f'{template_name}.yml')
        
        # Create template file with sample data
        with open(template_file, 'w') as f:
            yaml.dump(sample_template_data, f)
        
        with patch('blastdock.core.template_manager.load_yaml', return_value=sample_template_data):
            result = manager.get_template_info(template_name)
        
        expected_info = sample_template_data['template_info']
        assert result == expected_info

    def test_get_template_info_file_not_exists(self, manager):
        """Test getting template info when file doesn't exist."""
        template_name = 'nonexistent'
        
        result = manager.get_template_info(template_name)
        
        assert result == {}

    def test_get_template_info_yaml_error(self, manager, temp_dir):
        """Test getting template info with YAML error."""
        template_name = 'invalid'
        template_file = os.path.join(temp_dir, f'{template_name}.yml')
        
        # Create template file
        with open(template_file, 'w') as f:
            f.write('test content')
        
        with patch('blastdock.core.template_manager.load_yaml', side_effect=Exception("YAML error")):
            with patch('blastdock.core.template_manager.console.print') as mock_print:
                result = manager.get_template_info(template_name)
        
        assert result == {}
        mock_print.assert_called_once()

    def test_get_default_config_success(self, manager, temp_dir, sample_template_data):
        """Test getting default config successfully."""
        template_name = 'test-template'
        template_file = os.path.join(temp_dir, f'{template_name}.yml')
        
        # Create template file
        with open(template_file, 'w') as f:
            yaml.dump(sample_template_data, f)
        
        with patch('blastdock.core.template_manager.load_yaml', return_value=sample_template_data):
            with patch('blastdock.core.template_manager.generate_password', return_value='auto_generated_password'):
                result = manager.get_default_config(template_name)
        
        expected = {
            'project_name': '',
            'domain': 'localhost',
            'port': 8080,
            'admin_password': 'auto_generated_password',  # Should be auto-generated
            'enable_ssl': False
        }
        assert result == expected

    def test_get_default_config_template_not_found(self, manager):
        """Test getting default config when template doesn't exist."""
        template_name = 'nonexistent'
        
        with pytest.raises(Exception) as exc_info:
            manager.get_default_config(template_name)
        
        assert f"Template {template_name} not found" in str(exc_info.value)

    def test_get_default_config_yaml_error(self, manager, temp_dir):
        """Test getting default config with YAML error."""
        template_name = 'invalid'
        template_file = os.path.join(temp_dir, f'{template_name}.yml')
        
        # Create template file
        with open(template_file, 'w') as f:
            f.write('test content')
        
        with patch('blastdock.core.template_manager.load_yaml', side_effect=Exception("YAML error")):
            with pytest.raises(Exception) as exc_info:
                manager.get_default_config(template_name)
        
        assert "Error loading template: YAML error" in str(exc_info.value)

    def test_interactive_config_success(self, manager, temp_dir, sample_template_data):
        """Test interactive configuration successfully."""
        template_name = 'test-template'
        template_file = os.path.join(temp_dir, f'{template_name}.yml')
        
        # Create template file
        with open(template_file, 'w') as f:
            yaml.dump(sample_template_data, f)
        
        # Mock the prompt field method
        with patch('blastdock.core.template_manager.load_yaml', return_value=sample_template_data):
            with patch('blastdock.core.template_manager.console.print'):
                with patch.object(manager, '_prompt_field') as mock_prompt:
                    mock_prompt.side_effect = ['myproject', 'example.com', 9000, 'secretpass', True]
                    
                    result = manager.interactive_config(template_name)
        
        expected = {
            'project_name': 'myproject',
            'domain': 'example.com',
            'port': 9000,
            'admin_password': 'secretpass',
            'enable_ssl': True
        }
        assert result == expected

    def test_interactive_config_template_not_found(self, manager):
        """Test interactive config when template doesn't exist."""
        template_name = 'nonexistent'
        
        with pytest.raises(Exception) as exc_info:
            manager.interactive_config(template_name)
        
        assert f"Template {template_name} not found" in str(exc_info.value)

    def test_prompt_field_string(self, manager):
        """Test prompting for string field."""
        field_info = {
            'type': 'string',
            'description': 'Project name',
            'default': 'myproject'
        }
        
        with patch('blastdock.core.template_manager.Prompt.ask', return_value='testproject'):
            with patch.object(manager, '_validate_field', return_value=(True, '')):
                result = manager._prompt_field('project_name', field_info)
        
        assert result == 'testproject'

    def test_prompt_field_boolean(self, manager):
        """Test prompting for boolean field."""
        field_info = {
            'type': 'boolean',
            'description': 'Enable SSL',
            'default': False
        }
        
        with patch('blastdock.core.template_manager.Confirm.ask', return_value=True):
            result = manager._prompt_field('enable_ssl', field_info)
        
        assert result is True

    def test_prompt_field_password_auto_generate(self, manager):
        """Test prompting for password field with auto-generation."""
        field_info = {
            'type': 'password',
            'description': 'Admin password',
            'default': 'auto'
        }
        
        with patch('blastdock.core.template_manager.Confirm.ask', return_value=True):
            with patch('blastdock.core.template_manager.generate_password', return_value='generated_password'):
                result = manager._prompt_field('admin_password', field_info)
        
        assert result == 'generated_password'

    def test_prompt_field_password_manual(self, manager):
        """Test prompting for password field with manual entry."""
        field_info = {
            'type': 'password',
            'description': 'Admin password',
            'default': 'auto'
        }
        
        with patch('blastdock.core.template_manager.Confirm.ask', return_value=False):
            with patch('blastdock.core.template_manager.Prompt.ask', return_value='mypassword'):
                with patch.object(manager, '_validate_field', return_value=(True, '')):
                    result = manager._prompt_field('admin_password', field_info)
        
        assert result == 'mypassword'

    def test_prompt_field_validation_error(self, manager):
        """Test prompting with validation error."""
        field_info = {
            'type': 'string',
            'description': 'Project name',
            'required': True
        }
        
        with patch('blastdock.core.template_manager.Prompt.ask', side_effect=['', 'validname']):
            with patch.object(manager, '_validate_field', side_effect=[(False, 'Required field'), (True, '')]):
                with patch('blastdock.core.template_manager.console.print') as mock_print:
                    result = manager._prompt_field('project_name', field_info)
        
        assert result == 'validname'
        mock_print.assert_called_once()

    def test_validate_field_required_empty(self, manager):
        """Test field validation for required empty field."""
        field_info = {'required': True}
        
        valid, error = manager._validate_field('test_field', '', field_info)
        
        assert valid is False
        assert 'test_field is required' in error

    def test_validate_field_optional_empty(self, manager):
        """Test field validation for optional empty field."""
        field_info = {'required': False}
        
        valid, error = manager._validate_field('test_field', '', field_info)
        
        assert valid is True
        assert error == ''

    def test_validate_field_port(self, manager):
        """Test field validation for port type."""
        field_info = {'type': 'port'}
        
        with patch('blastdock.core.template_manager.validate_port_input', return_value=(True, '')):
            valid, error = manager._validate_field('port', '8080', field_info)
        
        assert valid is True

    def test_validate_field_email(self, manager):
        """Test field validation for email type."""
        field_info = {'type': 'email'}
        
        with patch('blastdock.core.template_manager.validate_email', return_value=(True, '')):
            valid, error = manager._validate_field('email', 'test@example.com', field_info)
        
        assert valid is True

    def test_validate_field_domain(self, manager):
        """Test field validation for domain type."""
        field_info = {'type': 'domain'}
        
        with patch('blastdock.core.template_manager.validate_domain', return_value=(True, '')):
            valid, error = manager._validate_field('domain', 'example.com', field_info)
        
        assert valid is True

    def test_validate_field_password(self, manager):
        """Test field validation for password type."""
        field_info = {'type': 'password'}
        
        with patch('blastdock.core.template_manager.validate_password', return_value=(True, '')):
            valid, error = manager._validate_field('password', 'secretpass', field_info)
        
        assert valid is True

    def test_validate_field_database_name(self, manager):
        """Test field validation for database_name type."""
        field_info = {'type': 'database_name'}
        
        with patch('blastdock.core.template_manager.validate_database_name', return_value=(True, '')):
            valid, error = manager._validate_field('db_name', 'mydb', field_info)
        
        assert valid is True

    def test_validate_field_project_name(self, manager):
        """Test field validation for project_name field."""
        field_info = {'type': 'string'}
        
        with patch('blastdock.core.template_manager.validate_project_name', return_value=(True, '')):
            valid, error = manager._validate_field('project_name', 'myproject', field_info)
        
        assert valid is True

    def test_validate_field_default_string(self, manager):
        """Test field validation for default string type."""
        field_info = {'type': 'string'}
        
        valid, error = manager._validate_field('description', 'Some description', field_info)
        
        assert valid is True
        assert error == ''

    def test_render_template_success(self, manager, sample_template_data):
        """Test rendering template successfully."""
        template_name = 'test-template'
        config = {
            'domain': 'example.com',
            'port': 9000
        }
        
        # Mock Jinja2 template
        mock_template = Mock()
        mock_template.render.return_value = yaml.dump(sample_template_data)
        
        with patch.object(manager.jinja_env, 'get_template', return_value=mock_template):
            result = manager.render_template(template_name, config)
        
        assert result == sample_template_data
        mock_template.render.assert_called_once_with(**config)

    def test_render_template_not_found(self, manager):
        """Test rendering template when template not found."""
        template_name = 'nonexistent'
        config = {}
        
        from jinja2 import TemplateNotFound
        with patch.object(manager.jinja_env, 'get_template', side_effect=TemplateNotFound(template_name)):
            with pytest.raises(Exception) as exc_info:
                manager.render_template(template_name, config)
        
        assert f"Template {template_name} not found" in str(exc_info.value)

    def test_render_template_render_error(self, manager):
        """Test rendering template with render error."""
        template_name = 'test-template'
        config = {}
        
        mock_template = Mock()
        mock_template.render.side_effect = Exception("Render error")
        
        with patch.object(manager.jinja_env, 'get_template', return_value=mock_template):
            with pytest.raises(Exception) as exc_info:
                manager.render_template(template_name, config)
        
        assert "Error rendering template: Render error" in str(exc_info.value)

    def test_prompt_field_optional_not_required_empty(self, manager):
        """Test prompting for optional field that's not required."""
        field_info = {
            'type': 'string',
            'description': 'Optional field',
            'required': False
        }
        
        with patch('blastdock.core.template_manager.Prompt.ask', return_value=''):
            with patch.object(manager, '_validate_field', return_value=(True, '')):
                result = manager._prompt_field('optional_field', field_info)
        
        assert result == ''

    def test_get_default_config_no_fields(self, manager, temp_dir):
        """Test getting default config when template has no fields."""
        template_data = {
            'template_info': {'name': 'simple'},
            'compose': {'version': '3.8'}
        }
        template_name = 'simple'
        template_file = os.path.join(temp_dir, f'{template_name}.yml')
        
        with open(template_file, 'w') as f:
            yaml.dump(template_data, f)
        
        with patch('blastdock.core.template_manager.load_yaml', return_value=template_data):
            result = manager.get_default_config(template_name)
        
        assert result == {}

    def test_interactive_config_no_description(self, manager, temp_dir):
        """Test interactive config when template has no description."""
        template_data = {
            'template_info': {'name': 'no-desc'},
            'fields': {
                'test_field': {
                    'type': 'string',
                    'default': 'test'
                }
            }
        }
        template_name = 'no-desc'
        template_file = os.path.join(temp_dir, f'{template_name}.yml')
        
        with open(template_file, 'w') as f:
            yaml.dump(template_data, f)
        
        with patch('blastdock.core.template_manager.load_yaml', return_value=template_data):
            with patch('blastdock.core.template_manager.console.print') as mock_print:
                with patch.object(manager, '_prompt_field', return_value='test_value'):
                    result = manager.interactive_config(template_name)
        
        assert result == {'test_field': 'test_value'}
        # Should still print the header
        mock_print.assert_called()

    def test_interactive_config_yaml_error(self, manager, temp_dir):
        """Test interactive config with YAML loading error."""
        template_name = 'invalid'
        template_file = os.path.join(temp_dir, f'{template_name}.yml')
        
        # Create template file
        with open(template_file, 'w') as f:
            f.write('test content')
        
        with patch('blastdock.core.template_manager.load_yaml', side_effect=Exception("YAML error")):
            with pytest.raises(Exception) as exc_info:
                manager.interactive_config(template_name)
        
        assert "Error in interactive config: YAML error" in str(exc_info.value)

    def test_prompt_field_required_with_retry(self, manager):
        """Test prompting for required field with empty value first, then valid value."""
        field_info = {
            'type': 'string',
            'description': 'Required field',
            'required': True
        }
        
        with patch('blastdock.core.template_manager.Prompt.ask', side_effect=['', 'valid_value']):
            with patch.object(manager, '_validate_field', side_effect=[(False, 'Required'), (True, '')]):
                with patch('blastdock.core.template_manager.console.print'):
                    result = manager._prompt_field('required_field', field_info)
        
        assert result == 'valid_value'