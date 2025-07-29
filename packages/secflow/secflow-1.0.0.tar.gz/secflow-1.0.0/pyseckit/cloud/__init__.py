"""
Модуль сканнеров облачной безопасности.

Содержит сканнеры для проверки конфигураций облачных ресурсов.
"""

from .checkov import CheckovScanner

__all__ = [
    "CheckovScanner",
] 