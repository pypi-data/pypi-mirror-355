"""
Модуль моделирования угроз.

Содержит инструменты для автоматического создания моделей угроз.
"""

from .generator import ThreatModelGenerator, AdvancedThreatModelGenerator

__all__ = [
    "ThreatModelGenerator",
    "AdvancedThreatModelGenerator",
] 