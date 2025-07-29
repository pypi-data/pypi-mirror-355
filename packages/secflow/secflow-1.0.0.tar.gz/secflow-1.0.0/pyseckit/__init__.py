"""
PySecKit - Универсальный фреймворк для интеграции Security в процессы разработки и CI/CD.

Поддерживает SAST, DAST, secret-scanning, threat modeling, отчёты и оповещения.
"""

__version__ = "1.0.0"
__author__ = "PySecKit Contributors"
__email__ = "info@pyseckit.org"

from .core.scanner import Scanner, ScanResult, ScannerManager
from .core.config import Config
from .core.exceptions import PySecKitException, ScannerException
from .reporting.manager import ReportManager
from .ci_cd.manager import CICDManager

# Импорт сканнеров
from .sast import BanditScanner, SemgrepScanner, SafetyScanner
from .dast import ZapScanner
from .secret_scan import GitleaksScanner, TruffleHogScanner
from .cloud import CheckovScanner
from .threat_model import ThreatModelGenerator, AdvancedThreatModelGenerator

# Импорт расширенных модулей
from .plugins import PluginRegistry, PluginBase, ScannerPlugin
from .integrations import ElasticsearchIntegration, NotificationManager, SlackNotifier, TeamsNotifier
from .web import create_app, api_bp, dashboard_bp

__all__ = [
    # Основные классы
    "Scanner",
    "ScanResult", 
    "ScannerManager",
    "Config",
    "PySecKitException",
    "ScannerException",
    "ReportManager",
    "CICDManager",
    
    # SAST сканнеры
    "BanditScanner",
    "SemgrepScanner", 
    "SafetyScanner",
    
    # DAST сканнеры
    "ZapScanner",
    
    # Secret сканнеры
    "GitleaksScanner",
    "TruffleHogScanner",
    
    # Cloud сканнеры
    "CheckovScanner",
    
    # Threat modeling
    "ThreatModelGenerator",
    "AdvancedThreatModelGenerator",
    
    # Система плагинов
    "PluginRegistry",
    "PluginBase", 
    "ScannerPlugin",
    
    # Интеграции
    "ElasticsearchIntegration",
    "NotificationManager",
    "SlackNotifier",
    "TeamsNotifier",
    
    # Веб-интерфейс
    "create_app",
    "api_bp",
    "dashboard_bp",
]

# Версия библиотеки для совместимости
VERSION = __version__ 