"""
Генератор моделей угроз.
"""

import json
import yaml
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Asset:
    """Представляет актив системы."""
    name: str
    type: str
    description: str
    file_path: Optional[str] = None
    sensitive_data: bool = False
    external_access: bool = False


@dataclass
class Threat:
    """Представляет угрозу безопасности."""
    id: str
    category: str  # STRIDE категория
    title: str
    description: str
    impact: str
    likelihood: str
    risk_level: str
    mitigation: str
    affected_assets: List[str]


class ThreatModelGenerator:
    """Генератор автоматических моделей угроз."""
    
    def generate_from_code(self, project_path: Union[str, Path]) -> "ThreatModel":
        """Генерирует модель угроз из кода проекта."""
        # Заглушка - в реальной реализации здесь будет анализ кода и генерация модели
        return ThreatModel()


class AdvancedThreatModelGenerator:
    """Продвинутый генератор моделей угроз с поддержкой STRIDE."""
    
    def __init__(self):
        self.stride_categories = {
            'Spoofing': 'Подмена личности',
            'Tampering': 'Несанкционированное изменение',
            'Repudiation': 'Отказ от совершённых действий',
            'Information Disclosure': 'Раскрытие информации',
            'Denial of Service': 'Отказ в обслуживании',
            'Elevation of Privilege': 'Повышение привилегий'
        }
        
        # Паттерны для обнаружения активов
        self.asset_patterns = {
            'database': [r'\.db', r'database', r'sql', r'mysql', r'postgres', r'mongodb'],
            'api_endpoint': [r'@app\.route', r'@api\.', r'FastAPI', r'flask', r'django'],
            'authentication': [r'login', r'auth', r'password', r'token', r'jwt'],
            'file_storage': [r'upload', r'download', r'file', r'storage'],
            'configuration': [r'config', r'settings', r'\.env', r'\.ini', r'\.yaml', r'\.json'],
            'external_service': [r'requests\.', r'http', r'api_key', r'webhook'],
        }
    
    def analyze_codebase(self, project_path: str) -> List[Asset]:
        """Анализирует кодовую базу и извлекает активы."""
        assets = []
        project_path = Path(project_path)
        
        # Сканируем файлы проекта
        for file_path in project_path.rglob('*.py'):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                # Анализируем содержимое файла
                file_assets = self._analyze_file_content(str(file_path), content)
                assets.extend(file_assets)
                
            except Exception as e:
                print(f"Ошибка при анализе файла {file_path}: {e}")
                continue
        
        return assets
    
    def _analyze_file_content(self, file_path: str, content: str) -> List[Asset]:
        """Анализирует содержимое файла и извлекает активы."""
        assets = []
        
        for asset_type, patterns in self.asset_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    asset = Asset(
                        name=f"{asset_type}_{Path(file_path).stem}",
                        type=asset_type,
                        description=f"{asset_type.replace('_', ' ').title()} в файле {Path(file_path).name}",
                        file_path=file_path,
                        sensitive_data=asset_type in ['database', 'authentication', 'configuration'],
                        external_access=asset_type in ['api_endpoint', 'external_service']
                    )
                    assets.append(asset)
                    break  # Не дублируем активы одного типа для одного файла
        
        return assets
    
    def generate_threats_for_asset(self, asset: Asset) -> List[Threat]:
        """Генерирует угрозы для конкретного актива по модели STRIDE."""
        threats = []
        
        # Генерируем угрозы в зависимости от типа актива
        if asset.type == 'database':
            threats.extend(self._generate_database_threats(asset))
        elif asset.type == 'api_endpoint':
            threats.extend(self._generate_api_threats(asset))
        elif asset.type == 'authentication':
            threats.extend(self._generate_auth_threats(asset))
        elif asset.type == 'file_storage':
            threats.extend(self._generate_file_threats(asset))
        elif asset.type == 'configuration':
            threats.extend(self._generate_config_threats(asset))
        elif asset.type == 'external_service':
            threats.extend(self._generate_external_threats(asset))
        
        return threats
    
    def _generate_database_threats(self, asset: Asset) -> List[Threat]:
        """Генерирует угрозы для баз данных."""
        return [
            Threat(
                id=f"DB_001_{asset.name}",
                category="Information Disclosure",
                title="Несанкционированный доступ к данным",
                description="Злоумышленник может получить доступ к конфиденциальным данным в БД",
                impact="Высокий",
                likelihood="Средний",
                risk_level="Высокий",
                mitigation="Использовать шифрование данных, контроль доступа, аудит",
                affected_assets=[asset.name]
            ),
            Threat(
                id=f"DB_002_{asset.name}",
                category="Tampering",
                title="SQL-инъекции",
                description="Возможность выполнения произвольных SQL-запросов",
                impact="Критический",
                likelihood="Высокий",
                risk_level="Критический",
                mitigation="Использовать параметризованные запросы, валидацию входных данных",
                affected_assets=[asset.name]
            )
        ]
    
    def _generate_api_threats(self, asset: Asset) -> List[Threat]:
        """Генерирует угрозы для API endpoints."""
        return [
            Threat(
                id=f"API_001_{asset.name}",
                category="Spoofing",
                title="Подделка запросов к API",
                description="Злоумышленник может отправлять поддельные запросы от имени пользователя",
                impact="Высокий",
                likelihood="Средний",
                risk_level="Высокий",
                mitigation="Реализовать строгую аутентификацию и авторизацию",
                affected_assets=[asset.name]
            ),
            Threat(
                id=f"API_002_{asset.name}",
                category="Denial of Service",
                title="DDoS атаки на API",
                description="Перегрузка API большим количеством запросов",
                impact="Средний",
                likelihood="Высокий",
                risk_level="Высокий",
                mitigation="Реализовать rate limiting, мониторинг, балансировку нагрузки",
                affected_assets=[asset.name]
            )
        ]
    
    def _generate_auth_threats(self, asset: Asset) -> List[Threat]:
        """Генерирует угрозы для системы аутентификации."""
        return [
            Threat(
                id=f"AUTH_001_{asset.name}",
                category="Elevation of Privilege",
                title="Повышение привилегий",
                description="Пользователь может получить права администратора",
                impact="Критический",
                likelihood="Низкий",
                risk_level="Высокий",
                mitigation="Принцип минимальных привилегий, регулярный аудит прав",
                affected_assets=[asset.name]
            ),
            Threat(
                id=f"AUTH_002_{asset.name}",
                category="Spoofing",
                title="Брутфорс атаки",
                description="Подбор паролей методом перебора",
                impact="Высокий",
                likelihood="Высокий",
                risk_level="Высокий",
                mitigation="Блокировка после неудачных попыток, сильные пароли, 2FA",
                affected_assets=[asset.name]
            )
        ]
    
    def _generate_file_threats(self, asset: Asset) -> List[Threat]:
        """Генерирует угрозы для файлового хранилища."""
        return [
            Threat(
                id=f"FILE_001_{asset.name}",
                category="Tampering",
                title="Загрузка вредоносных файлов",
                description="Загрузка файлов с вредоносным кодом",
                impact="Высокий",
                likelihood="Средний",
                risk_level="Высокий",
                mitigation="Валидация типов файлов, антивирусное сканирование",
                affected_assets=[asset.name]
            )
        ]
    
    def _generate_config_threats(self, asset: Asset) -> List[Threat]:
        """Генерирует угрозы для конфигурационных файлов."""
        return [
            Threat(
                id=f"CONFIG_001_{asset.name}",
                category="Information Disclosure",
                title="Утечка конфигурационных данных",
                description="Раскрытие секретных ключей и паролей из конфигурации",
                impact="Критический",
                likelihood="Средний",
                risk_level="Критический",
                mitigation="Использовать переменные окружения, шифрование конфигурации",
                affected_assets=[asset.name]
            )
        ]
    
    def _generate_external_threats(self, asset: Asset) -> List[Threat]:
        """Генерирует угрозы для внешних сервисов."""
        return [
            Threat(
                id=f"EXT_001_{asset.name}",
                category="Tampering",
                title="Man-in-the-middle атаки",
                description="Перехват и изменение данных при взаимодействии с внешними сервисами",
                impact="Высокий",
                likelihood="Низкий",
                risk_level="Средний",
                mitigation="Использовать HTTPS, проверку сертификатов, pinning",
                affected_assets=[asset.name]
            )
        ]
    
    def generate_comprehensive_model(self, project_path: str) -> Dict[str, Any]:
        """Генерирует комплексную модель угроз для проекта."""
        # Анализируем активы
        assets = self.analyze_codebase(project_path)
        
        # Генерируем угрозы для всех активов
        all_threats = []
        for asset in assets:
            threats = self.generate_threats_for_asset(asset)
            all_threats.extend(threats)
        
        # Создаём комплексную модель
        threat_model = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'project_path': project_path,
                'total_assets': len(assets),
                'total_threats': len(all_threats)
            },
            'assets': [
                {
                    'name': asset.name,
                    'type': asset.type,
                    'description': asset.description,
                    'file_path': asset.file_path,
                    'sensitive_data': asset.sensitive_data,
                    'external_access': asset.external_access
                }
                for asset in assets
            ],
            'threats': [
                {
                    'id': threat.id,
                    'category': threat.category,
                    'title': threat.title,
                    'description': threat.description,
                    'impact': threat.impact,
                    'likelihood': threat.likelihood,
                    'risk_level': threat.risk_level,
                    'mitigation': threat.mitigation,
                    'affected_assets': threat.affected_assets
                }
                for threat in all_threats
            ],
            'summary': {
                'by_category': self._summarize_by_category(all_threats),
                'by_risk_level': self._summarize_by_risk_level(all_threats),
                'top_risks': self._get_top_risks(all_threats)
            }
        }
        
        return threat_model
    
    def _summarize_by_category(self, threats: List[Threat]) -> Dict[str, int]:
        """Группирует угрозы по STRIDE категориям."""
        summary = {}
        for threat in threats:
            category = threat.category
            summary[category] = summary.get(category, 0) + 1
        return summary
    
    def _summarize_by_risk_level(self, threats: List[Threat]) -> Dict[str, int]:
        """Группирует угрозы по уровню риска."""
        summary = {}
        for threat in threats:
            risk_level = threat.risk_level
            summary[risk_level] = summary.get(risk_level, 0) + 1
        return summary
    
    def _get_top_risks(self, threats: List[Threat], limit: int = 5) -> List[Dict[str, str]]:
        """Возвращает топ угроз по уровню риска."""
        # Сортируем по критичности
        risk_order = {'Критический': 4, 'Высокий': 3, 'Средний': 2, 'Низкий': 1}
        
        sorted_threats = sorted(
            threats,
            key=lambda t: risk_order.get(t.risk_level, 0),
            reverse=True
        )
        
        return [
            {
                'id': threat.id,
                'title': threat.title,
                'risk_level': threat.risk_level,
                'category': threat.category
            }
            for threat in sorted_threats[:limit]
        ]
    
    def export_to_json(self, threat_model: Dict[str, Any], output_path: str) -> None:
        """Экспортирует модель угроз в JSON."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(threat_model, f, ensure_ascii=False, indent=2)
    
    def export_to_yaml(self, threat_model: Dict[str, Any], output_path: str) -> None:
        """Экспортирует модель угроз в YAML."""
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(threat_model, f, default_flow_style=False, allow_unicode=True)


class ThreatModel:
    """Модель угроз."""
    
    def export_dfd(self, output_path: Union[str, Path]) -> None:
        """Экспортирует диаграмму потоков данных в PlantUML."""
        # Заглушка
        pass 