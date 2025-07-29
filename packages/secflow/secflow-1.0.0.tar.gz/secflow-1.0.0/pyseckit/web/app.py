"""
Основное Flask приложение для веб-интерфейса PySecKit.
"""

import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
from datetime import datetime
from typing import Dict, Any, Optional

from pyseckit.core.config import Config
from pyseckit.core.scanner import ScannerManager
from pyseckit.plugins.registry import plugin_registry
from pyseckit.integrations.elasticsearch_integration import ElasticsearchIntegration
from pyseckit.integrations.notifications import NotificationManager


def create_app(config_path: Optional[str] = None) -> Flask:
    """Создает и настраивает Flask приложение."""
    app = Flask(__name__)
    
    # Основные настройки
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['PYSECKIT_CONFIG'] = config_path or '.pyseckit.yml'
    
    # Включаем CORS для API запросов
    CORS(app)
    
    # Инициализируем PySecKit компоненты
    try:
        config = Config.from_file(app.config['PYSECKIT_CONFIG'])
        app.config['PYSECKIT'] = config
        
        # Менеджер сканеров
        scanner_manager = ScannerManager(config.get_scanners_config())
        app.config['SCANNER_MANAGER'] = scanner_manager
        
        # Elasticsearch интеграция
        es_config = config.config.get('integrations', {}).get('elasticsearch', {})
        es_integration = ElasticsearchIntegration(es_config)
        app.config['ELASTICSEARCH'] = es_integration
        
        # Менеджер уведомлений
        notifications_config = config.config.get('integrations', {}).get('notifications', {})
        notification_manager = NotificationManager(notifications_config)
        app.config['NOTIFICATIONS'] = notification_manager
        
    except Exception as e:
        print(f"Предупреждение: Не удалось загрузить конфигурацию PySecKit: {e}")
        app.config['PYSECKIT'] = None
    
    # Регистрируем blueprints
    from .dashboard import dashboard_bp
    from .api import api_bp
    
    app.register_blueprint(dashboard_bp, url_prefix='/')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Обработчики ошибок
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500
    
    # Контекст процессор для шаблонов
    @app.context_processor
    def inject_global_vars():
        return {
            'app_name': 'PySecKit',
            'current_year': datetime.now().year,
            'config_loaded': app.config.get('PYSECKIT') is not None
        }
    
    return app


class WebInterface:
    """Основной класс веб-интерфейса."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.app = create_app(config_path)
        self.config = self.app.config.get('PYSECKIT')
        self.scanner_manager = self.app.config.get('SCANNER_MANAGER')
        self.es_integration = self.app.config.get('ELASTICSEARCH')
        self.notification_manager = self.app.config.get('NOTIFICATIONS')
    
    def run(self, host: str = '127.0.0.1', port: int = 5000, debug: bool = False) -> None:
        """Запускает веб-интерфейс."""
        print(f"🚀 Запуск PySecKit Web Interface на http://{host}:{port}")
        print(f"📊 Dashboard: http://{host}:{port}/")
        print(f"🔌 API: http://{host}:{port}/api/")
        
        self.app.run(host=host, port=port, debug=debug)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Возвращает статус системы."""
        status = {
            "config_loaded": self.config is not None,
            "elasticsearch_enabled": False,
            "notifications_enabled": False,
            "scanners_available": 0,
            "plugins_loaded": 0
        }
        
        if self.config:
            status["elasticsearch_enabled"] = (
                self.es_integration and 
                self.es_integration.enabled
            )
            
            status["notifications_enabled"] = (
                self.notification_manager and 
                len(self.notification_manager.notifiers) > 0
            )
            
            if self.scanner_manager:
                status["scanners_available"] = len(self.scanner_manager.get_available_scanners())
            
            status["plugins_loaded"] = len(plugin_registry.list_plugins())
        
        return status 