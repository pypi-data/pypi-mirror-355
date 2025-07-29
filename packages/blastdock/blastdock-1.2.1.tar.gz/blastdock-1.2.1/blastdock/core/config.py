"""
Legacy configuration module - redirects to new enhanced config system
"""

import warnings
from typing import Dict, Any, Optional, List

# Import from new enhanced configuration system
from ..config import (
    ConfigManager as EnhancedConfigManager,
    get_config_manager as get_enhanced_config_manager,
    get_config as get_enhanced_config,
    BlastDockConfig,
    DefaultPortsConfig,
    LoggingConfig,
    DockerConfig,
    SecurityConfig,
    TemplateConfig
)

from ..utils.logging import get_logger

logger = get_logger(__name__)

# Issue deprecation warning
warnings.warn(
    "blastdock.core.config is deprecated. Please use blastdock.config instead.",
    DeprecationWarning,
    stacklevel=2
)


class ConfigManager(EnhancedConfigManager):
    """Legacy ConfigManager wrapper for backward compatibility"""
    
    def __init__(self, profile: str = "default"):
        logger.warning("Using legacy ConfigManager. Consider upgrading to blastdock.config.ConfigManager")
        super().__init__(profile, auto_save=True, watch_changes=False)


def get_config_manager(profile: str = "default") -> ConfigManager:
    """Get the global configuration manager instance (legacy)"""
    logger.warning("Using legacy get_config_manager. Consider upgrading to blastdock.config.get_config_manager")
    return ConfigManager(profile)


def get_config(profile: str = "default") -> BlastDockConfig:
    """Get the current configuration (legacy)"""
    return get_enhanced_config(profile)