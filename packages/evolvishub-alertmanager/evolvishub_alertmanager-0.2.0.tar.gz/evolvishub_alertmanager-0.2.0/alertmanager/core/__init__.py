"""
Core modules for the project.
"""

from .base_manager import BaseManager
from .sqlite_adapter import SQLiteAdapter

__all__ = ['BaseManager', 'SQLiteAdapter']
