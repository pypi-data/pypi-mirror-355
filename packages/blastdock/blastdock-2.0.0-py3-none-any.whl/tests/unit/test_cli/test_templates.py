"""Comprehensive tests for CLI templates module."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
from click.testing import CliRunner

from blastdock.cli.templates import (
    templates, validate, analyze, enhance, list,
    _filter_analyses, _display_table_output, _display_detailed_output,
    _display_json_output, _display_template_analysis, _display_summary
)
from blastdock.utils.template_validator import ValidationLevel, TraefikCompatibility


class TestTemplatesCLI:
    """Test suite for templates CLI commands."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def temp_templates_dir(self):
        """Create temporary templates directory with sample templates."""
        temp_dir = tempfile.mkdtemp()
        templates_dir = Path(temp_dir) / 'templates'
        templates_dir.mkdir()
        
        # Create sample template files
        template1 = templates_dir / 'nginx.yml'
        template1.write_text("""
version: '3.8'
template_info:
  name: nginx
  description: Nginx web server
  version: 1.0.0
  traefik_compatible: true
  services: [web]
services:
  web:
    image: nginx:1.21
    ports:
      - "80:80"
""")
        
        template2 = templates_dir / 'postgres.yml'
        template2.write_text("""
version: '3.8'
template_info:
  name: postgres
  description: PostgreSQL database
  version: 1.2.0
  traefik_compatible: false
  services: [database]
services:
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: myapp
""")
        
        yield templates_dir
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def mock_validator(self):
        """Create mock template validator."""
        validator = Mock()
        # Create a mock Path object for templates_dir
        mock_templates_dir = Mock(spec=Path)
        mock_templates_dir.glob = Mock()
        validator.templates_dir = mock_templates_dir
        
        # Mock analysis results
        mock_analysis = Mock()
        mock_analysis.is_valid = True
        mock_analysis.score = 85
        mock_analysis.error_count = 0
        mock_analysis.warning_count = 1
        mock_analysis.traefik_compatibility = TraefikCompatibility.FULL
        mock_analysis.template_name = 'nginx'
        mock_analysis.results = []
        
        validator.validate_template.return_value = mock_analysis
        validator.validate_all_templates.return_value = {'nginx': mock_analysis}
        validator.enhance_template_traefik_support.return_value = (True, 'Enhanced successfully')
        validator.generate_validation_report.return_value = 'Mock validation report'
        
        return validator

    def test_templates_group(self, runner):
        """Test templates command group."""
        result = runner.invoke(templates, ['--help'])
        
        assert result.exit_code == 0
        assert 'Template management and validation commands' in result.output

    def test_validate_command_basic(self, runner, temp_templates_dir, mock_validator):
        """Test basic validate command."""
        with patch('blastdock.cli.templates.TemplateValidator', return_value=mock_validator):
            # Mock glob to return our test templates
            mock_validator.templates_dir.glob.return_value = [
                temp_templates_dir / 'nginx.yml',
                temp_templates_dir / 'postgres.yml'
            ]
            
            result = runner.invoke(validate, ['-d', str(temp_templates_dir)])
            
            assert result.exit_code == 0
            assert 'Validating BlastDock Templates' in result.output

    def test_validate_command_no_templates(self, runner, mock_validator):
        """Test validate command with no templates found."""
        with patch('blastdock.cli.templates.TemplateValidator', return_value=mock_validator):
            # Mock empty glob result
            mock_validator.templates_dir.glob.return_value = []
            
            result = runner.invoke(validate)
            
            assert result.exit_code == 0
            assert 'No template files found' in result.output

    def test_validate_command_table_output(self, runner, temp_templates_dir, mock_validator):
        """Test validate command with table output."""
        with patch('blastdock.cli.templates.TemplateValidator', return_value=mock_validator):
            mock_validator.templates_dir.glob.return_value = [temp_templates_dir / 'nginx.yml']
            
            result = runner.invoke(validate, ['-d', str(temp_templates_dir), '--output', 'table'])
            
            assert result.exit_code == 0

    def test_validate_command_detailed_output(self, runner, temp_templates_dir, mock_validator):
        """Test validate command with detailed output."""
        with patch('blastdock.cli.templates.TemplateValidator', return_value=mock_validator):
            mock_validator.templates_dir = temp_templates_dir
            mock_validator.templates_dir.glob.return_value = [temp_templates_dir / 'nginx.yml']
            
            result = runner.invoke(validate, ['-d', str(temp_templates_dir), '--output', 'detailed'])
            
            assert result.exit_code == 0

    def test_validate_command_json_output(self, runner, temp_templates_dir, mock_validator):
        """Test validate command with JSON output."""
        with patch('blastdock.cli.templates.TemplateValidator', return_value=mock_validator):
            mock_validator.templates_dir = temp_templates_dir
            mock_validator.templates_dir.glob.return_value = [temp_templates_dir / 'nginx.yml']
            
            result = runner.invoke(validate, ['-d', str(temp_templates_dir), '--output', 'json'])
            
            assert result.exit_code == 0

    def test_validate_command_with_filters(self, runner, temp_templates_dir, mock_validator):
        """Test validate command with different filters."""
        with patch('blastdock.cli.templates.TemplateValidator', return_value=mock_validator):
            mock_validator.templates_dir = temp_templates_dir
            mock_validator.templates_dir.glob.return_value = [temp_templates_dir / 'nginx.yml']
            
            # Test different filter types
            for filter_type in ['all', 'errors', 'warnings', 'no-traefik']:
                result = runner.invoke(validate, ['-d', str(temp_templates_dir), '--filter', filter_type])
                assert result.exit_code == 0

    def test_validate_command_save_report(self, runner, temp_templates_dir, mock_validator):
        """Test validate command with report saving."""
        with patch('blastdock.cli.templates.TemplateValidator', return_value=mock_validator):
            mock_validator.templates_dir = temp_templates_dir
            mock_validator.templates_dir.glob.return_value = [temp_templates_dir / 'nginx.yml']
            
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as report_file:
                result = runner.invoke(validate, [
                    '-d', str(temp_templates_dir),
                    '--save-report', report_file.name
                ])
                
                assert result.exit_code == 0
                assert 'Detailed report saved to' in result.output
                
                # Cleanup
                os.unlink(report_file.name)

    def test_analyze_command_success(self, runner, temp_templates_dir, mock_validator):
        """Test analyze command with existing template."""
        with patch('blastdock.cli.templates.TemplateValidator', return_value=mock_validator):
            mock_validator.templates_dir = temp_templates_dir
            template_path = temp_templates_dir / 'nginx.yml'
            
            # Mock path existence
            with patch.object(Path, 'exists', return_value=True):
                result = runner.invoke(analyze, ['nginx', '-d', str(temp_templates_dir)])
                
                assert result.exit_code == 0
                assert 'Analyzing Template: nginx' in result.output

    def test_analyze_command_template_not_found(self, runner, temp_templates_dir, mock_validator):
        """Test analyze command with non-existent template."""
        with patch('blastdock.cli.templates.TemplateValidator', return_value=mock_validator):
            mock_validator.templates_dir = temp_templates_dir
            
            # Mock path not existing
            with patch.object(Path, 'exists', return_value=False):
                result = runner.invoke(analyze, ['nonexistent', '-d', str(temp_templates_dir)])
                
                assert result.exit_code == 0
                assert "Template 'nonexistent' not found" in result.output

    def test_enhance_command_no_templates_to_enhance(self, runner, temp_templates_dir, mock_validator):
        """Test enhance command when no templates need enhancement."""
        with patch('blastdock.cli.templates.TemplateValidator', return_value=mock_validator):
            mock_validator.templates_dir = temp_templates_dir
            # Mock no templates needing enhancement
            mock_validator.validate_all_templates.return_value = {}
            
            result = runner.invoke(enhance, ['-d', str(temp_templates_dir)])
            
            assert result.exit_code == 0
            assert 'No templates need enhancement' in result.output

    def test_enhance_command_with_templates_dry_run(self, runner, temp_templates_dir, mock_validator):
        """Test enhance command with dry run."""
        with patch('blastdock.cli.templates.TemplateValidator', return_value=mock_validator):
            mock_validator.templates_dir = temp_templates_dir
            
            # Mock template needing enhancement
            mock_analysis = Mock()
            mock_analysis.traefik_compatibility = TraefikCompatibility.NONE
            mock_analysis.error_count = 1
            mock_analysis.warning_count = 2
            mock_analysis.score = 60
            
            mock_validator.validate_all_templates.return_value = {'nginx': mock_analysis}
            
            result = runner.invoke(enhance, ['-d', str(temp_templates_dir), '--dry-run'])
            
            assert result.exit_code == 0
            assert 'Dry run mode' in result.output

    def test_enhance_command_cancelled(self, runner, temp_templates_dir, mock_validator):
        """Test enhance command when user cancels."""
        with patch('blastdock.cli.templates.TemplateValidator', return_value=mock_validator):
            mock_validator.templates_dir = temp_templates_dir
            
            # Mock template needing enhancement
            mock_analysis = Mock()
            mock_analysis.traefik_compatibility = TraefikCompatibility.NONE
            mock_analysis.error_count = 1
            mock_analysis.warning_count = 2
            mock_analysis.score = 60
            
            mock_validator.validate_all_templates.return_value = {'nginx': mock_analysis}
            
            # Mock user declining confirmation
            with patch('click.confirm', return_value=False):
                result = runner.invoke(enhance, ['-d', str(temp_templates_dir)])
                
                assert result.exit_code == 0
                assert 'Enhancement cancelled' in result.output

    def test_enhance_command_with_backup(self, runner, temp_templates_dir, mock_validator):
        """Test enhance command with backup option."""
        with patch('blastdock.cli.templates.TemplateValidator', return_value=mock_validator):
            mock_validator.templates_dir = temp_templates_dir
            
            # Mock template needing enhancement
            mock_analysis = Mock()
            mock_analysis.traefik_compatibility = TraefikCompatibility.NONE
            mock_analysis.error_count = 1
            mock_analysis.warning_count = 2
            mock_analysis.score = 60
            
            mock_validator.validate_all_templates.return_value = {'nginx': mock_analysis}
            
            # Mock user confirming
            with patch('click.confirm', return_value=True):
                with patch.object(Path, 'read_text', return_value='template content'):
                    with patch.object(Path, 'write_text'):
                        result = runner.invoke(enhance, ['-d', str(temp_templates_dir), '--backup'])
                        
                        assert result.exit_code == 0

    def test_list_command_no_templates(self, runner, mock_validator):
        """Test list command with no templates."""
        with patch('blastdock.cli.templates.TemplateValidator', return_value=mock_validator):
            mock_validator.templates_dir.glob.return_value = []
            
            result = runner.invoke(list)
            
            assert result.exit_code == 0
            assert 'No template files found' in result.output

    def test_list_command_table_output(self, runner, temp_templates_dir, mock_validator):
        """Test list command with table output."""
        with patch('blastdock.cli.templates.TemplateValidator', return_value=mock_validator):
            mock_validator.templates_dir = temp_templates_dir
            mock_validator.templates_dir.glob.return_value = [
                temp_templates_dir / 'nginx.yml',
                temp_templates_dir / 'postgres.yml'
            ]
            
            result = runner.invoke(list, ['-d', str(temp_templates_dir), '--output', 'table'])
            
            assert result.exit_code == 0
            assert 'Available Templates' in result.output

    def test_list_command_json_output(self, runner, temp_templates_dir, mock_validator):
        """Test list command with JSON output."""
        with patch('blastdock.cli.templates.TemplateValidator', return_value=mock_validator):
            mock_validator.templates_dir = temp_templates_dir
            mock_validator.templates_dir.glob.return_value = [
                temp_templates_dir / 'nginx.yml',
                temp_templates_dir / 'postgres.yml'
            ]
            
            result = runner.invoke(list, ['-d', str(temp_templates_dir), '--output', 'json'])
            
            assert result.exit_code == 0

    def test_list_command_with_template_errors(self, runner, temp_templates_dir, mock_validator):
        """Test list command with template loading errors."""
        with patch('blastdock.cli.templates.TemplateValidator', return_value=mock_validator):
            mock_validator.templates_dir = temp_templates_dir
            
            # Create invalid template
            invalid_template = temp_templates_dir / 'invalid.yml'
            invalid_template.write_text('invalid: yaml: content: {')
            
            mock_validator.templates_dir.glob.return_value = [invalid_template]
            
            result = runner.invoke(list, ['-d', str(temp_templates_dir)])
            
            assert result.exit_code == 0

    def test_filter_analyses_all(self):
        """Test filtering analyses with 'all' filter."""
        analyses = {'template1': Mock(), 'template2': Mock()}
        result = _filter_analyses(analyses, 'all')
        
        assert len(result) == 2

    def test_filter_analyses_errors(self):
        """Test filtering analyses with 'errors' filter."""
        analysis1 = Mock()
        analysis1.error_count = 1
        analysis2 = Mock()
        analysis2.error_count = 0
        
        analyses = {'template1': analysis1, 'template2': analysis2}
        result = _filter_analyses(analyses, 'errors')
        
        assert len(result) == 1
        assert 'template1' in result

    def test_filter_analyses_warnings(self):
        """Test filtering analyses with 'warnings' filter."""
        analysis1 = Mock()
        analysis1.warning_count = 1
        analysis2 = Mock()
        analysis2.warning_count = 0
        
        analyses = {'template1': analysis1, 'template2': analysis2}
        result = _filter_analyses(analyses, 'warnings')
        
        assert len(result) == 1
        assert 'template1' in result

    def test_filter_analyses_no_traefik(self):
        """Test filtering analyses with 'no-traefik' filter."""
        analysis1 = Mock()
        analysis1.traefik_compatibility = TraefikCompatibility.NONE
        analysis2 = Mock()
        analysis2.traefik_compatibility = TraefikCompatibility.FULL
        
        analyses = {'template1': analysis1, 'template2': analysis2}
        result = _filter_analyses(analyses, 'no-traefik')
        
        assert len(result) == 1
        assert 'template1' in result

    def test_display_table_output(self, capsys):
        """Test table output display."""
        analysis = Mock()
        analysis.is_valid = True
        analysis.score = 85
        analysis.error_count = 0
        analysis.warning_count = 1
        analysis.traefik_compatibility = TraefikCompatibility.FULL
        
        analyses = {'nginx': analysis}
        
        with patch('blastdock.cli.templates.console') as mock_console:
            _display_table_output(analyses)
            mock_console.print.assert_called()

    def test_display_detailed_output(self):
        """Test detailed output display."""
        mock_result = Mock()
        mock_result.level = ValidationLevel.INFO
        mock_result.category = 'structure'
        mock_result.message = 'Test message'
        mock_result.suggestion = 'Test suggestion'
        
        analysis = Mock()
        analysis.score = 85
        analysis.traefik_compatibility = TraefikCompatibility.FULL
        analysis.results = [mock_result]
        
        analyses = {'nginx': analysis}
        
        with patch('blastdock.cli.templates.console') as mock_console:
            _display_detailed_output(analyses)
            mock_console.print.assert_called()

    def test_display_json_output(self):
        """Test JSON output display."""
        mock_result = Mock()
        mock_result.level = ValidationLevel.INFO
        mock_result.category = 'structure'
        mock_result.message = 'Test message'
        mock_result.suggestion = 'Test suggestion'
        
        analysis = Mock()
        analysis.is_valid = True
        analysis.score = 85
        analysis.traefik_compatibility = TraefikCompatibility.FULL
        analysis.error_count = 0
        analysis.warning_count = 1
        analysis.results = [mock_result]
        
        analyses = {'nginx': analysis}
        
        with patch('blastdock.cli.templates.console') as mock_console:
            _display_json_output(analyses)
            mock_console.print.assert_called()

    def test_display_template_analysis(self):
        """Test template analysis display."""
        mock_result = Mock()
        mock_result.level = ValidationLevel.ERROR
        mock_result.category = 'security'
        mock_result.message = 'Security issue found'
        mock_result.suggestion = 'Fix the issue'
        
        analysis = Mock()
        analysis.template_name = 'nginx'
        analysis.is_valid = False
        analysis.score = 65
        analysis.traefik_compatibility = TraefikCompatibility.PARTIAL
        analysis.error_count = 1
        analysis.warning_count = 0
        analysis.results = [mock_result]
        
        with patch('blastdock.cli.templates.console') as mock_console:
            _display_template_analysis(analysis)
            mock_console.print.assert_called()

    def test_display_summary(self):
        """Test summary display."""
        analysis1 = Mock()
        analysis1.is_valid = True
        analysis1.score = 85
        analysis1.traefik_compatibility = TraefikCompatibility.FULL
        
        analysis2 = Mock()
        analysis2.is_valid = False
        analysis2.score = 60
        analysis2.traefik_compatibility = TraefikCompatibility.NONE
        
        analyses = {'template1': analysis1, 'template2': analysis2}
        
        with patch('blastdock.cli.templates.console') as mock_console:
            _display_summary(analyses)
            mock_console.print.assert_called()

    def test_enhance_command_filter_types(self, runner, temp_templates_dir, mock_validator):
        """Test enhance command with different filter types."""
        with patch('blastdock.cli.templates.TemplateValidator', return_value=mock_validator):
            mock_validator.templates_dir = temp_templates_dir
            
            # Test each filter type
            for filter_type in ['none', 'basic', 'partial']:
                # Mock analysis with matching compatibility
                mock_analysis = Mock()
                if filter_type == 'none':
                    mock_analysis.traefik_compatibility = TraefikCompatibility.NONE
                elif filter_type == 'basic':
                    mock_analysis.traefik_compatibility = TraefikCompatibility.BASIC
                else:
                    mock_analysis.traefik_compatibility = TraefikCompatibility.PARTIAL
                
                mock_analysis.error_count = 1
                mock_analysis.warning_count = 2
                mock_analysis.score = 60
                
                mock_validator.validate_all_templates.return_value = {'nginx': mock_analysis}
                
                result = runner.invoke(enhance, [
                    '-d', str(temp_templates_dir),
                    '--filter', filter_type,
                    '--dry-run'
                ])
                
                assert result.exit_code == 0

    def test_enhance_command_enhancement_failure(self, runner, temp_templates_dir, mock_validator):
        """Test enhance command when enhancement fails."""
        with patch('blastdock.cli.templates.TemplateValidator', return_value=mock_validator):
            mock_validator.templates_dir = temp_templates_dir
            
            # Mock template needing enhancement
            mock_analysis = Mock()
            mock_analysis.traefik_compatibility = TraefikCompatibility.NONE
            mock_analysis.error_count = 1
            mock_analysis.warning_count = 2
            mock_analysis.score = 60
            
            mock_validator.validate_all_templates.return_value = {'nginx': mock_analysis}
            mock_validator.enhance_template_traefik_support.return_value = (False, 'Enhancement failed')
            
            # Mock user confirming
            with patch('click.confirm', return_value=True):
                result = runner.invoke(enhance, ['-d', str(temp_templates_dir)])
                
                assert result.exit_code == 0
                assert 'Failed to enhance' in result.output