"""
Модуль DAST (Dynamic Application Security Testing) сканнеров.

Содержит сканнеры для динамического анализа безопасности приложений.
"""

from .zap import ZapScanner

__all__ = [
    "ZapScanner",
] 