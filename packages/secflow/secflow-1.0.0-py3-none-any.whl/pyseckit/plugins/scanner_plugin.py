"""
Плагин для сканеров безопасности.
"""

from abc import abstractmethod
from typing import Dict, Any, List
from pyseckit.core.scanner import Scanner, ScanResult
from .base import PluginBase, PluginMetadata


class ScannerPlugin(PluginBase, Scanner):
    """Базовый класс для плагинов сканеров."""
    
    def __init__(self, config: Dict[str, Any] = None):
        PluginBase.__init__(self, config)
        Scanner.__init__(self, config)
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Метаданные плагина сканера."""
        pass
    
    @abstractmethod
    def scan(self, target: str) -> ScanResult:
        """Выполняет сканирование цели."""
        pass
    
    def get_scanner_info(self) -> Dict[str, Any]:
        """Возвращает информацию о сканере."""
        meta = self.metadata
        return {
            "name": meta.name,
            "version": meta.version,
            "description": meta.description,
            "author": meta.author,
            "category": meta.category,
            "dependencies": meta.dependencies,
            "enabled": self.enabled,
            "initialized": self.is_initialized()
        }


class CustomScannerExample(ScannerPlugin):
    """Пример пользовательского сканера."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="custom-scanner",
            version="1.0.0",
            description="Пример пользовательского сканера",
            author="PySecKit Team",
            category="custom",
            config_schema={
                "required": ["patterns"],
                "properties": {
                    "patterns": {
                        "type": "array",
                        "description": "Паттерны для поиска"
                    }
                }
            }
        )
    
    def initialize(self) -> bool:
        """Инициализация пользовательского сканера."""
        if not self.validate_config():
            return False
        
        self._initialized = True
        return True
    
    def cleanup(self) -> None:
        """Очистка ресурсов."""
        self._initialized = False
    
    def scan(self, target: str) -> ScanResult:
        """Выполняет пользовательское сканирование."""
        import os
        import re
        from datetime import datetime
        
        findings = []
        patterns = self.config.get("patterns", [])
        
        # Простой поиск по файлам
        if os.path.isfile(target):
            files_to_scan = [target]
        elif os.path.isdir(target):
            files_to_scan = []
            for root, _, files in os.walk(target):
                for file in files:
                    if file.endswith(('.py', '.js', '.ts', '.java', '.cpp', '.c')):
                        files_to_scan.append(os.path.join(root, file))
        else:
            files_to_scan = []
        
        for file_path in files_to_scan:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                for pattern in patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        findings.append({
                            "severity": "MEDIUM",
                            "confidence": "MEDIUM",
                            "title": f"Pattern match: {pattern}",
                            "description": f"Found pattern '{pattern}' in file",
                            "file": file_path,
                            "line": line_num,
                            "column": match.start() - content.rfind('\n', 0, match.start()),
                            "code": match.group(0),
                            "rule_id": f"custom-{hash(pattern) % 10000}",
                            "cwe": "CWE-200"
                        })
            except Exception:
                continue
        
        return ScanResult(
            scanner_name=self.metadata.name,
            target=target,
            start_time=datetime.now(),
            end_time=datetime.now(),
            findings=findings,
            metadata={"patterns_used": patterns}
        ) 