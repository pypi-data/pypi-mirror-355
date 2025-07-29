"""
Модуль исключений для PySecKit.

Содержит все кастомные исключения, используемые в библиотеке.
"""

from typing import Optional, Any, Dict


class PySecKitException(Exception):
    """Базовое исключение для всех ошибок PySecKit."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message}. Детали: {self.details}"
        return self.message


class ScannerException(PySecKitException):
    """Исключение для ошибок сканнеров."""
    
    def __init__(
        self, 
        message: str, 
        scanner_name: Optional[str] = None,
        exit_code: Optional[int] = None,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message, details)
        self.scanner_name = scanner_name
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr


class ConfigurationException(PySecKitException):
    """Исключение для ошибок конфигурации."""
    
    def __init__(self, message: str, config_path: Optional[str] = None) -> None:
        super().__init__(message)
        self.config_path = config_path


class ReportException(PySecKitException):
    """Исключение для ошибок генерации отчётов."""
    pass


class CICDException(PySecKitException):
    """Исключение для ошибок CI/CD интеграции."""
    pass


class CloudException(PySecKitException):
    """Исключение для ошибок облачных провайдеров."""
    pass


class ThreatModelException(PySecKitException):
    """Исключение для ошибок моделирования угроз."""
    pass


class PluginException(PySecKitException):
    """Исключение для ошибок плагинов."""
    pass 