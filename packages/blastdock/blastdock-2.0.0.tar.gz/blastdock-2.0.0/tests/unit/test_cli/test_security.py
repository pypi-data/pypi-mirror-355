"""Comprehensive tests for CLI security module."""

import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
import pytest
from click.testing import CliRunner

from blastdock.cli.security import (
    security, scan, validate_template, check_docker, audit, config
)


class TestSecurityCLI:
    """Test suite for security CLI commands."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def mock_security_validator(self):
        """Create mock security validator."""
        validator = Mock()
        validator.get_security_report.return_value = {
            'overall_score': 85,
            'issues_found': 3,
            'recommendations': ['Use non-root users', 'Enable SSL']
        }
        return validator

    @pytest.fixture
    def mock_docker_security_checker(self):
        """Create mock Docker security checker."""
        checker = Mock()
        checker.check_docker_daemon_security.return_value = {
            'accessible': True,
            'security_score': 75,
            'security_issues': [
                {
                    'severity': 'medium',
                    'issue': 'Docker daemon running as root',
                    'recommendation': 'Configure rootless mode'
                }
            ],
            'daemon_info': {
                'version': '24.0.7',
                'security_options': ['apparmor', 'seccomp']
            }
        }
        checker.check_container_security.return_value = {
            'container': 'test-container',
            'accessible': True,
            'security_score': 80,
            'security_issues': [],
            'configuration': {}
        }
        checker.check_image_security.return_value = {
            'image': 'nginx:latest',
            'accessible': True,
            'security_score': 70,
            'security_issues': [
                {
                    'severity': 'low',
                    'issue': 'Using latest tag',
                    'recommendation': 'Use specific version tags'
                }
            ],
            'metadata': {}
        }
        return checker

    @pytest.fixture
    def mock_template_security_scanner(self):
        """Create mock template security scanner."""
        scanner = Mock()
        scanner.scan_all_templates.return_value = {
            'accessible': True,
            'templates_scanned': 5,
            'templates_with_issues': 2,
            'average_security_score': 82.5,
            'total_issues': 3,
            'issues_by_severity': {
                'critical': 0,
                'high': 1,
                'medium': 2,
                'low': 0
            },
            'all_issues': [
                {
                    'template': 'nginx',
                    'severity': 'high',
                    'issue': 'Hardcoded password detected',
                    'recommendation': 'Use environment variables'
                }
            ],
            'summary': ['Found 3 issues across 5 templates']
        }
        scanner.scan_template.return_value = {
            'template_path': '/path/to/template.yml',
            'accessible': True,
            'security_score': 75,
            'security_issues': [
                {
                    'severity': 'medium',
                    'issue': 'Root user detected',
                    'recommendation': 'Use non-root user'
                }
            ],
            'scan_type': 'file'
        }
        return scanner

    @pytest.fixture
    def mock_config_security(self):
        """Create mock config security."""
        config_sec = Mock()
        config_sec.get_security_status.return_value = {
            'encryption_enabled': True,
            'secure_storage': True,
            'access_controls': True,
            'last_audit': '2023-01-01T12:00:00Z'
        }
        config_sec.audit_configuration.return_value = {
            'total_configs': 10,
            'secure_configs': 8,
            'insecure_configs': 2,
            'recommendations': ['Enable encryption for sensitive values']
        }
        return config_sec

    @pytest.fixture
    def mock_secure_file_operations(self):
        """Create mock secure file operations."""
        file_ops = Mock()
        file_ops.scan_directory_security.return_value = {
            'exists': True,
            'file_count': 25,
            'directory_count': 5,
            'security_issues': ['World-writable file found'],
            'insecure_files': ['/path/to/insecure/file'],
            'is_secure': False
        }
        return file_ops

    def test_security_group(self, runner):
        """Test security command group."""
        result = runner.invoke(security, ['--help'])
        
        assert result.exit_code == 0
        assert 'Security validation and management commands' in result.output

    def test_scan_command_basic(self, runner, mock_security_validator, mock_docker_security_checker, 
                               mock_template_security_scanner, mock_config_security):
        """Test basic security scan command."""
        with patch('blastdock.cli.security.get_security_validator', return_value=mock_security_validator):
            with patch('blastdock.cli.security.get_docker_security_checker', return_value=mock_docker_security_checker):
                with patch('blastdock.cli.security.get_template_security_scanner', return_value=mock_template_security_scanner):
                    with patch('blastdock.cli.security.get_config_security', return_value=mock_config_security):
                        with patch('os.path.exists', return_value=True):
                            result = runner.invoke(scan)
                            
                            assert result.exit_code == 0
                            assert 'BlastDock Security Scan' in result.output

    def test_scan_command_json_format(self, runner, mock_security_validator, mock_docker_security_checker,
                                    mock_template_security_scanner, mock_config_security):
        """Test security scan with JSON output format."""
        with patch('blastdock.cli.security.get_security_validator', return_value=mock_security_validator):
            with patch('blastdock.cli.security.get_docker_security_checker', return_value=mock_docker_security_checker):
                with patch('blastdock.cli.security.get_template_security_scanner', return_value=mock_template_security_scanner):
                    with patch('blastdock.cli.security.get_config_security', return_value=mock_config_security):
                        with patch('os.path.exists', return_value=True):
                            result = runner.invoke(scan, ['--format', 'json'])
                            
                            assert result.exit_code == 0
                            assert '{' in result.output

    def test_scan_command_save_report(self, runner, mock_security_validator, mock_docker_security_checker,
                                    mock_template_security_scanner, mock_config_security):
        """Test security scan with report saving."""
        with patch('blastdock.cli.security.get_security_validator', return_value=mock_security_validator):
            with patch('blastdock.cli.security.get_docker_security_checker', return_value=mock_docker_security_checker):
                with patch('blastdock.cli.security.get_template_security_scanner', return_value=mock_template_security_scanner):
                    with patch('blastdock.cli.security.get_config_security', return_value=mock_config_security):
                        with patch('os.path.exists', return_value=True):
                            with tempfile.NamedTemporaryFile(mode='w', delete=False) as report_file:
                                result = runner.invoke(scan, ['--save-report', report_file.name])
                                
                                assert result.exit_code == 0
                                assert 'Security report saved' in result.output
                                
                                # Cleanup
                                os.unlink(report_file.name)

    def test_scan_command_project_specific(self, runner, mock_security_validator, mock_docker_security_checker,
                                         mock_template_security_scanner, mock_config_security):
        """Test security scan for specific project."""
        with patch('blastdock.cli.security.get_security_validator', return_value=mock_security_validator):
            with patch('blastdock.cli.security.get_docker_security_checker', return_value=mock_docker_security_checker):
                with patch('blastdock.cli.security.get_template_security_scanner', return_value=mock_template_security_scanner):
                    with patch('blastdock.cli.security.get_config_security', return_value=mock_config_security):
                        with patch('os.path.exists', return_value=True):
                            result = runner.invoke(scan, ['--project', 'test-project'])
                            
                            assert result.exit_code == 0

    def test_scan_command_templates_not_exist(self, runner, mock_security_validator, mock_docker_security_checker,
                                            mock_template_security_scanner, mock_config_security):
        """Test security scan when templates directory doesn't exist."""
        with patch('blastdock.cli.security.get_security_validator', return_value=mock_security_validator):
            with patch('blastdock.cli.security.get_docker_security_checker', return_value=mock_docker_security_checker):
                with patch('blastdock.cli.security.get_template_security_scanner', return_value=mock_template_security_scanner):
                    with patch('blastdock.cli.security.get_config_security', return_value=mock_config_security):
                        with patch('os.path.exists', return_value=False):
                            result = runner.invoke(scan)
                            
                            assert result.exit_code == 0

    def test_validate_template_command_success(self, runner, mock_template_security_scanner):
        """Test validate-template command with successful validation."""
        with patch('blastdock.cli.security.get_template_security_scanner', return_value=mock_template_security_scanner):
            result = runner.invoke(validate_template, ['/path/to/template.yml'])
            
            assert result.exit_code == 0
            assert 'Template Security Validation' in result.output
            mock_template_security_scanner.scan_template.assert_called_once_with('/path/to/template.yml')

    def test_validate_template_command_json_format(self, runner, mock_template_security_scanner):
        """Test validate-template command with JSON output."""
        with patch('blastdock.cli.security.get_template_security_scanner', return_value=mock_template_security_scanner):
            result = runner.invoke(validate_template, ['/path/to/template.yml', '--format', 'json'])
            
            assert result.exit_code == 0
            assert '{' in result.output

    def test_validate_template_command_inaccessible(self, runner, mock_template_security_scanner):
        """Test validate-template command with inaccessible template."""
        mock_template_security_scanner.scan_template.return_value = {
            'template_path': '/path/to/template.yml',
            'accessible': False,
            'error': 'File not found'
        }
        
        with patch('blastdock.cli.security.get_template_security_scanner', return_value=mock_template_security_scanner):
            result = runner.invoke(validate_template, ['/path/to/template.yml'])
            
            assert result.exit_code == 0
            assert 'Error validating template' in result.output

    def test_check_docker_command_daemon(self, runner, mock_docker_security_checker):
        """Test check-docker command for daemon security."""
        with patch('blastdock.cli.security.get_docker_security_checker', return_value=mock_docker_security_checker):
            result = runner.invoke(check_docker, ['daemon'])
            
            assert result.exit_code == 0
            assert 'Docker Daemon Security Check' in result.output
            mock_docker_security_checker.check_docker_daemon_security.assert_called_once()

    def test_check_docker_command_container(self, runner, mock_docker_security_checker):
        """Test check-docker command for container security."""
        with patch('blastdock.cli.security.get_docker_security_checker', return_value=mock_docker_security_checker):
            result = runner.invoke(check_docker, ['container', 'test-container'])
            
            assert result.exit_code == 0
            assert 'Container Security Check' in result.output
            mock_docker_security_checker.check_container_security.assert_called_once_with('test-container')

    def test_check_docker_command_image(self, runner, mock_docker_security_checker):
        """Test check-docker command for image security."""
        with patch('blastdock.cli.security.get_docker_security_checker', return_value=mock_docker_security_checker):
            result = runner.invoke(check_docker, ['image', 'nginx:latest'])
            
            assert result.exit_code == 0
            assert 'Image Security Check' in result.output
            mock_docker_security_checker.check_image_security.assert_called_once_with('nginx:latest')

    def test_check_docker_command_json_format(self, runner, mock_docker_security_checker):
        """Test check-docker command with JSON output."""
        with patch('blastdock.cli.security.get_docker_security_checker', return_value=mock_docker_security_checker):
            result = runner.invoke(check_docker, ['daemon', '--format', 'json'])
            
            assert result.exit_code == 0
            assert '{' in result.output

    def test_check_docker_command_inaccessible(self, runner, mock_docker_security_checker):
        """Test check-docker command when Docker is inaccessible."""
        mock_docker_security_checker.check_docker_daemon_security.return_value = {
            'accessible': False,
            'error': 'Cannot connect to Docker daemon'
        }
        
        with patch('blastdock.cli.security.get_docker_security_checker', return_value=mock_docker_security_checker):
            result = runner.invoke(check_docker, ['daemon'])
            
            assert result.exit_code == 0
            assert 'Error checking Docker daemon' in result.output

    def test_audit_command_filesystem(self, runner, mock_secure_file_operations):
        """Test audit command for filesystem security."""
        with patch('blastdock.cli.security.get_secure_file_operations', return_value=mock_secure_file_operations):
            result = runner.invoke(audit, ['filesystem', '/path/to/audit'])
            
            assert result.exit_code == 0
            assert 'Filesystem Security Audit' in result.output
            mock_secure_file_operations.scan_directory_security.assert_called_once_with('/path/to/audit')

    def test_audit_command_filesystem_json_format(self, runner, mock_secure_file_operations):
        """Test audit command filesystem with JSON output."""
        with patch('blastdock.cli.security.get_secure_file_operations', return_value=mock_secure_file_operations):
            result = runner.invoke(audit, ['filesystem', '/path/to/audit', '--format', 'json'])
            
            assert result.exit_code == 0
            assert '{' in result.output

    def test_audit_command_filesystem_not_exist(self, runner, mock_secure_file_operations):
        """Test audit command when path doesn't exist."""
        mock_secure_file_operations.scan_directory_security.return_value = {
            'exists': False,
            'error': 'Directory does not exist'
        }
        
        with patch('blastdock.cli.security.get_secure_file_operations', return_value=mock_secure_file_operations):
            result = runner.invoke(audit, ['filesystem', '/nonexistent/path'])
            
            assert result.exit_code == 0
            assert 'Error auditing filesystem' in result.output

    def test_audit_command_permissions(self, runner):
        """Test audit command for permissions check."""
        with patch('blastdock.cli.security.get_secure_file_operations') as mock_get_file_ops:
            mock_file_ops = Mock()
            mock_file_ops.check_file_permissions.return_value = {
                'exists': True,
                'permissions': {
                    'owner_read': True,
                    'owner_write': True,
                    'group_read': True,
                    'other_read': False
                },
                'is_secure': True,
                'security_issues': []
            }
            mock_get_file_ops.return_value = mock_file_ops
            
            result = runner.invoke(audit, ['permissions', '/path/to/file'])
            
            assert result.exit_code == 0
            assert 'File Permissions Audit' in result.output

    def test_config_command_status(self, runner, mock_config_security):
        """Test config command to show status."""
        with patch('blastdock.cli.security.get_config_security', return_value=mock_config_security):
            result = runner.invoke(config, ['status'])
            
            assert result.exit_code == 0
            assert 'Configuration Security Status' in result.output
            mock_config_security.get_security_status.assert_called_once()

    def test_config_command_status_json_format(self, runner, mock_config_security):
        """Test config command status with JSON output."""
        with patch('blastdock.cli.security.get_config_security', return_value=mock_config_security):
            result = runner.invoke(config, ['status', '--format', 'json'])
            
            assert result.exit_code == 0
            assert '{' in result.output

    def test_config_command_audit(self, runner, mock_config_security):
        """Test config command to audit configuration."""
        with patch('blastdock.cli.security.get_config_security', return_value=mock_config_security):
            result = runner.invoke(config, ['audit'])
            
            assert result.exit_code == 0
            assert 'Configuration Security Audit' in result.output
            mock_config_security.audit_configuration.assert_called_once()

    def test_config_command_encrypt(self, runner, mock_config_security):
        """Test config command to encrypt value."""
        mock_config_security.encrypt_value.return_value = 'encrypted_value_123'
        
        with patch('blastdock.cli.security.get_config_security', return_value=mock_config_security):
            result = runner.invoke(config, ['encrypt', 'secret_value'])
            
            assert result.exit_code == 0
            assert 'encrypted_value_123' in result.output
            mock_config_security.encrypt_value.assert_called_once_with('secret_value')

    def test_config_command_decrypt(self, runner, mock_config_security):
        """Test config command to decrypt value."""
        mock_config_security.decrypt_value.return_value = 'decrypted_value'
        
        with patch('blastdock.cli.security.get_config_security', return_value=mock_config_security):
            result = runner.invoke(config, ['decrypt', 'encrypted_value_123'])
            
            assert result.exit_code == 0
            assert 'decrypted_value' in result.output
            mock_config_security.decrypt_value.assert_called_once_with('encrypted_value_123')

    def test_config_command_decrypt_failure(self, runner, mock_config_security):
        """Test config command decrypt when decryption fails."""
        mock_config_security.decrypt_value.side_effect = Exception("Decryption failed")
        
        with patch('blastdock.cli.security.get_config_security', return_value=mock_config_security):
            result = runner.invoke(config, ['decrypt', 'invalid_encrypted_value'])
            
            assert result.exit_code == 0
            assert 'Failed to decrypt' in result.output

    def test_scan_command_save_report_failure(self, runner, mock_security_validator, mock_docker_security_checker,
                                            mock_template_security_scanner, mock_config_security):
        """Test security scan with report saving failure."""
        with patch('blastdock.cli.security.get_security_validator', return_value=mock_security_validator):
            with patch('blastdock.cli.security.get_docker_security_checker', return_value=mock_docker_security_checker):
                with patch('blastdock.cli.security.get_template_security_scanner', return_value=mock_template_security_scanner):
                    with patch('blastdock.cli.security.get_config_security', return_value=mock_config_security):
                        with patch('os.path.exists', return_value=True):
                            with patch('builtins.open', side_effect=IOError("Permission denied")):
                                result = runner.invoke(scan, ['--save-report', '/invalid/path/report.json'])
                                
                                assert result.exit_code == 0
                                assert 'Failed to save report' in result.output

    def test_validate_template_command_with_guidelines(self, runner, mock_template_security_scanner):
        """Test validate-template command with security guidelines."""
        mock_template_security_scanner.get_security_guidelines.return_value = [
            'Use minimal base images',
            'Run containers as non-root users',
            'Avoid privileged containers'
        ]
        
        with patch('blastdock.cli.security.get_template_security_scanner', return_value=mock_template_security_scanner):
            result = runner.invoke(validate_template, ['/path/to/template.yml', '--show-guidelines'])
            
            assert result.exit_code == 0
            assert 'Security Guidelines' in result.output

    def test_check_docker_command_container_inaccessible(self, runner, mock_docker_security_checker):
        """Test check-docker container command when container is inaccessible."""
        mock_docker_security_checker.check_container_security.return_value = {
            'container': 'nonexistent-container',
            'accessible': False,
            'error': 'Container not found'
        }
        
        with patch('blastdock.cli.security.get_docker_security_checker', return_value=mock_docker_security_checker):
            result = runner.invoke(check_docker, ['container', 'nonexistent-container'])
            
            assert result.exit_code == 0
            assert 'Error checking container' in result.output

    def test_check_docker_command_image_inaccessible(self, runner, mock_docker_security_checker):
        """Test check-docker image command when image is inaccessible."""
        mock_docker_security_checker.check_image_security.return_value = {
            'image': 'nonexistent:image',
            'accessible': False,
            'error': 'Image not found'
        }
        
        with patch('blastdock.cli.security.get_docker_security_checker', return_value=mock_docker_security_checker):
            result = runner.invoke(check_docker, ['image', 'nonexistent:image'])
            
            assert result.exit_code == 0
            assert 'Error checking image' in result.output