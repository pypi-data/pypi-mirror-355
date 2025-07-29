"""
Система плагинов PySecKit для расширения функциональности.
"""

from .registry import PluginRegistry
from .base import PluginBase
from .scanner_plugin import ScannerPlugin

__all__ = ["PluginRegistry", "PluginBase", "ScannerPlugin"] 