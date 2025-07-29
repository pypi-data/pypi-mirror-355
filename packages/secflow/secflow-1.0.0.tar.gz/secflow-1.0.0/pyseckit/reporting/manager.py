"""
Менеджер генерации отчётов.
"""

import csv
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from jinja2 import Environment, FileSystemLoader, Template

from ..core.config import ReportConfig
from ..core.scanner import ScanResult, Severity
from ..core.exceptions import ReportException


class ReportManager:
    """Менеджер для генерации отчётов в различных форматах."""
    
    def __init__(self, config: ReportConfig) -> None:
        """
        Инициализирует менеджер отчётов.
        
        Args:
            config: Конфигурация отчётов
        """
        self.config = config
        self._setup_jinja()
    
    def _setup_jinja(self) -> None:
        """Настраивает Jinja2 окружение."""
        if self.config.template_dir:
            loader = FileSystemLoader(self.config.template_dir)
        else:
            # Используем встроенные шаблоны
            loader = FileSystemLoader(Path(__file__).parent / "templates")
        
        self.jinja_env = Environment(
            loader=loader,
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Добавляем фильтры
        self.jinja_env.filters['severity_color'] = self._severity_to_color
        self.jinja_env.filters['severity_icon'] = self._severity_to_icon
    
    def generate_json_report(
        self, 
        results: List[ScanResult], 
        output_path: Union[str, Path]
    ) -> None:
        """
        Генерирует JSON отчёт.
        
        Args:
            results: Список результатов сканирования
            output_path: Путь к выходному файлу
            
        Raises:
            ReportException: При ошибке генерации
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            report_data = {
                "metadata": self._generate_metadata(),
                "summary": self._generate_summary(results),
                "results": [result.dict() for result in results]
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
        
        except Exception as e:
            raise ReportException(f"Ошибка генерации JSON отчёта: {e}") from e
    
    def generate_html_report(
        self, 
        results: List[ScanResult], 
        output_path: Union[str, Path]
    ) -> None:
        """
        Генерирует HTML отчёт.
        
        Args:
            results: Список результатов сканирования
            output_path: Путь к выходному файлу
            
        Raises:
            ReportException: При ошибке генерации
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Подготавливаем данные для шаблона
            template_data = {
                "metadata": self._generate_metadata(),
                "summary": self._generate_summary(results),
                "results": results,
                "results_by_severity": self._group_by_severity(results),
                "results_by_scanner": self._group_by_scanner(results),
                "results_by_file": self._group_by_file(results),
            }
            
            # Рендерим шаблон
            try:
                template = self.jinja_env.get_template("report.html")
            except:
                # Используем встроенный шаблон
                template = self._get_default_html_template()
            
            html_content = template.render(**template_data)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
        
        except Exception as e:
            raise ReportException(f"Ошибка генерации HTML отчёта: {e}") from e
    
    def generate_csv_report(
        self, 
        results: List[ScanResult], 
        output_path: Union[str, Path]
    ) -> None:
        """
        Генерирует CSV отчёт.
        
        Args:
            results: Список результатов сканирования
            output_path: Путь к выходному файлу
            
        Raises:
            ReportException: При ошибке генерации
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            fieldnames = [
                'id', 'scanner_name', 'title', 'description', 'severity',
                'file_path', 'line_number', 'column_number', 'rule_id',
                'cwe_id', 'owasp_category', 'confidence', 'timestamp'
            ]
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in results:
                    row = {field: getattr(result, field, '') for field in fieldnames}
                    # Форматируем timestamp
                    if row['timestamp']:
                        row['timestamp'] = datetime.fromtimestamp(row['timestamp']).isoformat()
                    writer.writerow(row)
        
        except Exception as e:
            raise ReportException(f"Ошибка генерации CSV отчёта: {e}") from e
    
    def generate_xml_report(
        self, 
        results: List[ScanResult], 
        output_path: Union[str, Path]
    ) -> None:
        """
        Генерирует XML отчёт.
        
        Args:
            results: Список результатов сканирования
            output_path: Путь к выходному файлу
            
        Raises:
            ReportException: При ошибке генерации
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Создаём корневой элемент
            root = ET.Element("pyseckit_report")
            
            # Добавляем метаданные
            metadata = ET.SubElement(root, "metadata")
            meta_data = self._generate_metadata()
            for key, value in meta_data.items():
                meta_elem = ET.SubElement(metadata, key)
                meta_elem.text = str(value)
            
            # Добавляем сводку
            summary = ET.SubElement(root, "summary")
            summary_data = self._generate_summary(results)
            for key, value in summary_data.items():
                summary_elem = ET.SubElement(summary, key)
                summary_elem.text = str(value)
            
            # Добавляем результаты
            results_elem = ET.SubElement(root, "results")
            
            for result in results:
                result_elem = ET.SubElement(results_elem, "result")
                result_elem.set("id", result.id)
                
                for field_name in result.__fields__:
                    if field_name == "metadata":
                        continue  # Пропускаем сложные поля
                    
                    value = getattr(result, field_name)
                    if value is not None:
                        field_elem = ET.SubElement(result_elem, field_name)
                        if field_name == "timestamp":
                            field_elem.text = datetime.fromtimestamp(value).isoformat()
                        else:
                            field_elem.text = str(value)
            
            # Сохраняем XML
            tree = ET.ElementTree(root)
            ET.indent(tree, space="  ", level=0)
            tree.write(output_path, encoding='utf-8', xml_declaration=True)
        
        except Exception as e:
            raise ReportException(f"Ошибка генерации XML отчёта: {e}") from e
    
    def _generate_metadata(self) -> Dict[str, Any]:
        """Генерирует метаданные отчёта."""
        return {
            "generated_at": datetime.now().isoformat(),
            "generator": "PySecKit",
            "version": "1.0.0"
        }
    
    def _generate_summary(self, results: List[ScanResult]) -> Dict[str, Any]:
        """Генерирует сводку результатов."""
        if not results:
            return {
                "total_issues": 0,
                "by_severity": {},
                "by_scanner": {},
                "unique_files": 0
            }
        
        by_severity = {}
        by_scanner = {}
        files = set()
        
        for result in results:
            # По критичности
            severity = result.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1
            
            # По сканнеру
            scanner = result.scanner_name
            by_scanner[scanner] = by_scanner.get(scanner, 0) + 1
            
            # Уникальные файлы
            if result.file_path:
                files.add(result.file_path)
        
        return {
            "total_issues": len(results),
            "by_severity": by_severity,
            "by_scanner": by_scanner,
            "unique_files": len(files)
        }
    
    def _group_by_severity(self, results: List[ScanResult]) -> Dict[str, List[ScanResult]]:
        """Группирует результаты по критичности."""
        grouped = {}
        for result in results:
            severity = result.severity.value
            if severity not in grouped:
                grouped[severity] = []
            grouped[severity].append(result)
        
        # Сортируем по приоритету
        severity_order = ["critical", "high", "medium", "low", "info"]
        return {sev: grouped.get(sev, []) for sev in severity_order}
    
    def _group_by_scanner(self, results: List[ScanResult]) -> Dict[str, List[ScanResult]]:
        """Группирует результаты по сканнеру."""
        grouped = {}
        for result in results:
            scanner = result.scanner_name
            if scanner not in grouped:
                grouped[scanner] = []
            grouped[scanner].append(result)
        return grouped
    
    def _group_by_file(self, results: List[ScanResult]) -> Dict[str, List[ScanResult]]:
        """Группирует результаты по файлу."""
        grouped = {}
        for result in results:
            file_path = result.file_path or "unknown"
            if file_path not in grouped:
                grouped[file_path] = []
            grouped[file_path].append(result)
        return grouped
    
    def _severity_to_color(self, severity: str) -> str:
        """Конвертирует уровень критичности в цвет."""
        colors = {
            "critical": "#dc3545",
            "high": "#fd7e14",
            "medium": "#ffc107",
            "low": "#28a745",
            "info": "#17a2b8"
        }
        return colors.get(severity.lower(), "#6c757d")
    
    def _severity_to_icon(self, severity: str) -> str:
        """Конвертирует уровень критичности в иконку."""
        icons = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢",
            "info": "🔵"
        }
        return icons.get(severity.lower(), "⚪")
    
    def _get_default_html_template(self) -> Template:
        """Возвращает встроенный HTML шаблон."""
        template_content = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Отчёт PySecKit</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; border-bottom: 2px solid #007bff; padding-bottom: 20px; margin-bottom: 30px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .summary-card { background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #007bff; }
        .severity-critical { border-left-color: #dc3545; }
        .severity-high { border-left-color: #fd7e14; }
        .severity-medium { border-left-color: #ffc107; }
        .severity-low { border-left-color: #28a745; }
        .severity-info { border-left-color: #17a2b8; }
        .results-table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        .results-table th, .results-table td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        .results-table th { background-color: #007bff; color: white; }
        .results-table tr:hover { background-color: #f5f5f5; }
        .severity-badge { padding: 4px 8px; border-radius: 4px; color: white; font-size: 12px; font-weight: bold; }
        .file-path { color: #6c757d; font-family: monospace; font-size: 12px; }
        .description { max-width: 400px; overflow: hidden; text-overflow: ellipsis; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ Отчёт PySecKit</h1>
            <p>Сгенерирован: {{ metadata.generated_at }}</p>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <h3>Всего проблем</h3>
                <h2>{{ summary.total_issues }}</h2>
            </div>
            
            {% for severity, count in summary.by_severity.items() %}
            <div class="summary-card severity-{{ severity }}">
                <h3>{{ severity | title }}</h3>
                <h2>{{ count }}</h2>
            </div>
            {% endfor %}
        </div>
        
        {% if results %}
        <h2>Детальные результаты</h2>
        <table class="results-table">
            <thead>
                <tr>
                    <th>Критичность</th>
                    <th>Название</th>
                    <th>Файл</th>
                    <th>Строка</th>
                    <th>Сканнер</th>
                    <th>Описание</th>
                </tr>
            </thead>
            <tbody>
                {% for result in results %}
                <tr>
                    <td>
                        <span class="severity-badge" style="background-color: {{ result.severity.value | severity_color }}">
                            {{ result.severity.value | upper }}
                        </span>
                    </td>
                    <td><strong>{{ result.title }}</strong></td>
                    <td class="file-path">{{ result.file_path or 'N/A' }}</td>
                    <td>{{ result.line_number or 'N/A' }}</td>
                    <td>{{ result.scanner_name }}</td>
                    <td class="description">{{ result.description }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% endif %}
    </div>
</body>
</html>
        """
        return Template(template_content) 