"""
Модуль конфигурации для PySecKit.

Содержит класс Config для управления настройками библиотеки.
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

from .exceptions import ConfigurationException


class ScannerConfig(BaseModel):
    """Конфигурация для отдельного сканнера."""
    
    enabled: bool = Field(default=True, description="Включён ли сканнер")
    timeout: int = Field(default=300, description="Таймаут выполнения в секундах")
    args: List[str] = Field(default_factory=list, description="Дополнительные аргументы")
    rules: Dict[str, Any] = Field(default_factory=dict, description="Кастомные правила")
    exclude_patterns: List[str] = Field(default_factory=list, description="Паттерны исключений")
    severity_threshold: str = Field(default="low", description="Минимальный уровень критичности")
    
    @validator('severity_threshold')
    def validate_severity(cls, v: str) -> str:
        """Валидирует уровень критичности."""
        valid_severities = ['critical', 'high', 'medium', 'low', 'info']
        if v.lower() not in valid_severities:
            raise ValueError(f"Неверный уровень критичности: {v}. Допустимы: {valid_severities}")
        return v.lower()


class ReportConfig(BaseModel):
    """Конфигурация для отчётов."""
    
    output_dir: str = Field(default="./reports", description="Директория для отчётов")
    formats: List[str] = Field(default=["json", "html"], description="Форматы отчётов")
    template_dir: Optional[str] = Field(default=None, description="Директория шаблонов")
    include_metadata: bool = Field(default=True, description="Включать метаданные")
    group_by_severity: bool = Field(default=True, description="Группировать по критичности")
    

class CICDConfig(BaseModel):
    """Конфигурация для CI/CD интеграции."""
    
    fail_on_critical: bool = Field(default=True, description="Останавливать на критичных")
    fail_on_high: bool = Field(default=False, description="Останавливать на высоких")
    max_issues: Optional[int] = Field(default=None, description="Максимальное количество проблем")
    notifications: Dict[str, Any] = Field(default_factory=dict, description="Настройки уведомлений")


class CloudConfig(BaseModel):
    """Конфигурация для облачных провайдеров."""
    
    aws_profile: Optional[str] = Field(default=None, description="AWS профиль")
    azure_subscription: Optional[str] = Field(default=None, description="Azure подписка")
    gcp_project: Optional[str] = Field(default=None, description="GCP проект")
    scan_terraform: bool = Field(default=True, description="Сканировать Terraform")
    scan_cloudformation: bool = Field(default=True, description="Сканировать CloudFormation")


class Config(BaseModel):
    """Основной класс конфигурации PySecKit."""
    
    # Общие настройки
    project_name: str = Field(default="PySecKit Project", description="Название проекта")
    target_directories: List[str] = Field(default=["."], description="Целевые директории")
    exclude_patterns: List[str] = Field(
        default=[
            "*.git*", "*.svn*", "*.hg*",
            "*node_modules*", "*venv*", "*env*",
            "*.pyc", "*.pyo", "*.egg-info*",
            "*__pycache__*", "*.coverage*",
            "*dist*", "*build*"
        ],
        description="Глобальные паттерны исключений"
    )
    
    # Конфигурации модулей
    scanners: Dict[str, ScannerConfig] = Field(default_factory=dict, description="Настройки сканнеров")
    reporting: ReportConfig = Field(default_factory=ReportConfig, description="Настройки отчётов")
    cicd: CICDConfig = Field(default_factory=CICDConfig, description="Настройки CI/CD")
    cloud: CloudConfig = Field(default_factory=CloudConfig, description="Настройки облака")
    
    # Плагины
    plugins: List[str] = Field(default_factory=list, description="Список плагинов")
    plugin_directories: List[str] = Field(default_factory=list, description="Директории плагинов")
    
    class Config:
        """Конфигурация модели."""
        extra = "allow"  # Разрешаем дополнительные поля
    
    @classmethod
    def from_file(cls, config_path: Union[str, Path]) -> "Config":
        """
        Загружает конфигурацию из файла.
        
        Args:
            config_path: Путь к файлу конфигурации
            
        Returns:
            Экземпляр конфигурации
            
        Raises:
            ConfigurationException: При ошибке загрузки
        """
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise ConfigurationException(
                f"Файл конфигурации не найден: {config_path}",
                config_path=str(config_path)
            )
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix.lower() in ['.yml', '.yaml']:
                    data = yaml.safe_load(f)
                elif config_path.suffix.lower() == '.json':
                    import json
                    data = json.load(f)
                else:
                    raise ConfigurationException(
                        f"Неподдерживаемый формат файла: {config_path.suffix}",
                        config_path=str(config_path)
                    )
            
            if data is None:
                data = {}
                
            return cls.parse_obj(data)
            
        except yaml.YAMLError as e:
            raise ConfigurationException(
                f"Ошибка парсинга YAML: {e}",
                config_path=str(config_path)
            ) from e
        except Exception as e:
            raise ConfigurationException(
                f"Ошибка загрузки конфигурации: {e}",
                config_path=str(config_path)
            ) from e
    
    @classmethod
    def from_env(cls) -> "Config":
        """
        Создаёт конфигурацию из переменных окружения.
        
        Returns:
            Экземпляр конфигурации
        """
        data = {}
        
        # Базовые настройки
        if project_name := os.getenv("PYSECKIT_PROJECT_NAME"):
            data["project_name"] = project_name
        
        if target_dirs := os.getenv("PYSECKIT_TARGET_DIRS"):
            data["target_directories"] = target_dirs.split(",")
        
        if exclude := os.getenv("PYSECKIT_EXCLUDE_PATTERNS"):
            data["exclude_patterns"] = exclude.split(",")
        
        # CI/CD настройки
        cicd_data = {}
        if os.getenv("PYSECKIT_FAIL_ON_CRITICAL"):
            cicd_data["fail_on_critical"] = os.getenv("PYSECKIT_FAIL_ON_CRITICAL").lower() == "true"
        
        if os.getenv("PYSECKIT_FAIL_ON_HIGH"):
            cicd_data["fail_on_high"] = os.getenv("PYSECKIT_FAIL_ON_HIGH").lower() == "true"
        
        if max_issues := os.getenv("PYSECKIT_MAX_ISSUES"):
            try:
                cicd_data["max_issues"] = int(max_issues)
            except ValueError:
                pass
        
        if cicd_data:
            data["cicd"] = cicd_data
        
        # Облачные настройки
        cloud_data = {}
        if aws_profile := os.getenv("AWS_PROFILE"):
            cloud_data["aws_profile"] = aws_profile
        
        if azure_sub := os.getenv("AZURE_SUBSCRIPTION_ID"):
            cloud_data["azure_subscription"] = azure_sub
        
        if gcp_project := os.getenv("GOOGLE_CLOUD_PROJECT"):
            cloud_data["gcp_project"] = gcp_project
        
        if cloud_data:
            data["cloud"] = cloud_data
        
        return cls.parse_obj(data)
    
    def to_file(self, config_path: Union[str, Path], format: str = "yaml") -> None:
        """
        Сохраняет конфигурацию в файл.
        
        Args:
            config_path: Путь к файлу конфигурации
            format: Формат файла ('yaml' или 'json')
            
        Raises:
            ConfigurationException: При ошибке сохранения
        """
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            data = self.dict(exclude_none=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                if format.lower() in ['yml', 'yaml']:
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True, indent=2)
                elif format.lower() == 'json':
                    import json
                    json.dump(data, f, indent=2, ensure_ascii=False)
                else:
                    raise ConfigurationException(f"Неподдерживаемый формат: {format}")
                    
        except Exception as e:
            raise ConfigurationException(
                f"Ошибка сохранения конфигурации: {e}",
                config_path=str(config_path)
            ) from e
    
    def get_scanner_config(self, scanner_name: str) -> ScannerConfig:
        """
        Возвращает конфигурацию для сканнера.
        
        Args:
            scanner_name: Имя сканнера
            
        Returns:
            Конфигурация сканнера
        """
        if scanner_name not in self.scanners:
            self.scanners[scanner_name] = ScannerConfig()
        
        return self.scanners[scanner_name]
    
    def set_scanner_config(self, scanner_name: str, config: ScannerConfig) -> None:
        """
        Устанавливает конфигурацию для сканнера.
        
        Args:
            scanner_name: Имя сканнера
            config: Конфигурация сканнера
        """
        self.scanners[scanner_name] = config
    
    def is_scanner_enabled(self, scanner_name: str) -> bool:
        """
        Проверяет, включён ли сканнер.
        
        Args:
            scanner_name: Имя сканнера
            
        Returns:
            True если сканнер включён
        """
        scanner_config = self.get_scanner_config(scanner_name)
        return scanner_config.enabled
    
    def get_target_files(self) -> List[Path]:
        """
        Возвращает список файлов для сканирования с учётом исключений.
        
        Returns:
            Список путей к файлам
        """
        import fnmatch
        
        files = []
        
        for target_dir in self.target_directories:
            target_path = Path(target_dir)
            
            if target_path.is_file():
                files.append(target_path)
            elif target_path.is_dir():
                for file_path in target_path.rglob("*"):
                    if file_path.is_file():
                        # Проверяем исключения
                        excluded = False
                        for pattern in self.exclude_patterns:
                            if fnmatch.fnmatch(str(file_path), pattern):
                                excluded = True
                                break
                        
                        if not excluded:
                            files.append(file_path)
        
        return files
    
    @classmethod
    def get_default_config_paths(cls) -> List[Path]:
        """
        Возвращает список путей для поиска конфигурации по умолчанию.
        
        Returns:
            Список путей к файлам конфигурации
        """
        return [
            Path(".pyseckit.yml"),
            Path(".pyseckit.yaml"),
            Path("pyseckit.yml"),
            Path("pyseckit.yaml"),
            Path(".config/pyseckit.yml"),
            Path("~/.pyseckit.yml").expanduser(),
            Path("~/.config/pyseckit.yml").expanduser(),
        ]
    
    @classmethod
    def load_default(cls) -> "Config":
        """
        Загружает конфигурацию из файла по умолчанию или создаёт новую.
        
        Returns:
            Экземпляр конфигурации
        """
        # Пробуем найти файл конфигурации
        for config_path in cls.get_default_config_paths():
            if config_path.exists():
                try:
                    return cls.from_file(config_path)
                except ConfigurationException:
                    continue
        
        # Если файл не найден, создаём конфигурацию из переменных окружения
        return cls.from_env() 