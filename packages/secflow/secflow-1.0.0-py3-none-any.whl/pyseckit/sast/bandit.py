"""
Bandit сканнер для статического анализа безопасности Python кода.
"""

import json
import shutil
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..core.exceptions import ScannerException
from ..core.scanner import Scanner, ScanResult, Severity


class BanditScanner(Scanner):
    """Сканнер Bandit для Python кода."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Инициализирует Bandit сканнер."""
        super().__init__(config)
        self._severity_mapping = {
            "HIGH": Severity.HIGH,
            "MEDIUM": Severity.MEDIUM,
            "LOW": Severity.LOW,
        }
    
    @property
    def scanner_name(self) -> str:
        """Возвращает имя сканнера."""
        return "bandit"
    
    @property
    def version(self) -> str:
        """Возвращает версию Bandit."""
        try:
            result = self.run_command(["bandit", "--version"], timeout=10)
            if result.returncode == 0:
                # Парсим вывод "bandit 1.7.5"
                return result.stdout.strip().split()[-1]
            return "unknown"
        except ScannerException:
            return "unknown"
    
    @property
    def supported_formats(self) -> List[str]:
        """Возвращает поддерживаемые форматы файлов."""
        return [".py"]
    
    def is_available(self) -> bool:
        """Проверяет доступность Bandit в системе."""
        return shutil.which("bandit") is not None
    
    def scan(self, target: Union[str, Path], **kwargs) -> List[ScanResult]:
        """
        Выполняет сканирование с помощью Bandit.
        
        Args:
            target: Путь к файлу или директории для сканирования
            **kwargs: Дополнительные параметры:
                - config_file: Путь к файлу конфигурации Bandit
                - skip_tests: Пропускать тестовые файлы (по умолчанию True)
                - confidence: Минимальный уровень уверенности (low, medium, high)
                - severity: Минимальный уровень критичности (low, medium, high)
                - exclude_dirs: Список директорий для исключения
                - include_tests: Включать тестовые файлы
        
        Returns:
            Список результатов сканирования
            
        Raises:
            ScannerException: При ошибке сканирования
        """
        if not self.is_available():
            raise ScannerException("Bandit не найден в системе", scanner_name=self.scanner_name)
        
        target_path = Path(target)
        if not target_path.exists():
            raise ScannerException(f"Цель сканирования не найдена: {target}", scanner_name=self.scanner_name)
        
        # Очищаем предыдущие результаты
        self.clear_results()
        
        # Подготавливаем команду
        command = ["bandit"]
        
        # Формат вывода JSON
        command.extend(["-f", "json"])
        
        # Рекурсивное сканирование для директорий
        if target_path.is_dir():
            command.append("-r")
        
        # Дополнительные параметры
        config_file = kwargs.get("config_file")
        if config_file:
            command.extend(["-c", str(config_file)])
        
        skip_tests = kwargs.get("skip_tests", True)
        if not skip_tests or kwargs.get("include_tests", False):
            command.append("--include-tests")
        
        confidence = kwargs.get("confidence")
        if confidence:
            command.extend(["-i", confidence.lower()])
        
        severity = kwargs.get("severity")
        if severity:
            command.extend(["-l", severity.lower()])
        
        exclude_dirs = kwargs.get("exclude_dirs", [])
        for exclude_dir in exclude_dirs:
            command.extend(["-x", exclude_dir])
        
        # Добавляем цель сканирования
        command.append(str(target_path))
        
        # Получаем таймаут из конфигурации
        timeout = self.config.get("timeout", 300)
        
        # Выполняем сканирование
        try:
            result = self.run_command(command, timeout=timeout)
            
            # Bandit возвращает exit code 1 при обнаружении проблем, это нормально
            if result.returncode not in [0, 1]:
                raise ScannerException(
                    f"Bandit завершился с ошибкой (код {result.returncode})",
                    scanner_name=self.scanner_name,
                    exit_code=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr
                )
            
            # Парсим результаты
            results = self._parse_results(result.stdout, target_path)
            
            # Добавляем результаты
            for scan_result in results:
                self._add_result(scan_result)
            
            return self.get_results()
            
        except json.JSONDecodeError as e:
            raise ScannerException(
                f"Ошибка парсинга JSON результатов Bandit: {e}",
                scanner_name=self.scanner_name,
                details={"stdout": result.stdout, "stderr": result.stderr}
            ) from e
    
    def _parse_results(self, json_output: str, target_path: Path) -> List[ScanResult]:
        """
        Парсит JSON результаты Bandit.
        
        Args:
            json_output: JSON вывод Bandit
            target_path: Путь к цели сканирования
            
        Returns:
            Список результатов сканирования
        """
        if not json_output.strip():
            return []
        
        try:
            data = json.loads(json_output)
        except json.JSONDecodeError:
            # Если JSON невалиден, возвращаем пустой список
            return []
        
        results = []
        
        # Обрабатываем результаты
        for issue in data.get("results", []):
            # Создаём уникальный ID
            result_id = str(uuid.uuid4())
            
            # Определяем критичность
            severity_str = issue.get("issue_severity", "LOW").upper()
            severity = self._severity_mapping.get(severity_str, Severity.LOW)
            
            # Получаем информацию о файле
            filename = issue.get("filename", "")
            line_number = issue.get("line_number")
            
            # CWE информация
            cwe_info = issue.get("more_info", "")
            cwe_id = None
            if "CWE-" in cwe_info:
                try:
                    cwe_id = cwe_info.split("CWE-")[1].split("/")[0].split(")")[0]
                    cwe_id = f"CWE-{cwe_id}"
                except (IndexError, ValueError):
                    pass
            
            # Создаём результат
            scan_result = ScanResult(
                id=result_id,
                scanner_name=self.scanner_name,
                title=issue.get("test_name", ""),
                description=issue.get("issue_text", ""),
                severity=severity,
                file_path=filename,
                line_number=line_number,
                rule_id=issue.get("test_id", ""),
                cwe_id=cwe_id,
                confidence=issue.get("issue_confidence", ""),
                code_snippet=issue.get("code", ""),
                metadata={
                    "more_info": issue.get("more_info", ""),
                    "line_range": issue.get("line_range", []),
                    "col_offset": issue.get("col_offset"),
                    "filename": filename,
                }
            )
            
            results.append(scan_result)
        
        return results
    
    def get_default_config(self) -> Dict[str, Any]:
        """
        Возвращает конфигурацию Bandit по умолчанию.
        
        Returns:
            Словарь с конфигурацией
        """
        return {
            "skip_tests": True,
            "confidence": "low",
            "severity": "low",
            "exclude_dirs": [
                "/.tox/",
                "/tests/",
                "/test/",
                "/.venv/",
                "/venv/",
                "/env/",
                "/.env/",
                "/node_modules/",
                "/.git/",
                "/dist/",
                "/build/",
                "/__pycache__/",
            ]
        }
    
    def create_config_file(self, config_path: Union[str, Path], custom_config: Optional[Dict[str, Any]] = None) -> None:
        """
        Создаёт файл конфигурации Bandit.
        
        Args:
            config_path: Путь к файлу конфигурации
            custom_config: Кастомная конфигурация
        """
        config = self.get_default_config()
        if custom_config:
            config.update(custom_config)
        
        # Конвертируем в формат Bandit
        bandit_config = {
            "tests": ["B101", "B102", "B103", "B104", "B105", "B106", "B107", "B108", "B110", 
                     "B112", "B201", "B301", "B302", "B303", "B304", "B305", "B306", "B307", 
                     "B308", "B309", "B310", "B311", "B312", "B313", "B314", "B315", "B316", 
                     "B317", "B318", "B319", "B320", "B321", "B322", "B323", "B324", "B325", 
                     "B401", "B402", "B403", "B404", "B405", "B406", "B407", "B408", "B409", 
                     "B410", "B411", "B412", "B413", "B501", "B502", "B503", "B504", "B505", 
                     "B506", "B507", "B601", "B602", "B603", "B604", "B605", "B606", "B607", 
                     "B608", "B609", "B610", "B611", "B701", "B702", "B703"],
            "skips": ["B101"],  # Пример исключений
        }
        
        if "exclude_dirs" in config:
            bandit_config["exclude_dirs"] = config["exclude_dirs"]
        
        # Сохраняем в YAML формате
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        import yaml
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(bandit_config, f, default_flow_style=False, allow_unicode=True) 