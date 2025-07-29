"""
Расширенная система генерации моделей угроз.
"""

import json
import yaml
import os
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum


class ThreatCategory(Enum):
    """Категории угроз по STRIDE."""
    SPOOFING = "Spoofing"
    TAMPERING = "Tampering"  
    REPUDIATION = "Repudiation"
    INFORMATION_DISCLOSURE = "Information Disclosure"
    DENIAL_OF_SERVICE = "Denial of Service"
    ELEVATION_OF_PRIVILEGE = "Elevation of Privilege"


class AssetType(Enum):
    """Типы активов системы."""
    WEB_APPLICATION = "Web Application"
    DATABASE = "Database"
    API = "API"
    MICROSERVICE = "Microservice"
    EXTERNAL_SERVICE = "External Service"
    USER_INTERFACE = "User Interface"
    FILE_SYSTEM = "File System"
    NETWORK = "Network"
    CLOUD_STORAGE = "Cloud Storage"


@dataclass
class Asset:
    """Актив системы."""
    id: str
    name: str
    type: AssetType
    description: str
    trust_boundary: str
    data_classification: str  # PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED
    technologies: List[str]
    connections: List[str]  # IDs других активов
    attributes: Dict[str, Any]


@dataclass
class DataFlow:
    """Поток данных между активами."""
    id: str
    name: str
    source: str  # Asset ID
    destination: str  # Asset ID
    protocol: str
    port: Optional[int]
    data_type: str
    encryption: bool
    authentication_required: bool
    authorization_mechanism: str


@dataclass
class Threat:
    """Модель угрозы."""
    id: str
    title: str
    description: str
    category: ThreatCategory
    affected_assets: List[str]
    attack_vector: str
    impact: str  # HIGH, MEDIUM, LOW
    likelihood: str  # HIGH, MEDIUM, LOW
    risk_rating: str  # CRITICAL, HIGH, MEDIUM, LOW
    mitigation_strategies: List[str]
    detection_methods: List[str]
    cwe_mapping: List[str]
    owasp_mapping: List[str]


@dataclass
class ThreatModel:
    """Полная модель угроз."""
    id: str
    name: str
    description: str
    scope: str
    assets: List[Asset]
    data_flows: List[DataFlow]
    threats: List[Threat]
    assumptions: List[str]
    out_of_scope: List[str]
    created_at: datetime
    updated_at: datetime
    version: str


class AdvancedThreatModelGenerator:
    """Расширенный генератор моделей угроз."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.threat_knowledge_base = self._load_threat_knowledge_base()
        self.technology_mappings = self._load_technology_mappings()
    
    def analyze_codebase(self, target_path: str) -> ThreatModel:
        """Анализирует кодовую базу и создает модель угроз."""
        # Анализируем структуру проекта
        project_analysis = self._analyze_project_structure(target_path)
        
        # Идентифицируем активы
        assets = self._identify_assets(project_analysis)
        
        # Анализируем потоки данных
        data_flows = self._analyze_data_flows(project_analysis, assets)
        
        # Генерируем угрозы
        threats = self._generate_threats(assets, data_flows)
        
        # Создаем модель угроз
        threat_model = ThreatModel(
            id=f"tm-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            name=f"Threat Model for {project_analysis['project_name']}",
            description=f"Автоматически сгенерированная модель угроз для проекта {project_analysis['project_name']}",
            scope=target_path,
            assets=assets,
            data_flows=data_flows,
            threats=threats,
            assumptions=self._generate_assumptions(project_analysis),
            out_of_scope=self._generate_out_of_scope(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            version="1.0"
        )
        
        return threat_model
    
    def _analyze_project_structure(self, target_path: str) -> Dict[str, Any]:
        """Анализирует структуру проекта."""
        analysis = {
            "project_name": os.path.basename(target_path),
            "technologies": set(),
            "frameworks": set(),
            "databases": set(),
            "apis": [],
            "external_services": set(),
            "file_types": {},
            "security_features": set(),
            "deployment_configs": []
        }
        
        # Анализируем файлы
        for root, dirs, files in os.walk(target_path):
            for file in files:
                file_path = os.path.join(root, file)
                self._analyze_file(file_path, analysis)
        
        return analysis
    
    def _analyze_file(self, file_path: str, analysis: Dict[str, Any]) -> None:
        """Анализирует отдельный файл."""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Подсчитываем типы файлов
        analysis["file_types"][file_ext] = analysis["file_types"].get(file_ext, 0) + 1
        
        # Определяем технологии по расширениям
        tech_mapping = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.cs': 'C#',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.go': 'Go',
            '.rs': 'Rust',
            '.cpp': 'C++',
            '.c': 'C'
        }
        
        if file_ext in tech_mapping:
            analysis["technologies"].add(tech_mapping[file_ext])
        
        # Анализируем содержимое для специфических файлов
        if file_ext in ['.py', '.js', '.ts', '.java', '.php']:
            self._analyze_source_file(file_path, analysis)
        elif file_path.endswith(('requirements.txt', 'package.json', 'pom.xml', 'Gemfile')):
            self._analyze_dependency_file(file_path, analysis)
        elif file_path.endswith(('docker-compose.yml', 'Dockerfile', 'k8s.yaml')):
            analysis["deployment_configs"].append(file_path)
    
    def _analyze_source_file(self, file_path: str, analysis: Dict[str, Any]) -> None:
        """Анализирует исходный код."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Ищем фреймворки и библиотеки
            framework_patterns = {
                'Django': r'from django|import django',
                'Flask': r'from flask|import flask',
                'FastAPI': r'from fastapi|import fastapi',
                'Express': r'express\(',
                'React': r'from react|import react',
                'Angular': r'@angular/',
                'Vue': r'from vue|import vue',
                'Spring': r'@SpringBootApplication|import org.springframework'
            }
            
            for framework, pattern in framework_patterns.items():
                if re.search(pattern, content, re.IGNORECASE):
                    analysis["frameworks"].add(framework)
            
            # Ищем базы данных
            db_patterns = {
                'PostgreSQL': r'postgresql://|psycopg2|pg_',
                'MySQL': r'mysql://|pymysql|mysql\.connector',
                'MongoDB': r'mongodb://|pymongo|mongoose',
                'Redis': r'redis://|import redis',
                'SQLite': r'sqlite3|sqlite://',
                'Oracle': r'oracle://|cx_Oracle',
                'SQL Server': r'sqlserver://|pyodbc'
            }
            
            for db, pattern in db_patterns.items():
                if re.search(pattern, content, re.IGNORECASE):
                    analysis["databases"].add(db)
            
            # Ищем внешние сервисы
            external_patterns = {
                'AWS': r'aws\.|boto3|amazon',
                'Google Cloud': r'google\.cloud|gcp',
                'Azure': r'azure\.|microsoft',
                'Stripe': r'stripe\.|stripe_',
                'PayPal': r'paypal|braintree',
                'SendGrid': r'sendgrid',
                'Twilio': r'twilio'
            }
            
            for service, pattern in external_patterns.items():
                if re.search(pattern, content, re.IGNORECASE):
                    analysis["external_services"].add(service)
            
            # Ищем функции безопасности
            security_patterns = {
                'Authentication': r'authenticate|login|signin|jwt|oauth',
                'Authorization': r'authorize|permission|role|@login_required',
                'Encryption': r'encrypt|decrypt|crypto|bcrypt|hashlib',
                'Input Validation': r'validate|sanitize|escape|clean',
                'CSRF Protection': r'csrf|@csrf_exempt',
                'XSS Protection': r'xss|escape_html|bleach',
                'SQL Injection Protection': r'parameterized|prepared.*statement'
            }
            
            for security_feature, pattern in security_patterns.items():
                if re.search(pattern, content, re.IGNORECASE):
                    analysis["security_features"].add(security_feature)
            
            # Ищем API endpoints
            api_patterns = [
                r'@app\.route\(["\']([^"\']+)',
                r'@get\(["\']([^"\']+)',
                r'@post\(["\']([^"\']+)',
                r'app\.get\(["\']([^"\']+)',
                r'app\.post\(["\']([^"\']+)',
                r'router\.get\(["\']([^"\']+)',
                r'@RequestMapping.*value.*=.*["\']([^"\']+)'
            ]
            
            for pattern in api_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                analysis["apis"].extend(matches)
        
        except Exception:
            pass
    
    def _analyze_dependency_file(self, file_path: str, analysis: Dict[str, Any]) -> None:
        """Анализирует файлы зависимостей."""
        try:
            if file_path.endswith('requirements.txt'):
                with open(file_path, 'r') as f:
                    for line in f:
                        if '==' in line:
                            package = line.split('==')[0].strip()
                            if package in ['django', 'flask', 'fastapi']:
                                analysis["frameworks"].add(package.capitalize())
            
            elif file_path.endswith('package.json'):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    dependencies = list(data.get('dependencies', {}).keys())
                    dev_dependencies = list(data.get('devDependencies', {}).keys())
                    
                    all_deps = dependencies + dev_dependencies
                    
                    framework_mapping = {
                        'express': 'Express',
                        'react': 'React',
                        'angular': 'Angular',
                        'vue': 'Vue'
                    }
                    
                    for dep in all_deps:
                        if dep in framework_mapping:
                            analysis["frameworks"].add(framework_mapping[dep])
        
        except Exception:
            pass
    
    def _identify_assets(self, project_analysis: Dict[str, Any]) -> List[Asset]:
        """Идентифицирует активы на основе анализа проекта."""
        assets = []
        asset_id_counter = 1
        
        # Основное веб-приложение
        if any(fw in project_analysis["frameworks"] for fw in ['Django', 'Flask', 'FastAPI', 'Express', 'React', 'Angular', 'Vue']):
            assets.append(Asset(
                id=f"asset-{asset_id_counter}",
                name="Main Web Application",
                type=AssetType.WEB_APPLICATION,
                description=f"Основное веб-приложение на базе {', '.join(project_analysis['frameworks'])}",
                trust_boundary="Internal",
                data_classification="INTERNAL",
                technologies=list(project_analysis["technologies"]),
                connections=[],
                attributes={
                    "frameworks": list(project_analysis["frameworks"]),
                    "apis": project_analysis["apis"][:10]  # Первые 10 API
                }
            ))
            asset_id_counter += 1
        
        # Базы данных
        for db in project_analysis["databases"]:
            assets.append(Asset(
                id=f"asset-{asset_id_counter}",
                name=f"{db} Database",
                type=AssetType.DATABASE,
                description=f"База данных {db}",
                trust_boundary="Internal",
                data_classification="CONFIDENTIAL",
                technologies=[db],
                connections=[],
                attributes={"database_type": db}
            ))
            asset_id_counter += 1
        
        # Внешние сервисы
        for service in project_analysis["external_services"]:
            assets.append(Asset(
                id=f"asset-{asset_id_counter}",
                name=f"{service} Integration",
                type=AssetType.EXTERNAL_SERVICE,
                description=f"Интеграция с внешним сервисом {service}",
                trust_boundary="External",
                data_classification="PUBLIC",
                technologies=[service],
                connections=[],
                attributes={"service_provider": service}
            ))
            asset_id_counter += 1
        
        return assets
    
    def _analyze_data_flows(self, project_analysis: Dict[str, Any], assets: List[Asset]) -> List[DataFlow]:
        """Анализирует потоки данных между активами."""
        data_flows = []
        flow_id_counter = 1
        
        # Находим веб-приложение и базы данных
        web_app = next((a for a in assets if a.type == AssetType.WEB_APPLICATION), None)
        databases = [a for a in assets if a.type == AssetType.DATABASE]
        external_services = [a for a in assets if a.type == AssetType.EXTERNAL_SERVICE]
        
        # Потоки от веб-приложения к базам данных
        if web_app:
            for db in databases:
                data_flows.append(DataFlow(
                    id=f"flow-{flow_id_counter}",
                    name=f"Web App to {db.name}",
                    source=web_app.id,
                    destination=db.id,
                    protocol="TCP",
                    port=self._get_default_db_port(db.name),
                    data_type="Database queries and user data",
                    encryption=False,
                    authentication_required=True,
                    authorization_mechanism="Database credentials"
                ))
                flow_id_counter += 1
            
            # Потоки к внешним сервисам
            for service in external_services:
                data_flows.append(DataFlow(
                    id=f"flow-{flow_id_counter}",
                    name=f"Web App to {service.name}",
                    source=web_app.id,
                    destination=service.id,
                    protocol="HTTPS",
                    port=443,
                    data_type="API requests and user data",
                    encryption=True,
                    authentication_required=True,
                    authorization_mechanism="API Keys/OAuth"
                ))
                flow_id_counter += 1
        
        return data_flows
    
    def _generate_threats(self, assets: List[Asset], data_flows: List[DataFlow]) -> List[Threat]:
        """Генерирует угрозы на основе активов и потоков данных."""
        threats = []
        threat_id_counter = 1
        
        # Угрозы для веб-приложений
        web_apps = [a for a in assets if a.type == AssetType.WEB_APPLICATION]
        for web_app in web_apps:
            owasp_threats = [
                {
                    "title": "SQL Injection",
                    "description": "Возможность выполнения произвольных SQL запросов через уязвимые входные параметры",
                    "category": ThreatCategory.TAMPERING,
                    "attack_vector": "Вредоносные SQL команды в пользовательском вводе",
                    "impact": "HIGH",
                    "likelihood": "MEDIUM",
                    "cwe": ["CWE-89"],
                    "owasp": ["A03:2021"]
                },
                {
                    "title": "Cross-Site Scripting (XSS)",
                    "description": "Выполнение вредоносного JavaScript кода в браузере пользователя",
                    "category": ThreatCategory.TAMPERING,
                    "attack_vector": "Вредоносные скрипты в пользовательском контенте",
                    "impact": "MEDIUM",
                    "likelihood": "HIGH",
                    "cwe": ["CWE-79"],
                    "owasp": ["A03:2021"]
                }
            ]
            
            for threat_data in owasp_threats:
                threats.append(Threat(
                    id=f"threat-{threat_id_counter}",
                    title=threat_data["title"],
                    description=threat_data["description"],
                    category=threat_data["category"],
                    affected_assets=[web_app.id],
                    attack_vector=threat_data["attack_vector"],
                    impact=threat_data["impact"],
                    likelihood=threat_data["likelihood"],
                    risk_rating=self._calculate_risk_rating(threat_data["impact"], threat_data["likelihood"]),
                    mitigation_strategies=self._get_mitigation_strategies(threat_data["title"]),
                    detection_methods=self._get_detection_methods(threat_data["title"]),
                    cwe_mapping=threat_data["cwe"],
                    owasp_mapping=threat_data["owasp"]
                ))
                threat_id_counter += 1
        
        return threats
    
    def _calculate_risk_rating(self, impact: str, likelihood: str) -> str:
        """Вычисляет рейтинг риска."""
        risk_matrix = {
            ("HIGH", "HIGH"): "CRITICAL",
            ("HIGH", "MEDIUM"): "HIGH",
            ("HIGH", "LOW"): "MEDIUM",
            ("MEDIUM", "HIGH"): "HIGH",
            ("MEDIUM", "MEDIUM"): "MEDIUM",
            ("MEDIUM", "LOW"): "LOW",
            ("LOW", "HIGH"): "MEDIUM",
            ("LOW", "MEDIUM"): "LOW",
            ("LOW", "LOW"): "LOW"
        }
        
        return risk_matrix.get((impact, likelihood), "MEDIUM")
    
    def _get_mitigation_strategies(self, threat_title: str) -> List[str]:
        """Возвращает стратегии митигации."""
        mitigation_map = {
            "SQL Injection": [
                "Использование параметризованных запросов",
                "Валидация входных данных",
                "Минимальные привилегии для БД"
            ],
            "Cross-Site Scripting (XSS)": [
                "Кодирование выходных данных",
                "Content Security Policy",
                "Валидация входных данных"
            ]
        }
        
        return mitigation_map.get(threat_title, ["Регулярный анализ безопасности"])
    
    def _get_detection_methods(self, threat_title: str) -> List[str]:
        """Возвращает методы обнаружения."""
        detection_map = {
            "SQL Injection": [
                "Анализ логов веб-сервера",
                "SIEM правила для SQL паттернов"
            ],
            "Cross-Site Scripting (XSS)": [
                "Анализ исходящего контента",
                "CSP violation reports"
            ]
        }
        
        return detection_map.get(threat_title, ["Логирование и мониторинг"])
    
    def _get_default_db_port(self, db_name: str) -> Optional[int]:
        """Возвращает порт по умолчанию для БД."""
        port_map = {
            "PostgreSQL": 5432,
            "MySQL": 3306,
            "MongoDB": 27017,
            "Redis": 6379
        }
        
        for db, port in port_map.items():
            if db in db_name:
                return port
        
        return None
    
    def _generate_assumptions(self, project_analysis: Dict[str, Any]) -> List[str]:
        """Генерирует предположения."""
        return [
            "Система развернута в доверенной сетевой среде",
            "Пользователи проходят базовое обучение по безопасности",
            "Регулярно применяются обновления безопасности"
        ]
    
    def _generate_out_of_scope(self) -> List[str]:
        """Генерирует список элементов вне области анализа."""
        return [
            "Физическая безопасность серверов",
            "DDoS атаки на инфраструктурном уровне",
            "Социальная инженерия"
        ]
    
    def _load_threat_knowledge_base(self) -> Dict[str, Any]:
        """Загружает базу знаний об угрозах."""
        return {
            "owasp_top_10": [
                "A01:2021 – Broken Access Control",
                "A02:2021 – Cryptographic Failures", 
                "A03:2021 – Injection"
            ]
        }
    
    def _load_technology_mappings(self) -> Dict[str, Any]:
        """Загружает маппинги технологий."""
        return {
            "web_frameworks": {
                "Django": ["SQL Injection", "XSS", "CSRF"],
                "Flask": ["XSS", "Session Management"]
            }
        }
    
    def export_to_json(self, threat_model: ThreatModel, output_path: str) -> None:
        """Экспортирует модель угроз в JSON."""
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, Enum):
                return obj.value
            return obj.__dict__
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(threat_model), f, indent=2, ensure_ascii=False, default=json_serializer)
    
    def export_to_yaml(self, threat_model: ThreatModel, output_path: str) -> None:
        """Экспортирует модель угроз в YAML."""
        def yaml_representer(dumper, data):
            if isinstance(data, datetime):
                return dumper.represent_scalar('tag:yaml.org,2002:timestamp', data.isoformat())
            elif isinstance(data, Enum):
                return dumper.represent_scalar('tag:yaml.org,2002:str', data.value)
            return dumper.represent_dict(data.__dict__)
        
        yaml.add_representer(datetime, yaml_representer)
        yaml.add_representer(ThreatCategory, yaml_representer)
        yaml.add_representer(AssetType, yaml_representer)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(asdict(threat_model), f, default_flow_style=False, allow_unicode=True)
    
    def generate_mermaid_diagram(self, threat_model: ThreatModel) -> str:
        """Генерирует Mermaid диаграмму архитектуры."""
        mermaid = "graph TD\n"
        
        # Добавляем активы
        for asset in threat_model.assets:
            asset_style = self._get_asset_style(asset.type)
            mermaid += f"    {asset.id}[\"{asset.name}\"]{asset_style}\n"
        
        # Добавляем потоки данных
        for flow in threat_model.data_flows:
            if flow.source != "external-users":
                arrow_style = "-->|" + flow.protocol + "|"
                mermaid += f"    {flow.source} {arrow_style} {flow.destination}\n"
        
        # Добавляем внешних пользователей
        mermaid += "    EXT[\"External Users\"]:::external\n"
        
        # Добавляем стили
        mermaid += "\n    classDef webapp fill:#e1f5fe\n"
        mermaid += "    classDef database fill:#fff3e0\n"
        mermaid += "    classDef api fill:#f3e5f5\n"
        mermaid += "    classDef external fill:#ffebee\n"
        
        return mermaid
    
    def _get_asset_style(self, asset_type: AssetType) -> str:
        """Возвращает стиль для типа актива."""
        style_map = {
            AssetType.WEB_APPLICATION: ":::webapp",
            AssetType.DATABASE: ":::database", 
            AssetType.API: ":::api",
            AssetType.EXTERNAL_SERVICE: ":::external"
        }
        
        return style_map.get(asset_type, "") 