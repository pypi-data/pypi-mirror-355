"""
AlertManager - A flexible alert management system with SQLite backend.
"""

__version__ = "0.1.0"

from .core.alert_manager import AlertManager
from .config.config_manager import ConfigManager

__all__ = ['AlertManager', 'ConfigManager'] 