"""
Базовые классы и интерфейсы для сканнеров безопасности.

Содержит абстрактный класс Scanner и модели данных для результатов сканирования.
"""

import json
import subprocess
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from .exceptions import ScannerException


class Severity(str, Enum):
    """Уровни критичности уязвимостей."""
    
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
    
    def __str__(self) -> str:
        return self.value
    
    @property
    def priority(self) -> int:
        """Возвращает числовой приоритет для сортировки."""
        priorities = {
            self.CRITICAL: 5,
            self.HIGH: 4,
            self.MEDIUM: 3,
            self.LOW: 2,
            self.INFO: 1
        }
        return priorities[self]


class ScanResult(BaseModel):
    """Модель результата сканирования."""
    
    id: str = Field(description="Уникальный идентификатор")
    scanner_name: str = Field(description="Имя сканнера")
    title: str = Field(description="Название уязвимости")
    description: str = Field(description="Описание уязвимости")
    severity: Severity = Field(description="Уровень критичности")
    file_path: Optional[str] = Field(default=None, description="Путь к файлу")
    line_number: Optional[int] = Field(default=None, description="Номер строки")
    column_number: Optional[int] = Field(default=None, description="Номер колонки")
    rule_id: Optional[str] = Field(default=None, description="ID правила")
    cwe_id: Optional[str] = Field(default=None, description="CWE идентификатор")
    owasp_category: Optional[str] = Field(default=None, description="OWASP категория")
    confidence: Optional[str] = Field(default=None, description="Уровень уверенности")
    remediation: Optional[str] = Field(default=None, description="Рекомендации по устранению")
    code_snippet: Optional[str] = Field(default=None, description="Фрагмент кода")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Дополнительные метаданные")
    timestamp: float = Field(default_factory=time.time, description="Время обнаружения")
    
    class Config:
        """Конфигурация модели."""
        use_enum_values = True
        
    def to_dict(self) -> Dict[str, Any]:
        """Конвертирует результат в словарь."""
        return self.dict()
    
    def to_json(self) -> str:
        """Конвертирует результат в JSON."""
        return self.json(indent=2)


@dataclass
class ScanStats:
    """Статистика сканирования."""
    
    total_scanned: int = 0
    total_issues: int = 0
    critical_issues: int = 0
    high_issues: int = 0
    medium_issues: int = 0
    low_issues: int = 0
    info_issues: int = 0
    scan_duration: float = 0.0
    scanner_name: str = ""
    
    def add_result(self, result: ScanResult) -> None:
        """Добавляет результат в статистику."""
        self.total_issues += 1
        
        if result.severity == Severity.CRITICAL:
            self.critical_issues += 1
        elif result.severity == Severity.HIGH:
            self.high_issues += 1
        elif result.severity == Severity.MEDIUM:
            self.medium_issues += 1
        elif result.severity == Severity.LOW:
            self.low_issues += 1
        elif result.severity == Severity.INFO:
            self.info_issues += 1


class Scanner(ABC):
    """Абстрактный базовый класс для всех сканнеров."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Инициализирует сканнер.
        
        Args:
            config: Конфигурация сканнера
        """
        self.config = config or {}
        self.name = self.__class__.__name__
        self._results: List[ScanResult] = []
        self._stats = ScanStats(scanner_name=self.name)
    
    @property
    @abstractmethod
    def scanner_name(self) -> str:
        """Возвращает имя сканнера."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Возвращает версию сканнера."""
        pass
    
    @property
    @abstractmethod
    def supported_formats(self) -> List[str]:
        """Возвращает поддерживаемые форматы файлов."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Проверяет доступность сканнера в системе."""
        pass
    
    @abstractmethod
    def scan(self, target: Union[str, Path], **kwargs) -> List[ScanResult]:
        """
        Выполняет сканирование цели.
        
        Args:
            target: Цель сканирования (файл, директория, URL и т.д.)
            **kwargs: Дополнительные параметры
            
        Returns:
            Список результатов сканирования
            
        Raises:
            ScannerException: При ошибке сканирования
        """
        pass
    
    def get_results(self) -> List[ScanResult]:
        """Возвращает результаты последнего сканирования."""
        return self._results.copy()
    
    def get_stats(self) -> ScanStats:
        """Возвращает статистику последнего сканирования."""
        return self._stats
    
    def clear_results(self) -> None:
        """Очищает результаты и статистику."""
        self._results.clear()
        self._stats = ScanStats(scanner_name=self.name)
    
    def filter_results(
        self,
        severity: Optional[List[Severity]] = None,
        file_pattern: Optional[str] = None,
        rule_id: Optional[str] = None
    ) -> List[ScanResult]:
        """
        Фильтрует результаты по заданным критериям.
        
        Args:
            severity: Список уровней критичности
            file_pattern: Паттерн для фильтрации файлов
            rule_id: ID правила для фильтрации
            
        Returns:
            Отфильтрованный список результатов
        """
        filtered = self._results.copy()
        
        if severity:
            filtered = [r for r in filtered if r.severity in severity]
        
        if file_pattern and file_pattern:
            import fnmatch
            filtered = [
                r for r in filtered 
                if r.file_path and fnmatch.fnmatch(r.file_path, file_pattern)
            ]
        
        if rule_id:
            filtered = [r for r in filtered if r.rule_id == rule_id]
        
        return filtered
    
    def run_command(
        self,
        command: List[str],
        cwd: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> subprocess.CompletedProcess:
        """
        Выполняет команду в подпроцессе.
        
        Args:
            command: Команда для выполнения
            cwd: Рабочая директория
            timeout: Таймаут выполнения
            
        Returns:
            Результат выполнения команды
            
        Raises:
            ScannerException: При ошибке выполнения
        """
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=timeout,
                check=False  # Не поднимаем исключение на non-zero exit code
            )
            return result
        except subprocess.TimeoutExpired as e:
            raise ScannerException(
                f"Команда {' '.join(command)} превысила таймаут {timeout}с",
                scanner_name=self.scanner_name,
                details={"command": command, "timeout": timeout}
            ) from e
        except Exception as e:
            raise ScannerException(
                f"Ошибка выполнения команды {' '.join(command)}: {e}",
                scanner_name=self.scanner_name,
                details={"command": command}
            ) from e
    
    def _add_result(self, result: ScanResult) -> None:
        """Добавляет результат в список и обновляет статистику."""
        self._results.append(result)
        self._stats.add_result(result)


class ScannerManager:
    """Менеджер для управления множественными сканнерами."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Инициализирует менеджер сканнеров."""
        self.config = config or {}
        self._scanners: Dict[str, Scanner] = {}
        self._results: List[ScanResult] = []
        
        # Автоматически регистрируем доступные сканнеры
        self._register_default_scanners()
    
    def register_scanner(self, scanner: Scanner) -> None:
        """
        Регистрирует сканнер в менеджере.
        
        Args:
            scanner: Экземпляр сканнера
        """
        self._scanners[scanner.scanner_name] = scanner
    
    def get_scanner(self, name: str) -> Optional[Scanner]:
        """
        Возвращает сканнер по имени.
        
        Args:
            name: Имя сканнера
            
        Returns:
            Экземпляр сканнера или None
        """
        return self._scanners.get(name)
    
    def get_available_scanners(self) -> Dict[str, Scanner]:
        """Возвращает словарь доступных сканнеров."""
        return {
            name: scanner for name, scanner in self._scanners.items()
            if scanner.is_available()
        }
    
    def _register_default_scanners(self) -> None:
        """Регистрирует сканнеры по умолчанию."""
        # Базовые сканнеры будут добавлены через импорты модулей
        scanner_configs = self.config.get('scanners', {})
        
        # Можно добавить логику автоматической регистрации
        # сканнеров из entry_points или плагинов
        pass
    
    def scan_with_multiple(
        self,
        target: Union[str, Path],
        scanner_names: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, List[ScanResult]]:
        """
        Выполняет сканирование несколькими сканнерами.
        
        Args:
            target: Цель сканирования
            scanner_names: Список имён сканнеров (если None, используются все доступные)
            **kwargs: Дополнительные параметры
            
        Returns:
            Словарь с результатами по каждому сканнеру
        """
        if scanner_names is None:
            scanner_names = list(self.get_available_scanners().keys())
        
        results = {}
        for name in scanner_names:
            scanner = self.get_scanner(name)
            if scanner and scanner.is_available():
                try:
                    scan_results = scanner.scan(target, **kwargs)
                    results[name] = scan_results
                except ScannerException as e:
                    # Логируем ошибку, но продолжаем с другими сканнерами
                    print(f"Ошибка сканнера {name}: {e}")
                    results[name] = []
            else:
                print(f"Сканнер {name} недоступен")
                results[name] = []
        
        return results
    
    def get_all_results(self) -> List[ScanResult]:
        """Возвращает все результаты сканирования."""
        all_results = []
        for scanner in self._scanners.values():
            all_results.extend(scanner.get_results())
        return all_results 