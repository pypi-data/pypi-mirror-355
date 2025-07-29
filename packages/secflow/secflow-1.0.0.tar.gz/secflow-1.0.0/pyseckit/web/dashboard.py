"""
Dashboard blueprint для веб-интерфейса PySecKit.
"""

from flask import Blueprint, render_template, request, jsonify, current_app, flash, redirect, url_for
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json


dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
def index():
    """Главная страница dashboard."""
    return render_template('dashboard/index.html')


@dashboard_bp.route('/scanners')
def scanners():
    """Страница управления сканерами."""
    scanner_manager = current_app.config.get('SCANNER_MANAGER')
    
    if not scanner_manager:
        flash('Менеджер сканеров не инициализирован', 'error')
        return redirect(url_for('dashboard.index'))
    
    available_scanners = scanner_manager.get_available_scanners()
    return render_template('dashboard/scanners.html', scanners=available_scanners)


@dashboard_bp.route('/scan')
def scan_page():
    """Страница запуска сканирования."""
    scanner_manager = current_app.config.get('SCANNER_MANAGER')
    
    if not scanner_manager:
        flash('Менеджер сканеров не инициализирован', 'error')
        return redirect(url_for('dashboard.index'))
    
    available_scanners = scanner_manager.get_available_scanners()
    return render_template('dashboard/scan.html', scanners=available_scanners)


@dashboard_bp.route('/results')
def results():
    """Страница результатов сканирования."""
    es_integration = current_app.config.get('ELASTICSEARCH')
    
    # Получаем результаты из Elasticsearch или локального хранилища
    scan_results = []
    
    if es_integration and es_integration.enabled:
        try:
            # Получаем последние сканирования
            query = {"match_all": {}}
            results = es_integration.search_findings(query, size=50)
            scan_results = results
        except Exception as e:
            flash(f'Ошибка при получении результатов из Elasticsearch: {e}', 'error')
    
    return render_template('dashboard/results.html', results=scan_results)


@dashboard_bp.route('/statistics')
def statistics():
    """Страница статистики."""
    es_integration = current_app.config.get('ELASTICSEARCH')
    
    stats = {}
    
    if es_integration and es_integration.enabled:
        try:
            stats = es_integration.get_scan_statistics(days=30)
        except Exception as e:
            flash(f'Ошибка при получении статистики: {e}', 'error')
            stats = {}
    
    return render_template('dashboard/statistics.html', stats=stats)


@dashboard_bp.route('/plugins')
def plugins():
    """Страница управления плагинами."""
    from pyseckit.plugins.registry import plugin_registry
    
    available_plugins = plugin_registry.list_plugins()
    return render_template('dashboard/plugins.html', plugins=available_plugins)


@dashboard_bp.route('/threat-model')
def threat_model():
    """Страница моделирования угроз."""
    return render_template('dashboard/threat_model.html')


@dashboard_bp.route('/settings')
def settings():
    """Страница настроек."""
    config = current_app.config.get('PYSECKIT')
    
    # Маскируем чувствительные данные
    if config:
        config_dict = config.config.copy()
        _mask_sensitive_data(config_dict)
    else:
        config_dict = {}
    
    return render_template('dashboard/settings.html', config=config_dict)


@dashboard_bp.route('/notifications')
def notifications():
    """Страница настройки уведомлений."""
    notification_manager = current_app.config.get('NOTIFICATIONS')
    
    notifier_status = {}
    if notification_manager:
        for notifier in notification_manager.notifiers:
            notifier_name = notifier.__class__.__name__
            notifier_status[notifier_name] = {
                'enabled': notifier.enabled,
                'config': _mask_notifier_config(notifier.config)
            }
    
    return render_template('dashboard/notifications.html', notifiers=notifier_status)


def _mask_sensitive_data(data: Dict[str, Any]) -> None:
    """Маскирует чувствительные данные в конфигурации."""
    sensitive_keys = ['password', 'token', 'key', 'secret', 'webhook_url']
    
    if isinstance(data, dict):
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                if isinstance(value, str) and len(value) > 4:
                    data[key] = value[:4] + '*' * (len(value) - 4)
            elif isinstance(value, dict):
                _mask_sensitive_data(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        _mask_sensitive_data(item)


def _mask_notifier_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Маскирует конфигурацию уведомителей."""
    masked_config = config.copy()
    _mask_sensitive_data(masked_config)
    return masked_config 