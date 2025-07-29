"""
Базовые классы для системы плагинов PySecKit.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel


class PluginMetadata(BaseModel):
    """Метаданные плагина."""
    name: str
    version: str
    description: str
    author: str
    category: str
    dependencies: list[str] = []
    config_schema: Optional[Dict[str, Any]] = None


class PluginBase(ABC):
    """Базовый класс для всех плагинов PySecKit."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._initialized = False
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Возвращает метаданные плагина."""
        pass
    
    @abstractmethod
    def initialize(self) -> bool:
        """Инициализирует плагин. Возвращает True при успехе."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Очищает ресурсы плагина."""
        pass
    
    def is_initialized(self) -> bool:
        """Проверяет, инициализирован ли плагин."""
        return self._initialized
    
    def validate_config(self) -> bool:
        """Проверяет конфигурацию плагина."""
        if not self.metadata.config_schema:
            return True
        
        # Простая валидация наличия обязательных полей
        schema = self.metadata.config_schema
        required_fields = schema.get('required', [])
        
        for field in required_fields:
            if field not in self.config:
                return False
        
        return True 