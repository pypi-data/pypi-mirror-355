"""
Semgrep сканнер для многоязычного статического анализа безопасности.
"""

import json
import shutil
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..core.exceptions import ScannerException
from ..core.scanner import Scanner, ScanResult, Severity


class SemgrepScanner(Scanner):
    """Сканнер Semgrep для многоязычного анализа."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Инициализирует Semgrep сканнер."""
        super().__init__(config)
        self._severity_mapping = {
            "ERROR": Severity.HIGH,
            "WARNING": Severity.MEDIUM,
            "INFO": Severity.LOW,
        }
    
    @property
    def scanner_name(self) -> str:
        """Возвращает имя сканнера."""
        return "semgrep"
    
    @property
    def version(self) -> str:
        """Возвращает версию Semgrep."""
        try:
            result = self.run_command(["semgrep", "--version"], timeout=10)
            if result.returncode == 0:
                return result.stdout.strip()
            return "unknown"
        except ScannerException:
            return "unknown"
    
    @property
    def supported_formats(self) -> List[str]:
        """Возвращает поддерживаемые форматы файлов."""
        return [
            ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rb", 
            ".php", ".c", ".cpp", ".cs", ".scala", ".kt", ".swift",
            ".yml", ".yaml", ".json", ".xml", ".tf", ".hcl"
        ]
    
    def is_available(self) -> bool:
        """Проверяет доступность Semgrep в системе."""
        return shutil.which("semgrep") is not None
    
    def scan(self, target: Union[str, Path], **kwargs) -> List[ScanResult]:
        """
        Выполняет сканирование с помощью Semgrep.
        
        Args:
            target: Путь к файлу или директории для сканирования
            **kwargs: Дополнительные параметры:
                - config: Конфигурация правил (auto, p/security-audit, custom path)
                - ruleset: Набор правил (owasp-top-10, cwe-top-25, auto)
                - exclude: Паттерны исключений
                - include: Паттерны включений
                - max_target_bytes: Максимальный размер файла
                - timeout: Таймаут сканирования
                - severity: Минимальный уровень критичности
        
        Returns:
            Список результатов сканирования
            
        Raises:
            ScannerException: При ошибке сканирования
        """
        if not self.is_available():
            raise ScannerException("Semgrep не найден в системе", scanner_name=self.scanner_name)
        
        target_path = Path(target)
        if not target_path.exists():
            raise ScannerException(f"Цель сканирования не найдена: {target}", scanner_name=self.scanner_name)
        
        # Очищаем предыдущие результаты
        self.clear_results()
        
        # Подготавливаем команду
        command = ["semgrep"]
        
        # Формат вывода JSON
        command.extend(["--json"])
        
        # Конфигурация правил
        config = kwargs.get("config", "auto")
        if config == "auto":
            command.extend(["--config=auto"])
        elif config == "security":
            command.extend(["--config=p/security-audit"])
        elif config == "owasp":
            command.extend(["--config=p/owasp-top-ten"])
        elif config == "cwe":
            command.extend(["--config=p/cwe-top-25"])
        else:
            command.extend([f"--config={config}"])
        
        # Исключения
        exclude_patterns = kwargs.get("exclude", [])
        for pattern in exclude_patterns:
            command.extend(["--exclude", pattern])
        
        # Включения
        include_patterns = kwargs.get("include", [])
        for pattern in include_patterns:
            command.extend(["--include", pattern])
        
        # Максимальный размер файла
        max_target_bytes = kwargs.get("max_target_bytes")
        if max_target_bytes:
            command.extend(["--max-target-bytes", str(max_target_bytes)])
        
        # Таймаут
        timeout_param = kwargs.get("timeout")
        if timeout_param:
            command.extend(["--timeout", str(timeout_param)])
        
        # Уровень детализации
        command.extend(["--quiet"])
        
        # Отключаем аналитику
        command.extend(["--metrics", "off"])
        
        # Добавляем цель сканирования
        command.append(str(target_path))
        
        # Получаем таймаут из конфигурации
        execution_timeout = self.config.get("timeout", 300)
        
        # Выполняем сканирование
        try:
            result = self.run_command(command, timeout=execution_timeout)
            
            # Semgrep возвращает exit code > 0 при обнаружении проблем
            if result.returncode > 2:  # 0 = нет проблем, 1 = есть проблемы, 2 = ошибки
                raise ScannerException(
                    f"Semgrep завершился с ошибкой (код {result.returncode})",
                    scanner_name=self.scanner_name,
                    exit_code=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr
                )
            
            # Парсим результаты
            results = self._parse_results(result.stdout, target_path)
            
            # Фильтруем по минимальному уровню критичности
            min_severity = kwargs.get("severity")
            if min_severity:
                severity_levels = {
                    "info": [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO],
                    "low": [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW],
                    "medium": [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM],
                    "high": [Severity.CRITICAL, Severity.HIGH],
                    "critical": [Severity.CRITICAL]
                }
                allowed_severities = severity_levels.get(min_severity.lower(), severity_levels["info"])
                results = [r for r in results if r.severity in allowed_severities]
            
            # Добавляем результаты
            for scan_result in results:
                self._add_result(scan_result)
            
            return self.get_results()
            
        except json.JSONDecodeError as e:
            raise ScannerException(
                f"Ошибка парсинга JSON результатов Semgrep: {e}",
                scanner_name=self.scanner_name,
                details={"stdout": result.stdout, "stderr": result.stderr}
            ) from e
    
    def _parse_results(self, json_output: str, target_path: Path) -> List[ScanResult]:
        """
        Парсит JSON результаты Semgrep.
        
        Args:
            json_output: JSON вывод Semgrep
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
        for finding in data.get("results", []):
            # Создаём уникальный ID
            result_id = str(uuid.uuid4())
            
            # Определяем критичность
            severity_str = finding.get("extra", {}).get("severity", "INFO").upper()
            severity = self._severity_mapping.get(severity_str, Severity.INFO)
            
            # Получаем информацию о файле
            file_path = finding.get("path", "")
            start_line = finding.get("start", {}).get("line")
            start_col = finding.get("start", {}).get("col")
            
            # Метаданные
            extra = finding.get("extra", {})
            
            # CWE информация
            cwe_ids = extra.get("metadata", {}).get("cwe", [])
            cwe_id = None
            if cwe_ids and isinstance(cwe_ids, list):
                cwe_id = f"CWE-{cwe_ids[0]}" if cwe_ids[0] else None
            
            # OWASP категория
            owasp_categories = extra.get("metadata", {}).get("owasp", [])
            owasp_category = owasp_categories[0] if owasp_categories else None
            
            # Создаём результат
            scan_result = ScanResult(
                id=result_id,
                scanner_name=self.scanner_name,
                title=extra.get("message", ""),
                description=extra.get("message", ""),
                severity=severity,
                file_path=file_path,
                line_number=start_line,
                column_number=start_col,
                rule_id=finding.get("check_id", ""),
                cwe_id=cwe_id,
                owasp_category=owasp_category,
                confidence=extra.get("confidence", ""),
                remediation=extra.get("metadata", {}).get("fix_regex", {}).get("message"),
                metadata={
                    "category": extra.get("metadata", {}).get("category", []),
                    "technology": extra.get("metadata", {}).get("technology", []),
                    "references": extra.get("metadata", {}).get("references", []),
                    "impact": extra.get("impact", ""),
                    "likelihood": extra.get("likelihood", ""),
                    "end_line": finding.get("end", {}).get("line"),
                    "end_col": finding.get("end", {}).get("col"),
                    "semgrep_url": extra.get("metadata", {}).get("semgrep.url", ""),
                }
            )
            
            results.append(scan_result)
        
        return results
    
    def get_available_rulesets(self) -> List[str]:
        """
        Возвращает список доступных наборов правил.
        
        Returns:
            Список доступных наборов правил
        """
        try:
            result = self.run_command(["semgrep", "--config", "--help"], timeout=10)
            # Это базовые наборы, в реальности их может быть больше
            return [
                "auto",
                "p/security-audit", 
                "p/owasp-top-ten",
                "p/cwe-top-25",
                "p/ci",
                "p/secrets",
                "p/python",
                "p/javascript",
                "p/java",
                "p/go",
                "p/ruby",
                "p/php",
                "p/c",
                "p/csharp",
            ]
        except ScannerException:
            return ["auto", "p/security-audit"]
    
    def get_language_support(self) -> Dict[str, List[str]]:
        """
        Возвращает информацию о поддерживаемых языках.
        
        Returns:
            Словарь с поддерживаемыми языками и их расширениями
        """
        return {
            "Python": [".py"],
            "JavaScript": [".js", ".jsx"],
            "TypeScript": [".ts", ".tsx"],
            "Java": [".java"],
            "Go": [".go"],
            "Ruby": [".rb"],
            "PHP": [".php"],
            "C": [".c"],
            "C++": [".cpp", ".cc", ".cxx"],
            "C#": [".cs"],
            "Scala": [".scala"],
            "Kotlin": [".kt"],
            "Swift": [".swift"],
            "Terraform": [".tf", ".hcl"],
            "YAML": [".yml", ".yaml"],
            "JSON": [".json"],
            "XML": [".xml"],
        }
    
    def create_custom_rule(self, rule_path: Union[str, Path], rule_config: Dict[str, Any]) -> None:
        """
        Создаёт кастомное правило Semgrep.
        
        Args:
            rule_path: Путь к файлу правила
            rule_config: Конфигурация правила
        """
        rule_path = Path(rule_path)
        rule_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Базовая структура правила Semgrep
        rule = {
            "rules": [
                {
                    "id": rule_config.get("id", "custom-rule"),
                    "pattern": rule_config.get("pattern", ""),
                    "message": rule_config.get("message", "Custom security rule"),
                    "languages": rule_config.get("languages", ["python"]),
                    "severity": rule_config.get("severity", "WARNING").upper(),
                    "metadata": {
                        "category": rule_config.get("category", "security"),
                        "cwe": rule_config.get("cwe", []),
                        "owasp": rule_config.get("owasp", []),
                        "references": rule_config.get("references", []),
                    }
                }
            ]
        }
        
        import yaml
        with open(rule_path, 'w', encoding='utf-8') as f:
            yaml.dump(rule, f, default_flow_style=False, allow_unicode=True) 