"""
Реестр плагинов PySecKit.
"""

import importlib
import inspect
import os
from typing import Dict, List, Type, Any, Optional
from .base import PluginBase
from .scanner_plugin import ScannerPlugin


class PluginRegistry:
    """Реестр для управления плагинами."""
    
    def __init__(self):
        self._plugins: Dict[str, Type[PluginBase]] = {}
        self._instances: Dict[str, PluginBase] = {}
        self._discovery_paths: List[str] = []
    
    def register_plugin(self, plugin_class: Type[PluginBase]) -> None:
        """Регистрирует плагин."""
        if not issubclass(plugin_class, PluginBase):
            raise ValueError(f"Plugin {plugin_class} must inherit from PluginBase")
        
        # Создаем временный экземпляр для получения метаданных
        temp_instance = plugin_class({})
        metadata = temp_instance.metadata
        
        self._plugins[metadata.name] = plugin_class
    
    def register_plugin_class(self, name: str, plugin_class: Type) -> None:
        """Регистрирует плагин по имени и классу."""
        self._plugins[name] = plugin_class
    
    def get_plugin(self, name: str, config: Optional[Dict[str, Any]] = None) -> Optional[PluginBase]:
        """Получает экземпляр плагина."""
        if name in self._instances:
            return self._instances[name]
        
        if name not in self._plugins:
            return None
        
        plugin_class = self._plugins[name]
        instance = plugin_class(config or {})
        
        # Инициализируем плагин
        if hasattr(instance, 'initialize') and instance.initialize():
            self._instances[name] = instance
            return instance
        elif not hasattr(instance, 'initialize'):
            self._instances[name] = instance
            return instance
        
        return None
    
    def get_all_plugins(self) -> List[Dict[str, Any]]:
        """Возвращает список всех зарегистрированных плагинов."""
        return self.list_plugins()
    
    def list_plugins(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Возвращает список доступных плагинов."""
        plugins = []
        
        for name, plugin_class in self._plugins.items():
            try:
                temp_instance = plugin_class({})
                metadata = getattr(temp_instance, 'metadata', None)
                
                if metadata:
                    if category and metadata.category != category:
                        continue
                    
                    plugin_info = {
                        "name": metadata.name,
                        "version": metadata.version,
                        "description": metadata.description,
                        "author": metadata.author,
                        "category": metadata.category,
                        "dependencies": metadata.dependencies,
                        "registered": True,
                        "initialized": name in self._instances
                    }
                else:
                    # Для плагинов без метаданных
                    plugin_info = {
                        "name": name,
                        "version": "unknown",
                        "description": "Plugin without metadata",
                        "author": "unknown",
                        "category": "unknown",
                        "dependencies": [],
                        "registered": True,
                        "initialized": name in self._instances
                    }
                
                plugins.append(plugin_info)
            except Exception:
                # Если не удается создать экземпляр, добавляем базовую информацию
                plugin_info = {
                    "name": name,
                    "version": "unknown",
                    "description": "Plugin registration failed",
                    "author": "unknown",
                    "category": "unknown",
                    "dependencies": [],
                    "registered": False,
                    "initialized": False
                }
                plugins.append(plugin_info)
        
        return plugins
    
    def get_scanners(self) -> List[ScannerPlugin]:
        """Возвращает все инициализированные сканеры."""
        scanners = []
        
        for instance in self._instances.values():
            if isinstance(instance, ScannerPlugin):
                scanners.append(instance)
        
        return scanners
    
    def add_discovery_path(self, path: str) -> None:
        """Добавляет путь для поиска плагинов."""
        if os.path.exists(path) and path not in self._discovery_paths:
            self._discovery_paths.append(path)
    
    def discover_plugins(self) -> int:
        """Автоматически находит и регистрирует плагины."""
        discovered = 0
        
        for path in self._discovery_paths:
            try:
                discovered += self._discover_in_path(path)
            except Exception as e:
                print(f"Ошибка при поиске плагинов в {path}: {e}")
        
        return discovered
    
    def _discover_in_path(self, path: str) -> int:
        """Ищет плагины в указанном пути."""
        discovered = 0
        
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    try:
                        module_path = os.path.join(root, file)
                        discovered += self._load_plugins_from_file(module_path)
                    except Exception:
                        continue
        
        return discovered
    
    def _load_plugins_from_file(self, file_path: str) -> int:
        """Загружает плагины из файла."""
        try:
            spec = importlib.util.spec_from_file_location("plugin_module", file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                discovered = 0
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, PluginBase) and 
                        obj != PluginBase):
                        try:
                            self.register_plugin(obj)
                            discovered += 1
                        except Exception:
                            continue
                
                return discovered
        except Exception:
            pass
        
        return 0
    
    def unload_plugin(self, name: str) -> bool:
        """Выгружает плагин."""
        if name in self._instances:
            instance = self._instances[name]
            if hasattr(instance, 'cleanup'):
                instance.cleanup()
            del self._instances[name]
            return True
        
        return False
    
    def cleanup_all(self) -> None:
        """Очищает все плагины."""
        for instance in self._instances.values():
            try:
                if hasattr(instance, 'cleanup'):
                    instance.cleanup()
            except Exception:
                pass
        
        self._instances.clear()


# Глобальный реестр плагинов
plugin_registry = PluginRegistry() 