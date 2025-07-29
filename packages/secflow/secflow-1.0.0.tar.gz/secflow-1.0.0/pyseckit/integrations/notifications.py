"""
Система уведомлений для PySecKit.
"""

import json
import requests
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List, Optional
from pyseckit.core.scanner import ScanResult


class BaseNotifier(ABC):
    """Базовый класс для уведомлений."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('enabled', False)
    
    @abstractmethod
    def send_notification(self, title: str, message: str, scan_result: Optional[ScanResult] = None) -> bool:
        """Отправляет уведомление."""
        pass
    
    def format_scan_summary(self, scan_result: ScanResult) -> str:
        """Форматирует краткую сводку сканирования."""
        total_findings = len(scan_result.findings)
        duration = (scan_result.end_time - scan_result.start_time).total_seconds()
        
        # Группируем по severity
        severity_counts = {}
        for finding in scan_result.findings:
            severity = finding.get('severity', 'INFO')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        summary = f"""📊 **Результаты сканирования**
🎯 **Цель:** {scan_result.target}
🔍 **Сканер:** {scan_result.scanner_name}
⏱️ **Длительность:** {duration:.1f} сек
📋 **Всего найдено:** {total_findings}"""
        
        if severity_counts:
            summary += "\n\n**По уровням:**"
            severity_emojis = {
                'HIGH': '🔴',
                'MEDIUM': '🟡', 
                'LOW': '🟢',
                'INFO': 'ℹ️'
            }
            
            for severity, count in severity_counts.items():
                emoji = severity_emojis.get(severity, '⚪')
                summary += f"\n{emoji} {severity}: {count}"
        
        return summary


class SlackNotifier(BaseNotifier):
    """Отправка уведомлений в Slack."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.webhook_url = config.get('webhook_url')
        self.channel = config.get('channel', '#security')
        self.username = config.get('username', 'PySecKit')
        self.icon_emoji = config.get('icon_emoji', ':shield:')
    
    def send_notification(self, title: str, message: str, scan_result: Optional[ScanResult] = None) -> bool:
        """Отправляет уведомление в Slack."""
        if not self.enabled or not self.webhook_url:
            return False
        
        try:
            payload = self._build_slack_payload(title, message, scan_result)
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Ошибка при отправке Slack уведомления: {e}")
            return False
    
    def _build_slack_payload(self, title: str, message: str, scan_result: Optional[ScanResult] = None) -> Dict[str, Any]:
        """Строит payload для Slack API."""
        color = self._get_color_for_scan(scan_result) if scan_result else "#36a64f"
        
        attachment = {
            "color": color,
            "title": title,
            "text": message,
            "footer": "PySecKit Security Scanner",
            "ts": int(datetime.now().timestamp())
        }
        
        if scan_result:
            attachment["fields"] = self._build_slack_fields(scan_result)
        
        return {
            "channel": self.channel,
            "username": self.username,
            "icon_emoji": self.icon_emoji,
            "attachments": [attachment]
        }
    
    def _build_slack_fields(self, scan_result: ScanResult) -> List[Dict[str, Any]]:
        """Строит поля для Slack attachment."""
        fields = [
            {
                "title": "Цель сканирования",
                "value": scan_result.target,
                "short": True
            },
            {
                "title": "Сканер",
                "value": scan_result.scanner_name,
                "short": True
            },
            {
                "title": "Всего находок",
                "value": str(len(scan_result.findings)),
                "short": True
            }
        ]
        
        # Добавляем топ-3 критичные находки
        high_severity_findings = [
            f for f in scan_result.findings 
            if f.get('severity') == 'HIGH'
        ][:3]
        
        if high_severity_findings:
            critical_list = []
            for finding in high_severity_findings:
                critical_list.append(f"• {finding.get('title', 'Unknown issue')}")
            
            fields.append({
                "title": "Критичные проблемы",
                "value": "\n".join(critical_list),
                "short": False
            })
        
        return fields
    
    def _get_color_for_scan(self, scan_result: ScanResult) -> str:
        """Возвращает цвет для результата сканирования."""
        high_count = sum(1 for f in scan_result.findings if f.get('severity') == 'HIGH')
        medium_count = sum(1 for f in scan_result.findings if f.get('severity') == 'MEDIUM')
        
        if high_count > 0:
            return "#ff0000"  # Красный
        elif medium_count > 0:
            return "#ffaa00"  # Оранжевый
        else:
            return "#36a64f"  # Зеленый


class TeamsNotifier(BaseNotifier):
    """Отправка уведомлений в Microsoft Teams."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.webhook_url = config.get('webhook_url')
    
    def send_notification(self, title: str, message: str, scan_result: Optional[ScanResult] = None) -> bool:
        """Отправляет уведомление в Teams."""
        if not self.enabled or not self.webhook_url:
            return False
        
        try:
            payload = self._build_teams_payload(title, message, scan_result)
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Ошибка при отправке Teams уведомления: {e}")
            return False
    
    def _build_teams_payload(self, title: str, message: str, scan_result: Optional[ScanResult] = None) -> Dict[str, Any]:
        """Строит payload для Teams API."""
        color = self._get_theme_color_for_scan(scan_result) if scan_result else "good"
        
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": color,
            "summary": title,
            "sections": [
                {
                    "activityTitle": title,
                    "activitySubtitle": "PySecKit Security Scanner",
                    "activityImage": "https://example.com/pyseckit-icon.png",
                    "text": message,
                    "markdown": True
                }
            ]
        }
        
        if scan_result:
            payload["sections"][0]["facts"] = self._build_teams_facts(scan_result)
            
            # Добавляем потенциальные действия
            payload["potentialAction"] = [
                {
                    "@type": "OpenUri",
                    "name": "Просмотреть отчет",
                    "targets": [
                        {
                            "os": "default",
                            "uri": f"file://{scan_result.target}"
                        }
                    ]
                }
            ]
        
        return payload
    
    def _build_teams_facts(self, scan_result: ScanResult) -> List[Dict[str, str]]:
        """Строит факты для Teams card."""
        duration = (scan_result.end_time - scan_result.start_time).total_seconds()
        
        facts = [
            {"name": "Цель", "value": scan_result.target},
            {"name": "Сканер", "value": scan_result.scanner_name},
            {"name": "Длительность", "value": f"{duration:.1f} сек"},
            {"name": "Всего находок", "value": str(len(scan_result.findings))}
        ]
        
        # Добавляем распределение по severity
        severity_counts = {}
        for finding in scan_result.findings:
            severity = finding.get('severity', 'INFO')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        if severity_counts:
            severity_str = ", ".join([f"{k}: {v}" for k, v in severity_counts.items()])
            facts.append({"name": "По уровням", "value": severity_str})
        
        return facts
    
    def _get_theme_color_for_scan(self, scan_result: ScanResult) -> str:
        """Возвращает цвет темы для результата сканирования."""
        high_count = sum(1 for f in scan_result.findings if f.get('severity') == 'HIGH')
        medium_count = sum(1 for f in scan_result.findings if f.get('severity') == 'MEDIUM')
        
        if high_count > 0:
            return "attention"  # Красный
        elif medium_count > 0:
            return "warning"   # Желтый
        else:
            return "good"      # Зеленый


class EmailNotifier(BaseNotifier):
    """Отправка email уведомлений."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.smtp_server = config.get('smtp_server')
        self.smtp_port = config.get('smtp_port', 587)
        self.username = config.get('username')
        self.password = config.get('password')
        self.from_email = config.get('from_email')
        self.to_emails = config.get('to_emails', [])
        self.use_tls = config.get('use_tls', True)
    
    def send_notification(self, title: str, message: str, scan_result: Optional[ScanResult] = None) -> bool:
        """Отправляет email уведомление."""
        if not self.enabled or not all([self.smtp_server, self.username, self.password, self.from_email, self.to_emails]):
            return False
        
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = title
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            
            # Создаем HTML версию
            html_content = self._build_html_content(title, message, scan_result)
            html_part = MIMEText(html_content, 'html')
            
            # Создаем текстовую версию
            text_content = self._build_text_content(title, message, scan_result)
            text_part = MIMEText(text_content, 'plain')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Отправляем
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            print(f"Ошибка при отправке email уведомления: {e}")
            return False
    
    def _build_html_content(self, title: str, message: str, scan_result: Optional[ScanResult] = None) -> str:
        """Строит HTML содержимое email."""
        html = f"""
        <html>
        <body>
            <h2>{title}</h2>
            <p>{message.replace('\n', '<br>')}</p>
        """
        
        if scan_result:
            html += f"""
            <h3>Детали сканирования</h3>
            <table border="1" style="border-collapse: collapse;">
                <tr><td><b>Цель:</b></td><td>{scan_result.target}</td></tr>
                <tr><td><b>Сканер:</b></td><td>{scan_result.scanner_name}</td></tr>
                <tr><td><b>Всего находок:</b></td><td>{len(scan_result.findings)}</td></tr>
            </table>
            """
        
        html += """
        <br>
        <p><i>Отправлено PySecKit Security Scanner</i></p>
        </body>
        </html>
        """
        
        return html
    
    def _build_text_content(self, title: str, message: str, scan_result: Optional[ScanResult] = None) -> str:
        """Строит текстовое содержимое email."""
        content = f"{title}\n\n{message}\n"
        
        if scan_result:
            content += f"\nДетали сканирования:\n"
            content += f"Цель: {scan_result.target}\n"
            content += f"Сканер: {scan_result.scanner_name}\n"
            content += f"Всего находок: {len(scan_result.findings)}\n"
        
        content += "\n--\nОтправлено PySecKit Security Scanner"
        
        return content


class NotificationManager:
    """Менеджер уведомлений."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.notifiers: List[BaseNotifier] = []
        
        self._initialize_notifiers()
    
    def _initialize_notifiers(self) -> None:
        """Инициализирует настроенные уведомители."""
        if 'slack' in self.config:
            self.notifiers.append(SlackNotifier(self.config['slack']))
        
        if 'teams' in self.config:
            self.notifiers.append(TeamsNotifier(self.config['teams']))
        
        if 'email' in self.config:
            self.notifiers.append(EmailNotifier(self.config['email']))
    
    def send_scan_completed(self, scan_result: ScanResult) -> Dict[str, bool]:
        """Отправляет уведомление о завершении сканирования."""
        title = f"🔍 Сканирование завершено: {scan_result.scanner_name}"
        message = self.notifiers[0].format_scan_summary(scan_result) if self.notifiers else ""
        
        return self.send_notification(title, message, scan_result)
    
    def send_critical_findings(self, scan_result: ScanResult) -> Dict[str, bool]:
        """Отправляет уведомление о критических находках."""
        critical_findings = [
            f for f in scan_result.findings 
            if f.get('severity') == 'HIGH'
        ]
        
        if not critical_findings:
            return {}
        
        title = f"🚨 Найдены критические уязвимости!"
        message = f"Обнаружено {len(critical_findings)} критических проблем в {scan_result.target}"
        
        return self.send_notification(title, message, scan_result)
    
    def send_notification(self, title: str, message: str, scan_result: Optional[ScanResult] = None) -> Dict[str, bool]:
        """Отправляет уведомление через все настроенные каналы."""
        results = {}
        
        for notifier in self.notifiers:
            notifier_name = notifier.__class__.__name__
            try:
                success = notifier.send_notification(title, message, scan_result)
                results[notifier_name] = success
            except Exception as e:
                print(f"Ошибка в {notifier_name}: {e}")
                results[notifier_name] = False
        
        return results
    
    def test_notifications(self) -> Dict[str, bool]:
        """Тестирует все настроенные уведомления."""
        title = "🧪 Тест уведомлений PySecKit"
        message = "Это тестовое сообщение для проверки настроек уведомлений."
        
        return self.send_notification(title, message) 