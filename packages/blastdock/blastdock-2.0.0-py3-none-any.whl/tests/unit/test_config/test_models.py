"""
Tests for configuration models
"""

import pytest
from unittest.mock import patch, Mock

from blastdock.config import (
    ProfileManager, ConfigBackup, EnvironmentManager,
    get_config_manager, get_config
)


class TestProfileManager:
    """Test ProfileManager class"""

    def test_profile_manager_init(self):
        """Test ProfileManager initialization"""
        manager = ProfileManager()
        assert 'default' in manager.profiles
        assert manager.profiles['default'] == {}

    def test_list_profiles(self):
        """Test listing profiles"""
        manager = ProfileManager()
        profiles = manager.list_profiles()
        assert 'default' in profiles
        assert isinstance(profiles, list)

    def test_create_profile(self):
        """Test creating a new profile"""
        manager = ProfileManager()
        result = manager.create_profile('test', template='default')
        
        assert result is True
        assert 'test' in manager.profiles
        assert manager.profiles['test'] == {}

    def test_delete_profile_success(self):
        """Test deleting existing profile"""
        manager = ProfileManager()
        manager.create_profile('to_delete')
        
        result = manager.delete_profile('to_delete')
        assert result is True
        assert 'to_delete' not in manager.profiles

    def test_delete_profile_not_found(self):
        """Test deleting non-existent profile"""
        manager = ProfileManager()
        result = manager.delete_profile('nonexistent')
        assert result is False


class TestConfigBackup:
    """Test ConfigBackup class"""

    def test_config_backup_init(self):
        """Test ConfigBackup initialization"""
        backup = ConfigBackup()
        assert backup is not None

    def test_create_backup(self):
        """Test creating a backup"""
        backup = ConfigBackup()
        result = backup.create_backup('test_profile')
        
        assert result is not None
        assert 'backup_id' in result
        assert 'timestamp' in result
        assert result['backup_id'] == 'backup_123'

    def test_restore_backup(self):
        """Test restoring from backup"""
        backup = ConfigBackup()
        result = backup.restore_backup('backup_123')
        assert result is True

    def test_list_backups(self):
        """Test listing backups"""
        backup = ConfigBackup()
        result = backup.list_backups()
        assert isinstance(result, list)
        assert result == []


class TestEnvironmentManager:
    """Test EnvironmentManager class"""

    def test_environment_manager_init(self):
        """Test EnvironmentManager initialization"""
        manager = EnvironmentManager()
        assert manager is not None

    def test_get_environment_config(self):
        """Test getting environment configuration"""
        manager = EnvironmentManager()
        result = manager.get_environment_config('development')
        assert isinstance(result, dict)
        assert result == {}

    def test_set_environment_config(self):
        """Test setting environment configuration"""
        manager = EnvironmentManager()
        config = {'debug': True, 'log_level': 'DEBUG'}
        result = manager.set_environment_config('development', config)
        assert result is True


class TestConfigFunctions:
    """Test configuration module functions"""

    @patch('blastdock.config.ConfigManager')
    def test_get_config_manager_new_instance(self, mock_config_manager_class):
        """Test getting config manager - new instance"""
        mock_manager = Mock()
        mock_manager.profile = 'test'
        mock_config_manager_class.return_value = mock_manager
        
        # Reset the global instance
        import blastdock.config
        blastdock.config._manager_instance = None
        
        result = get_config_manager('test')
        
        assert result == mock_manager
        mock_config_manager_class.assert_called_once_with('test')

    @patch('blastdock.config.ConfigManager')
    def test_get_config_manager_existing_instance(self, mock_config_manager_class):
        """Test getting config manager - existing instance"""
        mock_manager = Mock()
        mock_manager.profile = 'test'
        
        # Set existing instance
        import blastdock.config
        blastdock.config._manager_instance = mock_manager
        
        result = get_config_manager('test')
        
        assert result == mock_manager
        # Should not create new instance if profile matches
        mock_config_manager_class.assert_not_called()

    @patch('blastdock.config.ConfigManager')
    def test_get_config_manager_different_profile(self, mock_config_manager_class):
        """Test getting config manager - different profile"""
        old_manager = Mock()
        old_manager.profile = 'old'
        
        new_manager = Mock()
        new_manager.profile = 'new'
        mock_config_manager_class.return_value = new_manager
        
        # Set existing instance with different profile
        import blastdock.config
        blastdock.config._manager_instance = old_manager
        
        result = get_config_manager('new')
        
        assert result == new_manager
        mock_config_manager_class.assert_called_once_with('new')

    def test_get_config(self):
        """Test getting configuration"""
        mock_manager = Mock()
        mock_config = Mock()
        mock_manager.config = mock_config
        
        with patch('blastdock.config.get_config_manager', return_value=mock_manager):
            result = get_config()
            assert result == mock_config

    def test_module_exports(self):
        """Test that all expected items are exported"""
        import blastdock.config
        
        expected_exports = [
            'ConfigManager',
            'get_config_manager',
            'get_config',
            'BlastDockConfig',
            'DefaultPortsConfig',
            'LoggingConfig',
            'DockerConfig',
            'SecurityConfig',
            'TemplateConfig',
            'ProfileManager',
            'ConfigBackup',
            'EnvironmentManager'
        ]
        
        for export in expected_exports:
            assert hasattr(blastdock.config, export), f"Export '{export}' not found"
        
        assert blastdock.config.__all__ == expected_exports

    def test_singleton_behavior(self):
        """Test singleton behavior of config manager"""
        # Reset singleton
        import blastdock.config
        blastdock.config._manager_instance = None
        
        with patch('blastdock.config.ConfigManager') as mock_class:
            mock_manager = Mock()
            mock_manager.profile = 'default'
            mock_class.return_value = mock_manager
            
            # First call should create instance
            manager1 = get_config_manager('default')
            
            # Second call with same profile should return same instance
            manager2 = get_config_manager('default')
            
            assert manager1 == manager2
            assert mock_class.call_count == 1  # Only called once

    def test_profile_change_creates_new_instance(self):
        """Test that changing profile creates new instance"""
        import blastdock.config
        blastdock.config._manager_instance = None
        
        with patch('blastdock.config.ConfigManager') as mock_class:
            manager1 = Mock()
            manager1.profile = 'profile1'
            
            manager2 = Mock()
            manager2.profile = 'profile2'
            
            mock_class.side_effect = [manager1, manager2]
            
            # Get manager for profile1
            result1 = get_config_manager('profile1')
            assert result1 == manager1
            
            # Get manager for profile2 - should create new instance
            result2 = get_config_manager('profile2')
            assert result2 == manager2
            
            assert mock_class.call_count == 2