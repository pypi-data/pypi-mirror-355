"""
Базовые тесты для PySecKit.
"""

import pytest
from pathlib import Path

from pyseckit.core.config import Config
from pyseckit.core.scanner import ScannerManager, Severity
from pyseckit.sast import BanditScanner, SemgrepScanner, SafetyScanner


def test_config_loading():
    """Тестирует загрузку конфигурации."""
    config = Config()
    assert config.project_name == "PySecKit Project"
    assert "." in config.target_directories


def test_scanner_manager():
    """Тестирует менеджер сканнеров."""
    manager = ScannerManager()
    
    # Регистрируем сканнер
    bandit = BanditScanner()
    manager.register_scanner(bandit)
    
    # Проверяем регистрацию
    assert manager.get_scanner("bandit") is not None
    assert "bandit" in [name for name in manager._scanners.keys()]


def test_bandit_scanner():
    """Тестирует Bandit сканнер."""
    scanner = BanditScanner()
    
    assert scanner.scanner_name == "bandit"
    assert ".py" in scanner.supported_formats
    
    # Тестируем базовую функциональность
    # is_available может вернуть False если bandit не установлен
    # Это нормально для тестирования


def test_semgrep_scanner():
    """Тестирует Semgrep сканнер."""
    scanner = SemgrepScanner()
    
    assert scanner.scanner_name == "semgrep"
    assert ".py" in scanner.supported_formats
    assert ".js" in scanner.supported_formats


def test_safety_scanner():
    """Тестирует Safety сканнер."""
    scanner = SafetyScanner()
    
    assert scanner.scanner_name == "safety"
    assert ".txt" in scanner.supported_formats


def test_severity_enum():
    """Тестирует enum критичности."""
    assert Severity.CRITICAL.priority > Severity.HIGH.priority
    assert Severity.HIGH.priority > Severity.MEDIUM.priority
    assert Severity.MEDIUM.priority > Severity.LOW.priority
    assert Severity.LOW.priority > Severity.INFO.priority


def test_config_from_env(monkeypatch):
    """Тестирует загрузку конфигурации из переменных окружения."""
    monkeypatch.setenv("PYSECKIT_PROJECT_NAME", "Test Project")
    monkeypatch.setenv("PYSECKIT_FAIL_ON_CRITICAL", "true")
    
    config = Config.from_env()
    
    assert config.project_name == "Test Project"
    assert config.cicd.fail_on_critical is True


def test_scanner_config():
    """Тестирует конфигурацию сканнеров."""
    config = Config()
    
    # Получаем конфигурацию для нового сканнера
    scanner_config = config.get_scanner_config("test_scanner")
    
    assert scanner_config.enabled is True
    assert scanner_config.timeout == 300


if __name__ == "__main__":
    pytest.main([__file__]) 