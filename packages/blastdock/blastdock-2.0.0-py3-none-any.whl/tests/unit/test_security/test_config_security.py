"""Comprehensive tests for security config_security module."""

import os
import json
import base64
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock
import pytest

from blastdock.security.config_security import ConfigurationSecurity, get_config_security
from blastdock.exceptions import SecurityError, ConfigurationError


class TestConfigurationSecurity:
    """Test suite for ConfigurationSecurity."""

    @pytest.fixture
    def config_security(self):
        """Create a ConfigurationSecurity instance."""
        return ConfigurationSecurity()

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup after test
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def sample_config(self):
        """Sample configuration for testing."""
        return {
            "app_name": "test_app",
            "database_password": "secret123",
            "api_key": "abc123def456",
            "server": {
                "host": "localhost",
                "port": 8080,
                "ssl_cert": "path/to/cert.pem"
            },
            "regular_setting": "normal_value"
        }

    @pytest.fixture
    def mock_paths(self):
        """Mock paths for testing."""
        with patch('blastdock.security.config_security.paths') as mock_paths:
            mock_paths.config_dir = '/tmp/test_config'
            yield mock_paths

    def test_init(self, config_security):
        """Test ConfigurationSecurity initialization."""
        assert config_security.logger is not None
        assert config_security.encryption_key is None
        assert config_security.key_derivation_iterations == 100000
        assert 'password' in config_security.SENSITIVE_KEYS
        assert 'secret' in config_security.SENSITIVE_KEYS
        assert 'api_key' in config_security.SENSITIVE_KEYS

    def test_is_sensitive_key(self, config_security):
        """Test sensitive key detection."""
        assert config_security._is_sensitive_key('password') is True
        assert config_security._is_sensitive_key('DATABASE_PASSWORD') is True
        assert config_security._is_sensitive_key('api_key') is True
        assert config_security._is_sensitive_key('secret_token') is True
        assert config_security._is_sensitive_key('ssl_cert') is True
        assert config_security._is_sensitive_key('normal_setting') is False
        assert config_security._is_sensitive_key('port') is False

    def test_looks_like_secret(self, config_security):
        """Test secret detection algorithm."""
        # Should detect as secrets
        assert config_security._looks_like_secret('abc123def456') is True
        assert config_security._looks_like_secret('P@ssw0rd123') is True
        assert config_security._looks_like_secret('sk-1234567890abcdef') is True
        
        # Should not detect as secrets
        assert config_security._looks_like_secret('password') is False
        assert config_security._looks_like_secret('changeme') is False
        assert config_security._looks_like_secret('${PASSWORD}') is False
        assert config_security._looks_like_secret('{{secret}}') is False
        assert config_security._looks_like_secret('short') is False
        assert config_security._looks_like_secret('example') is False

    @patch('blastdock.security.config_security.CRYPTOGRAPHY_AVAILABLE', True)
    def test_initialize_encryption_with_cryptography(self, config_security):
        """Test encryption initialization with cryptography library."""
        mock_fernet_class = Mock()
        mock_fernet_instance = Mock()
        mock_fernet_class.return_value = mock_fernet_instance
        mock_fernet_class.generate_key.return_value = b'test_key'
        
        with patch('blastdock.security.config_security.Fernet', mock_fernet_class):
            with patch.object(config_security, '_store_key', return_value=True):
                result = config_security.initialize_encryption()
        
        assert result is True
        assert config_security.encryption_key == mock_fernet_instance
        mock_fernet_class.generate_key.assert_called_once()

    @patch('blastdock.security.config_security.CRYPTOGRAPHY_AVAILABLE', True)
    def test_initialize_encryption_with_password(self, config_security):
        """Test encryption initialization with master password."""
        mock_pbkdf2_class = Mock()
        mock_kdf = Mock()
        mock_kdf.derive.return_value = b'derived_key'
        mock_pbkdf2_class.return_value = mock_kdf
        
        mock_fernet_class = Mock()
        mock_fernet_instance = Mock()
        mock_fernet_class.return_value = mock_fernet_instance
        
        with patch('blastdock.security.config_security.PBKDF2HMAC', mock_pbkdf2_class):
            with patch('blastdock.security.config_security.Fernet', mock_fernet_class):
                with patch.object(config_security, '_get_or_create_salt', return_value=b'salt'):
                    result = config_security.initialize_encryption('master_password')
        
        assert result is True
        assert config_security.encryption_key == mock_fernet_instance
        mock_kdf.derive.assert_called_once_with(b'master_password')

    @patch('blastdock.security.config_security.CRYPTOGRAPHY_AVAILABLE', False)
    def test_initialize_encryption_without_cryptography(self, config_security):
        """Test encryption initialization without cryptography library."""
        result = config_security.initialize_encryption()
        
        assert result is True
        assert config_security.encryption_key == "basic_fallback"

    @patch('blastdock.security.config_security.CRYPTOGRAPHY_AVAILABLE', True)
    def test_initialize_encryption_failure(self, config_security):
        """Test encryption initialization failure."""
        mock_fernet_class = Mock()
        mock_fernet_class.side_effect = Exception("Crypto error")
        
        with patch('blastdock.security.config_security.Fernet', mock_fernet_class):
            result = config_security.initialize_encryption()
        
        assert result is False

    def test_get_or_create_salt_existing(self, config_security, temp_dir):
        """Test getting existing salt file."""
        salt_file = os.path.join(temp_dir, '.blastdock_salt')
        test_salt = b'existing_salt'
        
        # Create existing salt file
        with open(salt_file, 'wb') as f:
            f.write(test_salt)
        
        with patch('blastdock.utils.filesystem.paths') as mock_paths:
            mock_paths.config_dir = temp_dir
            salt = config_security._get_or_create_salt()
        
        assert salt == test_salt

    def test_get_or_create_salt_new(self, config_security, temp_dir):
        """Test creating new salt file."""
        with patch('blastdock.utils.filesystem.paths') as mock_paths:
            mock_paths.config_dir = temp_dir
            with patch('os.urandom', return_value=b'new_salt'):
                salt = config_security._get_or_create_salt()
        
        assert salt == b'new_salt'
        
        # Verify salt file was created
        salt_file = os.path.join(temp_dir, '.blastdock_salt')
        assert os.path.exists(salt_file)
        
        with open(salt_file, 'rb') as f:
            stored_salt = f.read()
        assert stored_salt == b'new_salt'

    def test_get_or_create_salt_error(self, config_security):
        """Test salt creation with file error."""
        with patch('blastdock.utils.filesystem.paths') as mock_paths:
            mock_paths.config_dir = '/invalid/path'
            with patch('os.urandom', return_value=b'fallback_salt'):
                salt = config_security._get_or_create_salt()
        
        assert salt == b'fallback_salt'

    def test_store_key_success(self, config_security, temp_dir):
        """Test successful key storage."""
        test_key = b'test_encryption_key'
        
        with patch('blastdock.utils.filesystem.paths') as mock_paths:
            mock_paths.config_dir = temp_dir
            result = config_security._store_key(test_key)
        
        assert result is True
        
        # Verify key file was created
        key_file = os.path.join(temp_dir, '.blastdock_key')
        assert os.path.exists(key_file)
        
        with open(key_file, 'rb') as f:
            stored_key = f.read()
        assert stored_key == test_key
        
        # Verify secure permissions
        file_mode = os.stat(key_file).st_mode
        assert file_mode & 0o077 == 0  # No permissions for group/others

    def test_store_key_failure(self, config_security):
        """Test key storage failure."""
        test_key = b'test_key'
        
        with patch('blastdock.utils.filesystem.paths') as mock_paths:
            mock_paths.config_dir = '/invalid/path'
            with patch('os.makedirs', side_effect=OSError("Permission denied")):
                result = config_security._store_key(test_key)
        
        assert result is False

    @patch('blastdock.security.config_security.CRYPTOGRAPHY_AVAILABLE', True)
    def test_load_key_success(self, config_security, temp_dir):
        """Test successful key loading."""
        test_key = b'test_key'
        key_file = os.path.join(temp_dir, '.blastdock_key')
        
        # Create key file
        with open(key_file, 'wb') as f:
            f.write(test_key)
        
        mock_fernet_class = Mock()
        mock_fernet_instance = Mock()
        mock_fernet_class.return_value = mock_fernet_instance
        
        with patch('blastdock.security.config_security.Fernet', mock_fernet_class):
            with patch('blastdock.utils.filesystem.paths') as mock_paths:
                mock_paths.config_dir = temp_dir
                result = config_security._load_key()
        
        assert result is True
        assert config_security.encryption_key == mock_fernet_instance
        mock_fernet_class.assert_called_once_with(test_key)

    @patch('blastdock.security.config_security.CRYPTOGRAPHY_AVAILABLE', False)
    def test_load_key_without_cryptography(self, config_security):
        """Test key loading without cryptography library."""
        result = config_security._load_key()
        
        assert result is True
        assert config_security.encryption_key == "basic_fallback"

    def test_load_key_not_found(self, config_security, temp_dir):
        """Test key loading when key file doesn't exist."""
        with patch('blastdock.utils.filesystem.paths') as mock_paths:
            mock_paths.config_dir = temp_dir
            result = config_security._load_key()
        
        assert result is False

    @patch('blastdock.security.config_security.CRYPTOGRAPHY_AVAILABLE', True)
    def test_encrypt_value_with_cryptography(self, config_security):
        """Test value encryption with cryptography library."""
        mock_fernet = Mock()
        mock_fernet.encrypt.return_value = b'encrypted_data'
        config_security.encryption_key = mock_fernet
        
        result = config_security.encrypt_value('test_value')
        
        expected = base64.urlsafe_b64encode(b'encrypted_data').decode()
        assert result == expected
        mock_fernet.encrypt.assert_called_once_with(b'test_value')

    @patch('blastdock.security.config_security.CRYPTOGRAPHY_AVAILABLE', False)
    def test_encrypt_value_without_cryptography(self, config_security):
        """Test value encryption without cryptography library."""
        config_security.encryption_key = "basic_fallback"
        
        result = config_security.encrypt_value('test_value')
        
        expected = base64.urlsafe_b64encode(b'test_value').decode()
        assert result == expected

    def test_encrypt_value_no_key(self, config_security):
        """Test value encryption without initialized key."""
        with patch.object(config_security, '_load_key', return_value=False):
            with pytest.raises(SecurityError, match="Encryption not initialized"):
                config_security.encrypt_value('test_value')

    def test_encrypt_value_error(self, config_security):
        """Test value encryption with error."""
        mock_fernet = Mock()
        mock_fernet.encrypt.side_effect = Exception("Encryption error")
        config_security.encryption_key = mock_fernet
        
        with pytest.raises(SecurityError, match="Failed to encrypt value"):
            config_security.encrypt_value('test_value')

    @patch('blastdock.security.config_security.CRYPTOGRAPHY_AVAILABLE', True)
    def test_decrypt_value_with_cryptography(self, config_security):
        """Test value decryption with cryptography library."""
        mock_fernet = Mock()
        mock_fernet.decrypt.return_value = b'decrypted_data'
        config_security.encryption_key = mock_fernet
        
        # Prepare encrypted value
        encrypted_bytes = b'encrypted_data'
        encrypted_value = base64.urlsafe_b64encode(encrypted_bytes).decode()
        
        result = config_security.decrypt_value(encrypted_value)
        
        assert result == 'decrypted_data'
        mock_fernet.decrypt.assert_called_once_with(encrypted_bytes)

    @patch('blastdock.security.config_security.CRYPTOGRAPHY_AVAILABLE', False)
    def test_decrypt_value_without_cryptography(self, config_security):
        """Test value decryption without cryptography library."""
        config_security.encryption_key = "basic_fallback"
        
        # Prepare encoded value
        encoded_value = base64.urlsafe_b64encode(b'test_value').decode()
        
        result = config_security.decrypt_value(encoded_value)
        
        assert result == 'test_value'

    def test_decrypt_value_no_key(self, config_security):
        """Test value decryption without initialized key."""
        with patch.object(config_security, '_load_key', return_value=False):
            with pytest.raises(SecurityError, match="Encryption not initialized"):
                config_security.decrypt_value('encrypted_value')

    def test_decrypt_value_error(self, config_security):
        """Test value decryption with error."""
        mock_fernet = Mock()
        mock_fernet.decrypt.side_effect = Exception("Decryption error")
        config_security.encryption_key = mock_fernet
        
        encrypted_value = base64.urlsafe_b64encode(b'encrypted_data').decode()
        
        with pytest.raises(SecurityError, match="Failed to decrypt value"):
            config_security.decrypt_value(encrypted_value)

    def test_secure_config_encrypt_enabled(self, config_security, sample_config):
        """Test securing configuration with encryption enabled."""
        with patch.object(config_security, 'encrypt_value', return_value='encrypted_value'):
            result = config_security.secure_config(sample_config, encrypt_sensitive=True)
        
        assert result['app_name'] == 'test_app'  # Not sensitive
        assert result['database_password'] == 'encrypted:encrypted_value'  # Sensitive
        assert result['api_key'] == 'encrypted:encrypted_value'  # Sensitive
        assert result['server']['host'] == 'localhost'  # Not sensitive
        assert result['server']['ssl_cert'] == 'encrypted:encrypted_value'  # Sensitive
        assert result['regular_setting'] == 'normal_value'  # Not sensitive

    def test_secure_config_encrypt_disabled(self, config_security, sample_config):
        """Test securing configuration with encryption disabled."""
        result = config_security.secure_config(sample_config, encrypt_sensitive=False)
        
        assert result == sample_config  # Should be unchanged

    def test_secure_config_encryption_error(self, config_security, sample_config):
        """Test securing configuration with encryption error."""
        with patch.object(config_security, 'encrypt_value', side_effect=Exception("Encryption error")):
            result = config_security.secure_config(sample_config, encrypt_sensitive=True)
        
        # Should keep original values if encryption fails
        assert result['database_password'] == 'secret123'
        assert result['api_key'] == 'abc123def456'

    def test_unsecure_config(self, config_security):
        """Test unsecuring configuration."""
        secured_config = {
            'app_name': 'test_app',
            'database_password': 'encrypted:encrypted_value',
            'api_key': 'encrypted:another_encrypted_value',
            'server': {
                'host': 'localhost',
                'ssl_cert': 'encrypted:cert_encrypted_value'
            },
            'regular_setting': 'normal_value'
        }
        
        with patch.object(config_security, 'decrypt_value', side_effect=['decrypted_password', 'decrypted_key', 'decrypted_cert']):
            result = config_security.unsecure_config(secured_config)
        
        assert result['app_name'] == 'test_app'
        assert result['database_password'] == 'decrypted_password'
        assert result['api_key'] == 'decrypted_key'
        assert result['server']['host'] == 'localhost'
        assert result['server']['ssl_cert'] == 'decrypted_cert'
        assert result['regular_setting'] == 'normal_value'

    def test_unsecure_config_decryption_error(self, config_security):
        """Test unsecuring configuration with decryption error."""
        secured_config = {
            'database_password': 'encrypted:bad_encrypted_value'
        }
        
        with patch.object(config_security, 'decrypt_value', side_effect=Exception("Decryption error")):
            result = config_security.unsecure_config(secured_config)
        
        # Should keep encrypted value if decryption fails
        assert result['database_password'] == 'encrypted:bad_encrypted_value'

    def test_save_secure_config_success(self, config_security, sample_config, temp_dir):
        """Test successful secure configuration saving."""
        config_file = os.path.join(temp_dir, 'test_config.json')
        
        with patch.object(config_security, 'secure_config', return_value={'secured': 'config'}):
            result = config_security.save_secure_config(sample_config, config_file)
        
        assert result is True
        assert os.path.exists(config_file)
        
        # Verify file contents
        with open(config_file, 'r') as f:
            saved_config = json.load(f)
        assert saved_config == {'secured': 'config'}
        
        # Verify secure permissions
        file_mode = os.stat(config_file).st_mode
        assert file_mode & 0o077 == 0  # No permissions for group/others

    def test_save_secure_config_failure(self, config_security, sample_config):
        """Test secure configuration saving failure."""
        invalid_path = '/invalid/path/config.json'
        
        with patch('os.makedirs', side_effect=OSError("Permission denied")):
            result = config_security.save_secure_config(sample_config, invalid_path)
        
        assert result is False

    def test_load_secure_config_success(self, config_security, temp_dir):
        """Test successful secure configuration loading."""
        config_file = os.path.join(temp_dir, 'test_config.json')
        test_config = {'database_password': 'encrypted:encrypted_value'}
        
        # Create config file
        with open(config_file, 'w') as f:
            json.dump(test_config, f)
        
        with patch.object(config_security, 'unsecure_config', return_value={'unsecured': 'config'}):
            result = config_security.load_secure_config(config_file)
        
        assert result == {'unsecured': 'config'}

    def test_load_secure_config_not_found(self, config_security):
        """Test loading secure configuration when file doesn't exist."""
        result = config_security.load_secure_config('/nonexistent/config.json')
        
        assert result is None

    def test_load_secure_config_error(self, config_security, temp_dir):
        """Test loading secure configuration with error."""
        config_file = os.path.join(temp_dir, 'invalid_config.json')
        
        # Create invalid JSON file
        with open(config_file, 'w') as f:
            f.write('invalid json content')
        
        result = config_security.load_secure_config(config_file)
        
        assert result is None

    def test_validate_config_security_clean(self, config_security):
        """Test configuration security validation with clean config."""
        clean_config = {
            'app_name': 'test_app',
            'database_password': 'encrypted:encrypted_value',
            'server': {
                'host': 'localhost',
                'port': 8080
            }
        }
        
        is_secure, issues = config_security.validate_config_security(clean_config)
        
        assert is_secure is True
        assert len(issues) == 0

    def test_validate_config_security_hardcoded_secrets(self, config_security):
        """Test configuration security validation with hardcoded secrets."""
        insecure_config = {
            'app_name': 'test_app',
            'database_password': 'P@ssw0rd123',  # Hardcoded secret
            'api_key': 'sk-1234567890abcdef',  # Hardcoded secret
            'server': {
                'host': 'localhost',
                'ssl_key': 'secret_key_content'  # Hardcoded secret
            }
        }
        
        is_secure, issues = config_security.validate_config_security(insecure_config)
        
        assert is_secure is False
        assert len(issues) == 3
        assert any('database_password' in issue for issue in issues)
        assert any('api_key' in issue for issue in issues)
        assert any('ssl_key' in issue for issue in issues)

    def test_validate_config_security_dangerous_patterns(self, config_security):
        """Test configuration security validation with dangerous patterns."""
        dangerous_config = {
            'docker_settings': {
                'privileged': True,
                'host_network': True,
                'volumes': ['/dev:/dev']
            }
        }
        
        is_secure, issues = config_security.validate_config_security(dangerous_config)
        
        assert is_secure is False
        assert len(issues) >= 1
        assert any('privileged' in issue.lower() for issue in issues)

    def test_generate_secure_password_default(self, config_security):
        """Test secure password generation with default length."""
        password = config_security.generate_secure_password()
        
        assert len(password) == 16
        assert any(c.islower() for c in password)  # Has lowercase
        assert any(c.isupper() for c in password)  # Has uppercase
        assert any(c.isdigit() for c in password)  # Has digits
        assert any(c in '!@#$%^&*' for c in password)  # Has special chars

    def test_generate_secure_password_custom_length(self, config_security):
        """Test secure password generation with custom length."""
        password = config_security.generate_secure_password(24)
        
        assert len(password) == 24
        assert any(c.islower() for c in password)
        assert any(c.isupper() for c in password)
        assert any(c.isdigit() for c in password)
        assert any(c in '!@#$%^&*' for c in password)

    def test_generate_secure_password_minimum_length(self, config_security):
        """Test secure password generation with minimum length requirement."""
        with pytest.raises(ValueError, match="Password length must be at least 8 characters"):
            config_security.generate_secure_password(7)

    @patch('blastdock.security.config_security.CRYPTOGRAPHY_AVAILABLE', True)
    def test_hash_value_with_cryptography(self, config_security):
        """Test value hashing with cryptography library."""
        mock_pbkdf2_class = Mock()
        mock_kdf = Mock()
        mock_kdf.derive.return_value = b'hashed_value'
        mock_pbkdf2_class.return_value = mock_kdf
        
        with patch('blastdock.security.config_security.PBKDF2HMAC', mock_pbkdf2_class):
            test_salt = b'test_salt'
            hash_str, returned_salt = config_security.hash_value('test_value', test_salt)
        
        assert returned_salt == test_salt
        assert hash_str == base64.urlsafe_b64encode(b'hashed_value').decode()
        mock_kdf.derive.assert_called_once_with(b'test_value')

    @patch('blastdock.security.config_security.CRYPTOGRAPHY_AVAILABLE', False)
    def test_hash_value_without_cryptography(self, config_security):
        """Test value hashing without cryptography library."""
        test_salt = b'test_salt'
        hash_str, returned_salt = config_security.hash_value('test_value', test_salt)
        
        assert returned_salt == test_salt
        # Verify it's a valid hash
        assert len(hash_str) > 0
        assert isinstance(hash_str, str)

    def test_hash_value_auto_salt(self, config_security):
        """Test value hashing with auto-generated salt."""
        with patch('os.urandom', return_value=b'random_salt'):
            hash_str, salt = config_security.hash_value('test_value')
        
        assert salt == b'random_salt'
        assert len(hash_str) > 0

    def test_verify_hash_success(self, config_security):
        """Test successful hash verification."""
        test_value = 'test_value'
        test_salt = b'test_salt'
        
        # Get hash
        hash_str, _ = config_security.hash_value(test_value, test_salt)
        
        # Verify hash
        result = config_security.verify_hash(test_value, hash_str, test_salt)
        
        assert result is True

    def test_verify_hash_failure(self, config_security):
        """Test hash verification failure."""
        test_salt = b'test_salt'
        
        # Get hash for one value
        hash_str, _ = config_security.hash_value('correct_value', test_salt)
        
        # Try to verify with different value
        result = config_security.verify_hash('wrong_value', hash_str, test_salt)
        
        assert result is False

    def test_verify_hash_exception(self, config_security):
        """Test hash verification with exception."""
        with patch.object(config_security, 'hash_value', side_effect=Exception("Hash error")):
            result = config_security.verify_hash('test_value', 'hash_str', b'salt')
        
        assert result is False

    @patch('blastdock.security.config_security.CRYPTOGRAPHY_AVAILABLE', True)
    def test_rotate_encryption_key_with_password(self, config_security):
        """Test encryption key rotation with passwords."""
        mock_pbkdf2_class = Mock()
        mock_old_kdf = Mock()
        mock_old_kdf.derive.return_value = b'old_key'
        mock_pbkdf2_class.return_value = mock_old_kdf
        
        mock_fernet_class = Mock()
        mock_old_fernet = Mock()
        mock_new_fernet = Mock()
        mock_fernet_class.side_effect = [mock_old_fernet, mock_new_fernet]
        
        with patch('blastdock.security.config_security.PBKDF2HMAC', mock_pbkdf2_class):
            with patch('blastdock.security.config_security.Fernet', mock_fernet_class):
                with patch.object(config_security, '_get_or_create_salt', return_value=b'salt'):
                    with patch.object(config_security, 'initialize_encryption', return_value=True):
                        result = config_security.rotate_encryption_key('old_password', 'new_password')
        
        assert result is True

    def test_rotate_encryption_key_failure(self, config_security):
        """Test encryption key rotation failure."""
        with patch.object(config_security, '_load_key', return_value=False):
            result = config_security.rotate_encryption_key()
        
        assert result is False

    def test_get_security_status(self, config_security):
        """Test getting security status."""
        with patch.object(config_security, '_load_key', return_value=True):
            with patch('blastdock.utils.filesystem.paths') as mock_paths:
                mock_paths.config_dir = '/tmp/test'
                with patch('os.path.exists', return_value=True):
                    status = config_security.get_security_status()
        
        assert status['encryption_enabled'] is True
        assert status['key_file_exists'] is True
        assert status['salt_file_exists'] is True
        assert status['key_derivation_iterations'] == 100000
        assert status['sensitive_keys_count'] > 0
        assert 'Configuration encryption' in status['security_features']

    def test_get_security_status_no_encryption(self, config_security):
        """Test getting security status without encryption."""
        with patch.object(config_security, '_load_key', return_value=False):
            with patch('blastdock.utils.filesystem.paths') as mock_paths:
                mock_paths.config_dir = '/tmp/test'
                with patch('os.path.exists', return_value=False):
                    status = config_security.get_security_status()
        
        assert status['encryption_enabled'] is False
        assert status['key_file_exists'] is False
        assert status['salt_file_exists'] is False


class TestGlobalConfigSecurity:
    """Test suite for global configuration security functions."""

    def test_get_config_security_singleton(self):
        """Test the global configuration security singleton."""
        # Clear any existing instance
        import blastdock.security.config_security as config_security_module
        config_security_module._config_security = None
        
        # Get instances
        instance1 = get_config_security()
        instance2 = get_config_security()
        
        assert isinstance(instance1, ConfigurationSecurity)
        assert instance1 is instance2  # Should be the same instance


class TestConfigurationSecurityIntegration:
    """Integration tests for ConfigurationSecurity."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_full_encryption_cycle(self, temp_dir):
        """Test full encryption/decryption cycle."""
        config_security = ConfigurationSecurity()
        
        # Mock filesystem paths
        with patch('blastdock.utils.filesystem.paths') as mock_paths:
            mock_paths.config_dir = temp_dir
            
            # Initialize encryption
            assert config_security.initialize_encryption() is True
            
            # Test encryption/decryption
            test_value = 'secret_password_123'
            encrypted = config_security.encrypt_value(test_value)
            decrypted = config_security.decrypt_value(encrypted)
            
            assert decrypted == test_value
            assert encrypted != test_value

    def test_config_save_load_cycle(self, temp_dir):
        """Test full configuration save/load cycle."""
        config_security = ConfigurationSecurity()
        config_file = os.path.join(temp_dir, 'test_config.json')
        
        test_config = {
            'app_name': 'test_app',
            'database_password': 'secret123',
            'api_key': 'abc123def456'
        }
        
        with patch('blastdock.utils.filesystem.paths') as mock_paths:
            mock_paths.config_dir = temp_dir
            
            # Initialize encryption
            config_security.initialize_encryption()
            
            # Save config
            assert config_security.save_secure_config(test_config, config_file) is True
            
            # Load config
            loaded_config = config_security.load_secure_config(config_file)
            
            assert loaded_config is not None
            assert loaded_config['app_name'] == 'test_app'
            assert loaded_config['database_password'] == 'secret123'
            assert loaded_config['api_key'] == 'abc123def456'

    def test_password_hash_verify_cycle(self):
        """Test password hashing and verification cycle."""
        config_security = ConfigurationSecurity()
        
        test_password = 'secure_password_123'
        hash_str, salt = config_security.hash_value(test_password)
        
        # Verify correct password
        assert config_security.verify_hash(test_password, hash_str, salt) is True
        
        # Verify incorrect password
        assert config_security.verify_hash('wrong_password', hash_str, salt) is False