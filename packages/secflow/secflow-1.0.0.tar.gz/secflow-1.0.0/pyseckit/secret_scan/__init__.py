"""
Модуль сканнеров секретов.

Содержит сканнеры для поиска секретов, ключей и паролей в коде.
"""

from .gitleaks import GitleaksScanner
from .trufflehog import TruffleHogScanner

__all__ = [
    "GitleaksScanner",
    "TruffleHogScanner",
] 