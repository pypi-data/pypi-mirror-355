"""
API blueprint для REST API PySecKit.
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from typing import Dict, Any, List
import asyncio
import threading
import uuid
import json


api_bp = Blueprint('api', __name__)

# Хранилище активных сканирований
active_scans = {}


@api_bp.route('/status')
def status():
    """Возвращает статус системы."""
    try:
        config = current_app.config.get('PYSECKIT')
        scanner_manager = current_app.config.get('SCANNER_MANAGER')
        es_integration = current_app.config.get('ELASTICSEARCH')
        notification_manager = current_app.config.get('NOTIFICATIONS')
        
        status_data = {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "config_loaded": config is not None,
            "components": {
                "scanner_manager": scanner_manager is not None,
                "elasticsearch": es_integration and es_integration.enabled if es_integration else False,
                "notifications": notification_manager and len(notification_manager.notifiers) > 0 if notification_manager else False
            }
        }
        
        if scanner_manager:
            status_data["scanners"] = {
                "available": len(scanner_manager.get_available_scanners()),
                "active_scans": len(active_scans)
            }
        
        return jsonify(status_data)
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api_bp.route('/scanners')
def list_scanners():
    """Возвращает список доступных сканеров."""
    try:
        scanner_manager = current_app.config.get('SCANNER_MANAGER')
        
        if not scanner_manager:
            return jsonify({"error": "Scanner manager not initialized"}), 500
        
        scanners = scanner_manager.get_available_scanners()
        return jsonify({"scanners": scanners})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route('/plugins')
def list_plugins():
    """Возвращает список доступных плагинов."""
    try:
        from pyseckit.plugins.registry import plugin_registry
        
        plugins = plugin_registry.list_plugins()
        return jsonify({"plugins": plugins})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route('/scan', methods=['POST'])
def start_scan():
    """Запускает новое сканирование."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        target = data.get('target')
        scanners = data.get('scanners', [])
        
        if not target:
            return jsonify({"error": "Target is required"}), 400
        
        if not scanners:
            return jsonify({"error": "At least one scanner must be specified"}), 400
        
        scanner_manager = current_app.config.get('SCANNER_MANAGER')
        
        if not scanner_manager:
            return jsonify({"error": "Scanner manager not initialized"}), 500
        
        # Создаем уникальный ID для сканирования
        scan_id = str(uuid.uuid4())
        
        # Запускаем сканирование в отдельном потоке
        scan_thread = threading.Thread(
            target=_run_scan_background,
            args=(scan_id, target, scanners, scanner_manager)
        )
        
        # Сохраняем информацию о сканировании
        active_scans[scan_id] = {
            "id": scan_id,
            "target": target,
            "scanners": scanners,
            "status": "running",
            "started_at": datetime.now().isoformat(),
            "thread": scan_thread
        }
        
        scan_thread.start()
        
        return jsonify({
            "scan_id": scan_id,
            "status": "started",
            "target": target,
            "scanners": scanners
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route('/scan/<scan_id>')
def get_scan_status(scan_id: str):
    """Возвращает статус сканирования."""
    try:
        if scan_id not in active_scans:
            return jsonify({"error": "Scan not found"}), 404
        
        scan_info = active_scans[scan_id].copy()
        # Удаляем объект thread из ответа
        scan_info.pop('thread', None)
        
        return jsonify(scan_info)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route('/scan/<scan_id>/results')
def get_scan_results(scan_id: str):
    """Возвращает результаты сканирования."""
    try:
        if scan_id not in active_scans:
            return jsonify({"error": "Scan not found"}), 404
        
        scan_info = active_scans[scan_id]
        
        if scan_info["status"] != "completed":
            return jsonify({"error": "Scan not completed"}), 400
        
        results = scan_info.get("results", {})
        return jsonify(results)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route('/threat-model', methods=['POST'])
def generate_threat_model():
    """Генерирует модель угроз."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        target_path = data.get('target_path')
        
        if not target_path:
            return jsonify({"error": "Target path is required"}), 400
        
        from pyseckit.threat_model.advanced_generator import AdvancedThreatModelGenerator
        
        generator = AdvancedThreatModelGenerator()
        threat_model = generator.analyze_codebase(target_path)
        
        # Конвертируем в JSON-сериализуемый формат
        def serialize_threat_model(obj):
            if hasattr(obj, '__dict__'):
                return obj.__dict__
            elif isinstance(obj, datetime):
                return obj.isoformat()
            elif hasattr(obj, 'value'):  # Enum
                return obj.value
            return str(obj)
        
        threat_model_dict = json.loads(json.dumps(threat_model, default=serialize_threat_model))
        
        return jsonify(threat_model_dict)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route('/notifications/test', methods=['POST'])
def test_notifications():
    """Тестирует настроенные уведомления."""
    try:
        notification_manager = current_app.config.get('NOTIFICATIONS')
        
        if not notification_manager:
            return jsonify({"error": "Notification manager not initialized"}), 500
        
        results = notification_manager.test_notifications()
        
        return jsonify({"test_results": results})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route('/statistics')
def get_statistics():
    """Возвращает статистику сканирований."""
    try:
        es_integration = current_app.config.get('ELASTICSEARCH')
        
        if not es_integration or not es_integration.enabled:
            return jsonify({"error": "Elasticsearch not configured"}), 500
        
        days = request.args.get('days', 30, type=int)
        stats = es_integration.get_scan_statistics(days=days)
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route('/findings/search', methods=['POST'])
def search_findings():
    """Ищет находки по заданным критериям."""
    try:
        es_integration = current_app.config.get('ELASTICSEARCH')
        
        if not es_integration or not es_integration.enabled:
            return jsonify({"error": "Elasticsearch not configured"}), 500
        
        data = request.get_json()
        query = data.get('query', {"match_all": {}})
        size = data.get('size', 50)
        
        findings = es_integration.search_findings(query, size)
        
        return jsonify({"findings": findings})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _run_scan_background(scan_id: str, target: str, scanners: List[str], scanner_manager):
    """Выполняет сканирование в фоновом режиме."""
    try:
        # Обновляем статус
        active_scans[scan_id]["status"] = "running"
        
        results = {}
        
        for scanner_name in scanners:
            try:
                # Получаем и запускаем сканер
                result = scanner_manager.run_scanner(scanner_name, target)
                results[scanner_name] = {
                    "status": "completed",
                    "findings": result.findings if result else [],
                    "metadata": result.metadata if result else {}
                }
                
                # Отправляем в Elasticsearch если настроен
                es_integration = current_app.config.get('ELASTICSEARCH')
                if es_integration and es_integration.enabled and result:
                    es_integration.index_scan_result(result)
                    es_integration.index_findings(result)
                
            except Exception as e:
                results[scanner_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # Обновляем статус сканирования
        active_scans[scan_id].update({
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "results": results
        })
        
        # Отправляем уведомления
        notification_manager = current_app.config.get('NOTIFICATIONS')
        if notification_manager:
            # Создаем сводный результат для уведомления
            total_findings = sum(len(r.get("findings", [])) for r in results.values() if r.get("status") == "completed")
            
            if total_findings > 0:
                from pyseckit.core.scanner import ScanResult
                
                # Создаем объект результата для уведомления
                dummy_result = ScanResult(
                    scanner_name="Multiple Scanners",
                    target=target,
                    start_time=datetime.fromisoformat(active_scans[scan_id]["started_at"]),
                    end_time=datetime.now(),
                    findings=[],
                    metadata={"scan_id": scan_id, "total_findings": total_findings}
                )
                
                # Собираем все находки
                all_findings = []
                for scanner_result in results.values():
                    if scanner_result.get("status") == "completed":
                        all_findings.extend(scanner_result.get("findings", []))
                
                dummy_result.findings = all_findings
                
                notification_manager.send_scan_completed(dummy_result)
        
    except Exception as e:
        active_scans[scan_id].update({
            "status": "error",
            "completed_at": datetime.now().isoformat(),
            "error": str(e)
        }) 