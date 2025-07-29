"""
Интеграция с Elasticsearch для централизованного хранения результатов сканирования.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from pyseckit.core.scanner import ScanResult


class ElasticsearchIntegration:
    """Интеграция с Elasticsearch для хранения результатов сканирования."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = None
        self.index_prefix = config.get('index_prefix', 'pyseckit')
        self.enabled = config.get('enabled', False)
        
        if self.enabled:
            self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Инициализирует клиент Elasticsearch."""
        try:
            from elasticsearch import Elasticsearch
            
            hosts = self.config.get('hosts', ['localhost:9200'])
            username = self.config.get('username')
            password = self.config.get('password')
            use_ssl = self.config.get('ssl', False)
            verify_certs = self.config.get('verify_certs', True)
            ca_certs = self.config.get('ca_certs')
            
            auth = None
            if username and password:
                auth = (username, password)
            
            self.client = Elasticsearch(
                hosts=hosts,
                http_auth=auth,
                use_ssl=use_ssl,
                verify_certs=verify_certs,
                ca_certs=ca_certs,
                timeout=30,
                max_retries=3,
                retry_on_timeout=True
            )
            
            # Проверяем подключение
            if not self.client.ping():
                raise ConnectionError("Не удалось подключиться к Elasticsearch")
                
        except ImportError:
            raise ImportError("Установите elasticsearch: pip install elasticsearch>=8.0.0")
    
    def index_scan_result(self, scan_result: ScanResult) -> bool:
        """Индексирует результат сканирования в Elasticsearch."""
        if not self.enabled or not self.client:
            return False
        
        try:
            # Создаем индекс если не существует
            index_name = f"{self.index_prefix}-scans-{datetime.now().strftime('%Y-%m')}"
            self._ensure_index_exists(index_name)
            
            # Подготавливаем документ
            doc = self._prepare_scan_document(scan_result)
            
            # Индексируем
            response = self.client.index(
                index=index_name,
                id=str(uuid.uuid4()),
                body=doc
            )
            
            return response.get('result') == 'created'
            
        except Exception as e:
            print(f"Ошибка при индексации результата сканирования: {e}")
            return False
    
    def index_findings(self, scan_result: ScanResult) -> bool:
        """Индексирует отдельные находки в Elasticsearch."""
        if not self.enabled or not self.client:
            return False
        
        try:
            index_name = f"{self.index_prefix}-findings-{datetime.now().strftime('%Y-%m')}"
            self._ensure_index_exists(index_name, mapping_type='finding')
            
            success_count = 0
            for finding in scan_result.findings:
                doc = self._prepare_finding_document(scan_result, finding)
                
                response = self.client.index(
                    index=index_name,
                    id=str(uuid.uuid4()),
                    body=doc
                )
                
                if response.get('result') == 'created':
                    success_count += 1
            
            return success_count == len(scan_result.findings)
            
        except Exception as e:
            print(f"Ошибка при индексации находок: {e}")
            return False
    
    def search_findings(self, query: Dict[str, Any], size: int = 100) -> List[Dict[str, Any]]:
        """Ищет находки в Elasticsearch."""
        if not self.enabled or not self.client:
            return []
        
        try:
            index_pattern = f"{self.index_prefix}-findings-*"
            
            response = self.client.search(
                index=index_pattern,
                body={"query": query, "size": size},
                sort=[{"@timestamp": {"order": "desc"}}]
            )
            
            return [hit['_source'] for hit in response['hits']['hits']]
            
        except Exception as e:
            print(f"Ошибка при поиске находок: {e}")
            return []
    
    def get_scan_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Получает статистику сканирований за период."""
        if not self.enabled or not self.client:
            return {}
        
        try:
            from_date = datetime.now().replace(hour=0, minute=0, second=0)
            from_date = from_date.replace(day=from_date.day - days)
            
            query = {
                "bool": {
                    "filter": [
                        {
                            "range": {
                                "@timestamp": {
                                    "gte": from_date.isoformat()
                                }
                            }
                        }
                    ]
                }
            }
            
            # Статистика по сканированиям
            scan_stats = self.client.search(
                index=f"{self.index_prefix}-scans-*",
                body={
                    "query": query,
                    "aggs": {
                        "scanner_types": {
                            "terms": {"field": "scanner_name.keyword"}
                        },
                        "daily_scans": {
                            "date_histogram": {
                                "field": "@timestamp",
                                "calendar_interval": "day"
                            }
                        }
                    },
                    "size": 0
                }
            )
            
            # Статистика по находкам
            finding_stats = self.client.search(
                index=f"{self.index_prefix}-findings-*",
                body={
                    "query": query,
                    "aggs": {
                        "severity_distribution": {
                            "terms": {"field": "severity.keyword"}
                        },
                        "top_rules": {
                            "terms": {"field": "rule_id.keyword", "size": 10}
                        }
                    },
                    "size": 0
                }
            )
            
            return {
                "scan_statistics": scan_stats.get('aggregations', {}),
                "finding_statistics": finding_stats.get('aggregations', {}),
                "total_scans": scan_stats['hits']['total']['value'],
                "total_findings": finding_stats['hits']['total']['value']
            }
            
        except Exception as e:
            print(f"Ошибка при получении статистики: {e}")
            return {}
    
    def _ensure_index_exists(self, index_name: str, mapping_type: str = 'scan') -> None:
        """Создает индекс если не существует."""
        if self.client.indices.exists(index=index_name):
            return
        
        if mapping_type == 'scan':
            mapping = self._get_scan_mapping()
        else:
            mapping = self._get_finding_mapping()
        
        self.client.indices.create(
            index=index_name,
            body={
                "mappings": mapping,
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 1
                }
            }
        )
    
    def _get_scan_mapping(self) -> Dict[str, Any]:
        """Возвращает маппинг для индекса сканирований."""
        return {
            "properties": {
                "@timestamp": {"type": "date"},
                "scan_id": {"type": "keyword"},
                "scanner_name": {"type": "keyword"},
                "target": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                "start_time": {"type": "date"},
                "end_time": {"type": "date"},
                "duration_seconds": {"type": "float"},
                "total_findings": {"type": "integer"},
                "findings_by_severity": {
                    "properties": {
                        "HIGH": {"type": "integer"},
                        "MEDIUM": {"type": "integer"},
                        "LOW": {"type": "integer"},
                        "INFO": {"type": "integer"}
                    }
                },
                "metadata": {"type": "object", "enabled": False}
            }
        }
    
    def _get_finding_mapping(self) -> Dict[str, Any]:
        """Возвращает маппинг для индекса находок."""
        return {
            "properties": {
                "@timestamp": {"type": "date"},
                "scan_id": {"type": "keyword"},
                "scanner_name": {"type": "keyword"},
                "target": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                "severity": {"type": "keyword"},
                "confidence": {"type": "keyword"},
                "title": {"type": "text"},
                "description": {"type": "text"},
                "file": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                "line": {"type": "integer"},
                "column": {"type": "integer"},
                "rule_id": {"type": "keyword"},
                "cwe": {"type": "keyword"},
                "owasp": {"type": "keyword"},
                "cvss_score": {"type": "float"},
                "references": {"type": "text"}
            }
        }
    
    def _prepare_scan_document(self, scan_result: ScanResult) -> Dict[str, Any]:
        """Подготавливает документ сканирования."""
        duration = (scan_result.end_time - scan_result.start_time).total_seconds()
        
        # Группируем находки по severity
        severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
        for finding in scan_result.findings:
            severity = finding.get('severity', 'INFO')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            "@timestamp": datetime.now().isoformat(),
            "scan_id": str(uuid.uuid4()),
            "scanner_name": scan_result.scanner_name,
            "target": scan_result.target,
            "start_time": scan_result.start_time.isoformat(),
            "end_time": scan_result.end_time.isoformat(),
            "duration_seconds": duration,
            "total_findings": len(scan_result.findings),
            "findings_by_severity": severity_counts,
            "metadata": scan_result.metadata or {}
        }
    
    def _prepare_finding_document(self, scan_result: ScanResult, finding: Dict[str, Any]) -> Dict[str, Any]:
        """Подготавливает документ находки."""
        return {
            "@timestamp": datetime.now().isoformat(),
            "scan_id": getattr(scan_result, 'scan_id', str(uuid.uuid4())),
            "scanner_name": scan_result.scanner_name,
            "target": scan_result.target,
            "severity": finding.get('severity', 'INFO'),
            "confidence": finding.get('confidence', 'MEDIUM'),
            "title": finding.get('title', ''),
            "description": finding.get('description', ''),
            "file": finding.get('file', ''),
            "line": finding.get('line', 0),
            "column": finding.get('column', 0),
            "rule_id": finding.get('rule_id', ''),
            "cwe": finding.get('cwe', ''),
            "owasp": finding.get('owasp', ''),
            "cvss_score": finding.get('cvss_score', 0.0),
            "references": finding.get('references', [])
        }
    
    def create_kibana_dashboards(self) -> bool:
        """Создает базовые дашборды в Kibana."""
        if not self.enabled or not self.client:
            return False
        
        try:
            # Это упрощенная реализация
            # В реальном проекте нужно использовать Kibana API
            dashboard_config = {
                "version": "8.0.0",
                "objects": [
                    {
                        "id": "pyseckit-overview",
                        "type": "dashboard",
                        "attributes": {
                            "title": "PySecKit Security Overview",
                            "description": "Обзор результатов сканирования безопасности"
                        }
                    }
                ]
            }
            
            print("Для создания дашбордов Kibana используйте Kibana API или импортируйте конфигурацию вручную")
            return True
            
        except Exception as e:
            print(f"Ошибка при создании дашбордов Kibana: {e}")
            return False 