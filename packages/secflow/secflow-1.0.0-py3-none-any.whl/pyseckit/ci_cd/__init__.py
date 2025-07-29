"""
Модуль интеграции с CI/CD системами.

Содержит менеджеры и утилиты для интеграции с различными CI/CD платформами.
"""

from .manager import CICDManager

__all__ = [
    "CICDManager",
] 