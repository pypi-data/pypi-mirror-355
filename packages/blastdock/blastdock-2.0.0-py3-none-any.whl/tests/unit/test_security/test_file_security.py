"""Comprehensive tests for security file_security module."""

import os
import shutil
import tempfile
import hashlib
import stat
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import pytest

from blastdock.security.file_security import SecureFileOperations, get_secure_file_operations


class TestSecureFileOperations:
    """Test suite for SecureFileOperations."""

    @pytest.fixture
    def file_ops(self):
        """Create a SecureFileOperations instance."""
        return SecureFileOperations()

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup after test
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def test_file_content(self):
        """Sample file content for testing."""
        return "# Test configuration file\nkey: value\npassword: secret123\n"

    def test_init(self, file_ops):
        """Test SecureFileOperations initialization."""
        assert file_ops.logger is not None
        assert '.yml' in file_ops.SAFE_CONFIG_EXTENSIONS
        assert '.exe' in file_ops.DANGEROUS_EXTENSIONS
        assert file_ops.MAX_CONFIG_SIZE == 10 * 1024 * 1024

    def test_validate_file_path_valid(self, file_ops):
        """Test file path validation with valid paths."""
        valid, error = file_ops.validate_file_path('config.yml')
        assert valid is True
        assert error is None

        valid, error = file_ops.validate_file_path('subdir/template.yaml')
        assert valid is True
        assert error is None

    def test_validate_file_path_empty(self, file_ops):
        """Test file path validation with empty path."""
        valid, error = file_ops.validate_file_path('')
        assert valid is False
        assert 'empty' in error.lower()

    def test_validate_file_path_traversal(self, file_ops):
        """Test file path validation with path traversal attempts."""
        valid, error = file_ops.validate_file_path('../etc/passwd')
        assert valid is False
        assert 'traversal' in error.lower()

        valid, error = file_ops.validate_file_path('../../secret.txt')
        assert valid is False
        assert 'traversal' in error.lower()

    def test_validate_file_path_absolute(self, file_ops):
        """Test file path validation with absolute paths."""
        valid, error = file_ops.validate_file_path('/etc/passwd')
        assert valid is False
        assert 'absolute' in error.lower()

    def test_validate_file_path_dangerous_extension(self, file_ops):
        """Test file path validation with dangerous extensions."""
        valid, error = file_ops.validate_file_path('malware.exe')
        assert valid is False
        assert 'dangerous' in error.lower()

        valid, error = file_ops.validate_file_path('script.sh')
        assert valid is False
        assert 'dangerous' in error.lower()

    def test_validate_file_path_allowed_extensions(self, file_ops):
        """Test file path validation with allowed extensions filter."""
        allowed = {'.yml', '.yaml'}
        
        valid, error = file_ops.validate_file_path('config.yml', allowed_extensions=allowed)
        assert valid is True
        assert error is None

        valid, error = file_ops.validate_file_path('config.json', allowed_extensions=allowed)
        assert valid is False
        assert 'not allowed' in error.lower()

    def test_validate_file_path_base_directory(self, file_ops, temp_dir):
        """Test file path validation with base directory restriction."""
        valid, error = file_ops.validate_file_path('config.yml', base_dir=temp_dir)
        assert valid is True
        assert error is None

    def test_validate_file_path_escape_base_directory(self, file_ops, temp_dir):
        """Test file path validation preventing escape from base directory."""
        # Create symlink that points outside base directory
        outside_dir = tempfile.mkdtemp()
        try:
            link_path = os.path.join(temp_dir, 'escape_link')
            os.symlink(outside_dir, link_path)
            
            valid, error = file_ops.validate_file_path('escape_link/secret.txt', base_dir=temp_dir)
            assert valid is False
            assert 'escapes' in error.lower()
        finally:
            shutil.rmtree(outside_dir, ignore_errors=True)

    def test_safe_read_file_success(self, file_ops, temp_dir, test_file_content):
        """Test successful file reading."""
        test_file = os.path.join(temp_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write(test_file_content)
        
        success, content, error = file_ops.safe_read_file(test_file)
        
        assert success is True
        assert content == test_file_content
        assert error is None

    def test_safe_read_file_not_exists(self, file_ops):
        """Test reading non-existent file."""
        success, content, error = file_ops.safe_read_file('/nonexistent/file.txt')
        
        assert success is False
        assert content == ""
        assert 'not exist' in error.lower()

    def test_safe_read_file_too_large(self, file_ops, temp_dir):
        """Test reading file that's too large."""
        test_file = os.path.join(temp_dir, 'large.txt')
        with open(test_file, 'w') as f:
            f.write('x' * (file_ops.MAX_CONFIG_SIZE + 1))
        
        success, content, error = file_ops.safe_read_file(test_file)
        
        assert success is False
        assert 'too large' in error.lower()

    def test_safe_read_file_custom_max_size(self, file_ops, temp_dir):
        """Test reading file with custom max size."""
        test_file = os.path.join(temp_dir, 'test.txt')
        content = 'x' * 1000
        with open(test_file, 'w') as f:
            f.write(content)
        
        success, result, error = file_ops.safe_read_file(test_file, max_size=500)
        
        assert success is False
        assert 'too large' in error.lower()

    def test_safe_read_file_encoding_error(self, file_ops, temp_dir):
        """Test reading file with encoding error."""
        test_file = os.path.join(temp_dir, 'binary.txt')
        with open(test_file, 'wb') as f:
            f.write(b'\xff\xfe\x00\x01')  # Invalid UTF-8
        
        success, content, error = file_ops.safe_read_file(test_file)
        
        assert success is False
        assert 'encoding' in error.lower()

    def test_safe_read_file_permission_denied(self, file_ops, temp_dir):
        """Test reading file with permission denied."""
        test_file = os.path.join(temp_dir, 'no_read.txt')
        with open(test_file, 'w') as f:
            f.write('secret')
        
        # Remove read permission
        os.chmod(test_file, 0o000)
        
        try:
            success, content, error = file_ops.safe_read_file(test_file)
            
            assert success is False
            assert 'readable' in error.lower() or 'permission' in error.lower()
        finally:
            # Restore permissions for cleanup
            os.chmod(test_file, 0o644)

    def test_safe_write_file_success(self, file_ops, temp_dir):
        """Test successful file writing."""
        test_file = 'output.txt'
        content = "test content"
        
        # Mock validation to focus on core functionality
        with patch.object(file_ops, 'validate_file_path', return_value=(True, None)):
            with patch('os.makedirs'):
                with patch('tempfile.mkstemp') as mock_mkstemp:
                    with patch('os.fdopen', mock_open()) as mock_fdopen:
                        with patch('os.chmod'):
                            with patch('shutil.move'):
                                success, error = file_ops.safe_write_file(test_file, content)
        
        assert success is True
        assert error is None

    def test_safe_write_file_invalid_path(self, file_ops):
        """Test writing file with invalid path."""
        success, error = file_ops.safe_write_file('../escape.txt', 'content')
        
        assert success is False
        assert 'traversal' in error.lower()

    def test_safe_write_file_content_too_large(self, file_ops, temp_dir):
        """Test writing content that's too large."""
        test_file = 'large.txt'
        large_content = 'x' * (file_ops.MAX_CONFIG_SIZE + 1)
        
        # Mock validation to focus on size check
        with patch.object(file_ops, 'validate_file_path', return_value=(True, None)):
            success, error = file_ops.safe_write_file(test_file, large_content)
        
        assert success is False
        assert 'too large' in error.lower()

    def test_safe_write_file_with_backup(self, file_ops, temp_dir):
        """Test writing file with backup creation."""
        test_file = os.path.join(temp_dir, 'config.txt')
        original_content = "original content"
        new_content = "new content"
        
        # Write original file
        with open(test_file, 'w') as f:
            f.write(original_content)
        
        # Update with backup
        success, error = file_ops.safe_write_file(test_file, new_content, create_backup=True)
        
        assert success is True
        assert error is None
        
        # Check new content
        with open(test_file, 'r') as f:
            assert f.read() == new_content
        
        # Check backup exists
        backup_file = f"{test_file}.backup"
        assert os.path.exists(backup_file)
        with open(backup_file, 'r') as f:
            assert f.read() == original_content

    def test_safe_write_file_directory_creation(self, file_ops, temp_dir):
        """Test writing file with directory creation."""
        test_file = os.path.join(temp_dir, 'subdir', 'config.txt')
        content = "test content"
        
        success, error = file_ops.safe_write_file(test_file, content)
        
        assert success is True
        assert os.path.exists(test_file)
        assert os.path.exists(os.path.dirname(test_file))

    def test_safe_copy_file_success(self, file_ops, temp_dir, test_file_content):
        """Test successful file copying."""
        src_file = os.path.join(temp_dir, 'source.txt')
        dst_file = os.path.join(temp_dir, 'destination.txt')
        
        with open(src_file, 'w') as f:
            f.write(test_file_content)
        
        success, error = file_ops.safe_copy_file(src_file, dst_file)
        
        assert success is True
        assert error is None
        assert os.path.exists(dst_file)
        
        with open(dst_file, 'r') as f:
            assert f.read() == test_file_content

    def test_safe_copy_file_source_not_exists(self, file_ops, temp_dir):
        """Test copying non-existent source file."""
        src_file = os.path.join(temp_dir, 'nonexistent.txt')
        dst_file = os.path.join(temp_dir, 'destination.txt')
        
        success, error = file_ops.safe_copy_file(src_file, dst_file)
        
        assert success is False
        assert 'not exist' in error.lower()

    def test_safe_copy_file_invalid_paths(self, file_ops, temp_dir):
        """Test copying with invalid paths."""
        src_file = os.path.join(temp_dir, 'source.txt')
        with open(src_file, 'w') as f:
            f.write('content')
        
        success, error = file_ops.safe_copy_file(src_file, '../escape.txt')
        
        assert success is False
        assert 'invalid' in error.lower()

    def test_safe_copy_file_too_large(self, file_ops, temp_dir):
        """Test copying file that's too large."""
        src_file = os.path.join(temp_dir, 'large.txt')
        dst_file = os.path.join(temp_dir, 'destination.txt')
        
        with open(src_file, 'w') as f:
            f.write('x' * (file_ops.MAX_CONFIG_SIZE + 1))
        
        success, error = file_ops.safe_copy_file(src_file, dst_file)
        
        assert success is False
        assert 'too large' in error.lower()

    def test_safe_copy_file_preserve_permissions(self, file_ops, temp_dir):
        """Test copying file with preserved permissions."""
        src_file = os.path.join(temp_dir, 'source.txt')
        dst_file = os.path.join(temp_dir, 'destination.txt')
        
        with open(src_file, 'w') as f:
            f.write('content')
        os.chmod(src_file, 0o600)
        
        success, error = file_ops.safe_copy_file(src_file, dst_file, preserve_permissions=True)
        
        assert success is True
        # Check that permissions are similar (may not be exact due to umask)
        src_stat = os.stat(src_file)
        dst_stat = os.stat(dst_file)
        assert src_stat.st_mode == dst_stat.st_mode

    def test_safe_delete_file_success(self, file_ops, temp_dir):
        """Test successful file deletion."""
        test_file = os.path.join(temp_dir, 'delete_me.txt')
        with open(test_file, 'w') as f:
            f.write('content')
        
        success, error = file_ops.safe_delete_file(test_file)
        
        assert success is True
        assert error is None
        assert not os.path.exists(test_file)

    def test_safe_delete_file_not_exists(self, file_ops):
        """Test deleting non-existent file."""
        success, error = file_ops.safe_delete_file('/nonexistent/file.txt')
        
        assert success is True  # Consider it successful if already gone
        assert error is None

    def test_safe_delete_file_invalid_path(self, file_ops):
        """Test deleting file with invalid path."""
        success, error = file_ops.safe_delete_file('../escape.txt')
        
        assert success is False
        assert 'traversal' in error.lower()

    def test_safe_delete_file_secure_deletion(self, file_ops, temp_dir):
        """Test secure file deletion."""
        test_file = os.path.join(temp_dir, 'secure_delete.txt')
        content = 'sensitive data that should be overwritten'
        
        with open(test_file, 'w') as f:
            f.write(content)
        
        success, error = file_ops.safe_delete_file(test_file, secure_delete=True)
        
        assert success is True
        assert error is None
        assert not os.path.exists(test_file)

    def test_calculate_file_hash_success(self, file_ops, temp_dir):
        """Test successful file hash calculation."""
        test_file = os.path.join(temp_dir, 'hash_test.txt')
        content = 'test content for hashing'
        
        with open(test_file, 'w') as f:
            f.write(content)
        
        success, hash_value, error = file_ops.calculate_file_hash(test_file)
        
        assert success is True
        assert error is None
        assert len(hash_value) == 64  # SHA-256 hash length
        
        # Verify hash is correct
        expected = hashlib.sha256(content.encode()).hexdigest()
        assert hash_value == expected

    def test_calculate_file_hash_different_algorithms(self, file_ops, temp_dir):
        """Test file hash calculation with different algorithms."""
        test_file = os.path.join(temp_dir, 'hash_test.txt')
        content = 'test content'
        
        with open(test_file, 'w') as f:
            f.write(content)
        
        algorithms = ['md5', 'sha1', 'sha256', 'sha512']
        expected_lengths = [32, 40, 64, 128]
        
        for algo, expected_len in zip(algorithms, expected_lengths):
            success, hash_value, error = file_ops.calculate_file_hash(test_file, algo)
            assert success is True
            assert len(hash_value) == expected_len

    def test_calculate_file_hash_not_exists(self, file_ops):
        """Test hash calculation for non-existent file."""
        success, hash_value, error = file_ops.calculate_file_hash('/nonexistent/file.txt')
        
        assert success is False
        assert hash_value == ""
        assert 'not exist' in error.lower()

    def test_calculate_file_hash_unsupported_algorithm(self, file_ops, temp_dir):
        """Test hash calculation with unsupported algorithm."""
        test_file = os.path.join(temp_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('content')
        
        success, hash_value, error = file_ops.calculate_file_hash(test_file, 'unsupported')
        
        assert success is False
        assert 'unsupported' in error.lower()

    def test_verify_file_integrity_success(self, file_ops, temp_dir):
        """Test successful file integrity verification."""
        test_file = os.path.join(temp_dir, 'integrity_test.txt')
        content = 'test content'
        
        with open(test_file, 'w') as f:
            f.write(content)
        
        expected_hash = hashlib.sha256(content.encode()).hexdigest()
        success, error = file_ops.verify_file_integrity(test_file, expected_hash)
        
        assert success is True
        assert error is None

    def test_verify_file_integrity_mismatch(self, file_ops, temp_dir):
        """Test file integrity verification with hash mismatch."""
        test_file = os.path.join(temp_dir, 'integrity_test.txt')
        with open(test_file, 'w') as f:
            f.write('test content')
        
        wrong_hash = 'wrong_hash_value'
        success, error = file_ops.verify_file_integrity(test_file, wrong_hash)
        
        assert success is False
        assert 'mismatch' in error.lower()

    def test_check_file_permissions_success(self, file_ops, temp_dir):
        """Test checking file permissions."""
        test_file = os.path.join(temp_dir, 'perm_test.txt')
        with open(test_file, 'w') as f:
            f.write('content')
        os.chmod(test_file, 0o644)
        
        result = file_ops.check_file_permissions(test_file)
        
        assert result['exists'] is True
        assert result['permissions']['owner_read'] is True
        assert result['permissions']['owner_write'] is True
        assert result['permissions']['owner_execute'] is False
        assert result['octal'] == '644'

    def test_check_file_permissions_not_exists(self, file_ops):
        """Test checking permissions for non-existent file."""
        result = file_ops.check_file_permissions('/nonexistent/file.txt')
        
        assert result['exists'] is False
        assert 'error' in result

    def test_check_file_permissions_security_issues(self, file_ops, temp_dir):
        """Test checking file permissions with security issues."""
        test_file = os.path.join(temp_dir, 'insecure.txt')
        with open(test_file, 'w') as f:
            f.write('content')
        
        # Make file world-writable
        os.chmod(test_file, 0o666)
        
        result = file_ops.check_file_permissions(test_file)
        
        assert result['exists'] is True
        assert result['is_secure'] is False
        assert len(result['security_issues']) > 0
        assert any('world-writable' in issue for issue in result['security_issues'])

    def test_set_secure_permissions_file(self, file_ops, temp_dir):
        """Test setting secure permissions on a file."""
        test_file = os.path.join(temp_dir, 'secure_file.txt')
        with open(test_file, 'w') as f:
            f.write('content')
        
        success, error = file_ops.set_secure_permissions(test_file, is_directory=False)
        
        assert success is True
        assert error is None
        
        # Check permissions
        stat_info = os.stat(test_file)
        assert oct(stat_info.st_mode)[-3:] == '644'

    def test_set_secure_permissions_directory(self, file_ops, temp_dir):
        """Test setting secure permissions on a directory."""
        test_dir = os.path.join(temp_dir, 'secure_dir')
        os.makedirs(test_dir)
        
        success, error = file_ops.set_secure_permissions(test_dir, is_directory=True)
        
        assert success is True
        assert error is None
        
        # Check permissions
        stat_info = os.stat(test_dir)
        assert oct(stat_info.st_mode)[-3:] == '755'

    def test_set_secure_permissions_not_exists(self, file_ops):
        """Test setting permissions on non-existent file."""
        success, error = file_ops.set_secure_permissions('/nonexistent/file.txt')
        
        assert success is False
        assert 'not exist' in error.lower()

    def test_create_secure_directory_success(self, file_ops, temp_dir):
        """Test creating secure directory."""
        new_dir = os.path.join(temp_dir, 'new_secure_dir')
        
        success, error = file_ops.create_secure_directory(new_dir)
        
        assert success is True
        assert error is None
        assert os.path.exists(new_dir)
        assert os.path.isdir(new_dir)
        
        # Check permissions
        stat_info = os.stat(new_dir)
        assert oct(stat_info.st_mode)[-3:] == '755'

    def test_create_secure_directory_invalid_path(self, file_ops):
        """Test creating directory with invalid path."""
        success, error = file_ops.create_secure_directory('../escape_dir')
        
        assert success is False
        assert 'traversal' in error.lower()

    def test_scan_directory_security_success(self, file_ops, temp_dir):
        """Test scanning directory security."""
        # Create test files
        test_file = os.path.join(temp_dir, 'normal.txt')
        with open(test_file, 'w') as f:
            f.write('content')
        
        # Create subdirectory
        sub_dir = os.path.join(temp_dir, 'subdir')
        os.makedirs(sub_dir)
        
        result = file_ops.scan_directory_security(temp_dir)
        
        assert result['exists'] is True
        assert result['file_count'] >= 1
        assert result['directory_count'] >= 1
        assert result['total_size'] > 0

    def test_scan_directory_security_not_exists(self, file_ops):
        """Test scanning non-existent directory."""
        result = file_ops.scan_directory_security('/nonexistent/directory')
        
        assert result['exists'] is False
        assert 'error' in result

    def test_scan_directory_security_with_dangerous_files(self, file_ops, temp_dir):
        """Test scanning directory with dangerous files."""
        # Create dangerous file
        dangerous_file = os.path.join(temp_dir, 'malware.exe')
        with open(dangerous_file, 'w') as f:
            f.write('malicious content')
        
        result = file_ops.scan_directory_security(temp_dir)
        
        assert result['exists'] is True
        assert result['is_secure'] is False
        assert len(result['security_issues']) > 0
        assert any('dangerous' in issue.lower() for issue in result['security_issues'])
        assert len(result['insecure_files']) > 0

    def test_get_temp_directory(self, file_ops):
        """Test getting secure temporary directory."""
        temp_dir = file_ops.get_temp_directory()
        
        assert os.path.exists(temp_dir)
        assert os.path.isdir(temp_dir)
        assert 'blastdock_' in temp_dir
        
        # Check permissions
        stat_info = os.stat(temp_dir)
        assert oct(stat_info.st_mode)[-3:] == '700'
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_cleanup_temp_directory_success(self, file_ops):
        """Test successful cleanup of temporary directory."""
        temp_dir = file_ops.get_temp_directory()
        
        success = file_ops.cleanup_temp_directory(temp_dir)
        
        assert success is True
        assert not os.path.exists(temp_dir)

    def test_cleanup_temp_directory_not_exists(self, file_ops):
        """Test cleanup of non-existent directory."""
        nonexistent_dir = '/tmp/nonexistent_blastdock_temp'
        
        success = file_ops.cleanup_temp_directory(nonexistent_dir)
        
        assert success is False

    def test_cleanup_temp_directory_invalid_path(self, file_ops):
        """Test cleanup with invalid temp directory path."""
        invalid_dir = '/etc/not_temp_dir'
        
        success = file_ops.cleanup_temp_directory(invalid_dir)
        
        assert success is False

    def test_get_secure_file_operations_singleton(self):
        """Test the global secure file operations singleton."""
        ops1 = get_secure_file_operations()
        ops2 = get_secure_file_operations()
        
        assert isinstance(ops1, SecureFileOperations)
        assert ops1 is ops2  # Should be the same instance

    def test_safe_write_file_atomic_operation(self, file_ops, temp_dir):
        """Test that file writing is atomic (uses temporary file)."""
        test_file = os.path.join(temp_dir, 'atomic.txt')
        
        # Mock tempfile to verify atomic operation
        with patch('tempfile.mkstemp') as mock_mkstemp:
            temp_fd = 999
            temp_path = os.path.join(temp_dir, 'temp_atomic')
            mock_mkstemp.return_value = (temp_fd, temp_path)
            
            with patch('os.fdopen', mock_open()) as mock_fdopen:
                with patch('shutil.move') as mock_move:
                    with patch('os.chmod') as mock_chmod:
                        success, error = file_ops.safe_write_file(test_file, 'content')
            
            # Verify atomic operation
            mock_mkstemp.assert_called_once()
            mock_move.assert_called_once_with(temp_path, test_file)

    def test_file_size_validation_edge_cases(self, file_ops, temp_dir):
        """Test file size validation edge cases."""
        # Test file exactly at size limit
        test_file = os.path.join(temp_dir, 'exact_limit.txt')
        content = 'x' * file_ops.MAX_CONFIG_SIZE
        
        with open(test_file, 'w') as f:
            f.write(content)
        
        # Should succeed at exact limit
        success, result, error = file_ops.safe_read_file(test_file)
        assert success is True
        assert len(result) == file_ops.MAX_CONFIG_SIZE

    def test_multiple_security_issues(self, file_ops, temp_dir):
        """Test file with multiple security issues."""
        # Create file with multiple security problems
        insecure_file = os.path.join(temp_dir, 'very_insecure.exe')
        with open(insecure_file, 'w') as f:
            f.write('malicious content')
        
        # Make it world-writable and executable
        os.chmod(insecure_file, 0o777)
        
        result = file_ops.check_file_permissions(insecure_file)
        
        assert result['exists'] is True
        assert result['is_secure'] is False
        assert len(result['security_issues']) >= 2  # Multiple issues
        
        # Should also be flagged in directory scan
        dir_result = file_ops.scan_directory_security(temp_dir)
        assert dir_result['is_secure'] is False
        assert len(dir_result['security_issues']) >= 2