"""
Safety сканнер для проверки уязвимых зависимостей Python.
"""

import json
import shutil
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..core.exceptions import ScannerException
from ..core.scanner import Scanner, ScanResult, Severity


class SafetyScanner(Scanner):
    """Сканнер Safety для проверки уязвимых зависимостей."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Инициализирует Safety сканнер."""
        super().__init__(config)
        self._severity_mapping = {
            "HIGH": Severity.HIGH,
            "MEDIUM": Severity.MEDIUM, 
            "LOW": Severity.LOW,
        }
    
    @property
    def scanner_name(self) -> str:
        """Возвращает имя сканнера."""
        return "safety"
    
    @property
    def version(self) -> str:
        """Возвращает версию Safety."""
        try:
            result = self.run_command(["safety", "--version"], timeout=10)
            if result.returncode == 0:
                return result.stdout.strip().split()[-1]
            return "unknown"
        except ScannerException:
            return "unknown"
    
    @property
    def supported_formats(self) -> List[str]:
        """Возвращает поддерживаемые форматы файлов."""
        return [".txt", ".in", ".pip", "requirements.txt", "Pipfile", "pyproject.toml"]
    
    def is_available(self) -> bool:
        """Проверяет доступность Safety в системе."""
        return shutil.which("safety") is not None
    
    def scan(self, target: Union[str, Path], **kwargs) -> List[ScanResult]:
        """
        Выполняет сканирование с помощью Safety.
        
        Args:
            target: Путь к файлу требований или директории проекта
            **kwargs: Дополнительные параметры:
                - requirements_file: Путь к файлу требований
                - ignore_ids: Список ID уязвимостей для игнорирования
                - full_report: Полный отчёт с дополнительной информацией
                - audit_and_monitor: Отправка данных в Safety DB
                - continue_on_error: Продолжить при ошибках
        
        Returns:
            Список результатов сканирования
            
        Raises:
            ScannerException: При ошибке сканирования
        """
        if not self.is_available():
            raise ScannerException("Safety не найден в системе", scanner_name=self.scanner_name)
        
        target_path = Path(target)
        
        # Очищаем предыдущие результаты
        self.clear_results()
        
        # Подготавливаем команду
        command = ["safety", "check"]
        
        # Формат вывода JSON
        command.extend(["--output", "json"])
        
        # Определяем файл требований
        requirements_file = kwargs.get("requirements_file")
        if requirements_file:
            command.extend(["--file", str(requirements_file)])
        elif target_path.is_file():
            command.extend(["--file", str(target_path)])
        elif target_path.is_dir():
            # Ищем файлы требований в директории
            req_files = self._find_requirements_files(target_path)
            if req_files:
                command.extend(["--file", str(req_files[0])])
            else:
                # Проверяем установленные пакеты
                pass  # safety check без --file проверит установленные пакеты
        
        # Игнорирование уязвимостей
        ignore_ids = kwargs.get("ignore_ids", [])
        for ignore_id in ignore_ids:
            command.extend(["--ignore", str(ignore_id)])
        
        # Полный отчёт
        if kwargs.get("full_report", False):
            command.append("--full-report")
        
        # Продолжить при ошибках
        if kwargs.get("continue_on_error", True):
            command.append("--continue-on-error")
        
        # Получаем таймаут из конфигурации
        timeout = self.config.get("timeout", 300)
        
        # Выполняем сканирование
        try:
            result = self.run_command(command, timeout=timeout)
            
            # Safety возвращает exit code > 0 при обнаружении уязвимостей
            if result.returncode not in [0, 1, 2]:  # 0 = OK, 1 = vulnerabilities, 2 = other errors
                raise ScannerException(
                    f"Safety завершился с ошибкой (код {result.returncode})",
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
                f"Ошибка парсинга JSON результатов Safety: {e}",
                scanner_name=self.scanner_name,
                details={"stdout": result.stdout, "stderr": result.stderr}
            ) from e
    
    def _parse_results(self, json_output: str, target_path: Path) -> List[ScanResult]:
        """
        Парсит JSON результаты Safety.
        
        Args:
            json_output: JSON вывод Safety
            target_path: Путь к цели сканирования
            
        Returns:
            Список результатов сканирования
        """
        if not json_output.strip():
            return []
        
        try:
            # Safety может возвращать массив объектов или объект со списком
            if json_output.strip().startswith('['):
                vulnerabilities = json.loads(json_output)
            else:
                data = json.loads(json_output)
                vulnerabilities = data.get("vulnerabilities", [])
        except json.JSONDecodeError:
            # Если JSON невалиден, возвращаем пустой список
            return []
        
        results = []
        
        # Обрабатываем уязвимости
        for vuln in vulnerabilities:
            # Создаём уникальный ID
            result_id = str(uuid.uuid4())
            
            # Определяем критичность (Safety обычно не предоставляет severity)
            # Пытаемся определить по CVSS или другим полям
            severity = self._determine_severity(vuln)
            
            # Получаем информацию о пакете
            package_name = vuln.get("package_name", "")
            affected_versions = vuln.get("affected_versions", [])
            installed_version = vuln.get("analyzed_version", "")
            
            # ID уязвимости
            vulnerability_id = vuln.get("vulnerability_id", "")
            cve_id = vuln.get("CVE", "")
            
            # Создаём описание
            title = f"Уязвимый пакет: {package_name}"
            description = vuln.get("advisory", "")
            if not description:
                description = f"Пакет {package_name} версии {installed_version} содержит известную уязвимость"
            
            # Создаём результат
            scan_result = ScanResult(
                id=result_id,
                scanner_name=self.scanner_name,
                title=title,
                description=description,
                severity=severity,
                file_path=str(target_path) if target_path.is_file() else None,
                rule_id=vulnerability_id,
                cwe_id=cve_id if cve_id.startswith("CVE-") else None,
                metadata={
                    "package_name": package_name,
                    "installed_version": installed_version,
                    "affected_versions": affected_versions,
                    "vulnerability_id": vulnerability_id,
                    "cve": cve_id,
                    "more_info_url": vuln.get("more_info_url", ""),
                    "specifications": vuln.get("specifications", []),
                }
            )
            
            results.append(scan_result)
        
        return results
    
    def _determine_severity(self, vulnerability: Dict[str, Any]) -> Severity:
        """
        Определяет критичность уязвимости.
        
        Args:
            vulnerability: Данные уязвимости
            
        Returns:
            Уровень критичности
        """
        # Проверяем наличие CVSS
        if "cvss" in vulnerability:
            try:
                cvss_score = float(vulnerability["cvss"])
                if cvss_score >= 9.0:
                    return Severity.CRITICAL
                elif cvss_score >= 7.0:
                    return Severity.HIGH
                elif cvss_score >= 4.0:
                    return Severity.MEDIUM
                else:
                    return Severity.LOW
            except (ValueError, TypeError):
                pass
        
        # Проверяем ключевые слова в описании
        advisory = vulnerability.get("advisory", "").lower()
        if any(keyword in advisory for keyword in ["critical", "remote code execution", "rce"]):
            return Severity.CRITICAL
        elif any(keyword in advisory for keyword in ["high", "privilege escalation", "sql injection"]):
            return Severity.HIGH
        elif any(keyword in advisory for keyword in ["medium", "denial of service", "xss"]):
            return Severity.MEDIUM
        
        # По умолчанию средний уровень
        return Severity.MEDIUM
    
    def _find_requirements_files(self, directory: Path) -> List[Path]:
        """
        Находит файлы требований в директории.
        
        Args:
            directory: Директория для поиска
            
        Returns:
            Список найденных файлов требований
        """
        patterns = [
            "requirements.txt",
            "requirements-dev.txt", 
            "requirements-prod.txt",
            "requirements/*.txt",
            "Pipfile",
            "pyproject.toml",
            "setup.py",
        ]
        
        found_files = []
        
        for pattern in patterns:
            if "/" in pattern:
                # Поиск по паттерну в подпапках
                for file_path in directory.glob(pattern):
                    if file_path.is_file():
                        found_files.append(file_path)
            else:
                # Поиск файла в корне
                file_path = directory / pattern
                if file_path.exists() and file_path.is_file():
                    found_files.append(file_path)
        
        return found_files
    
    def check_requirements_file(self, requirements_file: Union[str, Path]) -> List[ScanResult]:
        """
        Проверяет конкретный файл требований.
        
        Args:
            requirements_file: Путь к файлу требований
            
        Returns:
            Список результатов сканирования
        """
        return self.scan(requirements_file, requirements_file=requirements_file)
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Получает информацию о базе данных уязвимостей Safety.
        
        Returns:
            Информация о базе данных
        """
        try:
            result = self.run_command(["safety", "--version"], timeout=10)
            return {
                "version": result.stdout.strip() if result.returncode == 0 else "unknown",
                "database_source": "PyUp.io Safety DB",
                "last_updated": "unknown"  # Safety не предоставляет эту информацию в CLI
            }
        except ScannerException:
            return {
                "version": "unknown",
                "database_source": "PyUp.io Safety DB",
                "last_updated": "unknown"
            } 