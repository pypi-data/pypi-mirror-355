"""
CLI интерфейс для PySecKit.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text

from .core.config import Config
from .core.scanner import ScannerManager, Severity
from .core.exceptions import PySecKitException
from .sast import BanditScanner, SemgrepScanner, SafetyScanner
from .reporting.manager import ReportManager

console = Console()


def print_banner():
    """Выводит баннер PySecKit."""
    banner = """
[bold blue]
╔═══════════════════════════════════════════════════════════════╗
║                            PySecKit                           ║
║           Универсальный фреймворк безопасности для            ║
║                      DevSecOps процессов                     ║
╚═══════════════════════════════════════════════════════════════╝
[/bold blue]
    """
    console.print(banner)


@click.group()
@click.option('--config', '-c', type=click.Path(exists=True), help='Путь к файлу конфигурации')
@click.option('--verbose', '-v', is_flag=True, help='Подробный вывод')
@click.pass_context
def cli(ctx: click.Context, config: Optional[str], verbose: bool) -> None:
    """PySecKit - Универсальный фреймворк безопасности для DevSecOps."""
    
    # Инициализируем контекст
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    
    # Загружаем конфигурацию
    try:
        if config:
            ctx.obj['config'] = Config.from_file(config)
        else:
            ctx.obj['config'] = Config.load_default()
    except Exception as e:
        console.print(f"[red]Ошибка загрузки конфигурации: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('target', type=click.Path(exists=True))
@click.option('--scanner', '-s', multiple=True, help='Конкретные сканнеры для запуска')
@click.option('--output', '-o', type=click.Path(), help='Файл для сохранения результатов')
@click.option('--format', '-f', type=click.Choice(['json', 'html', 'csv', 'xml']), default='json', help='Формат вывода')
@click.option('--severity', type=click.Choice(['info', 'low', 'medium', 'high', 'critical']), help='Минимальный уровень критичности')
@click.option('--exclude', multiple=True, help='Паттерны исключений')
@click.pass_context
def scan(ctx: click.Context, target: str, scanner: tuple, output: Optional[str], 
         format: str, severity: Optional[str], exclude: tuple) -> None:
    """Выполняет комплексное сканирование безопасности."""
    
    print_banner()
    
    config = ctx.obj['config']
    verbose = ctx.obj['verbose']
    
    target_path = Path(target)
    
    if verbose:
        console.print(f"[blue]Сканирование цели:[/blue] {target_path}")
        console.print(f"[blue]Формат вывода:[/blue] {format}")
    
    # Инициализируем менеджер сканнеров
    manager = ScannerManager()
    
    # Регистрируем доступные сканнеры
    available_scanners = {
        'bandit': BanditScanner,
        'semgrep': SemgrepScanner,
        'safety': SafetyScanner,
    }
    
    scanners_to_use = list(scanner) if scanner else list(available_scanners.keys())
    
    # Регистрируем выбранные сканнеры
    for scanner_name in scanners_to_use:
        if scanner_name in available_scanners:
            scanner_config = config.get_scanner_config(scanner_name)
            scanner_instance = available_scanners[scanner_name](scanner_config.dict())
            manager.register_scanner(scanner_instance)
    
    # Получаем список доступных сканнеров
    available_scanner_names = manager.get_available_scanners()
    
    if not available_scanner_names:
        console.print("[red]Нет доступных сканнеров. Убедитесь, что необходимые инструменты установлены.[/red]")
        sys.exit(1)
    
    if verbose:
        console.print(f"[green]Доступные сканнеры:[/green] {', '.join(available_scanner_names)}")
    
    # Выполняем сканирование с прогресс-баром
    results = {}
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        for scanner_name in available_scanner_names:
            task = progress.add_task(f"Сканирование с {scanner_name}...", total=None)
            
            try:
                scanner_instance = manager.get_scanner(scanner_name)
                if scanner_instance:
                    scan_kwargs = {}
                    
                    # Добавляем параметры исключения
                    if exclude:
                        scan_kwargs['exclude'] = list(exclude)
                    
                    # Добавляем минимальный уровень критичности
                    if severity:
                        scan_kwargs['severity'] = severity
                    
                    scan_results = scanner_instance.scan(target_path, **scan_kwargs)
                    results[scanner_name] = scan_results
                    
                    progress.update(task, description=f"✓ {scanner_name} ({len(scan_results)} проблем)")
                
            except Exception as e:
                progress.update(task, description=f"✗ {scanner_name} (ошибка)")
                if verbose:
                    console.print(f"[red]Ошибка сканнера {scanner_name}: {e}[/red]")
                results[scanner_name] = []
    
    # Подсчитываем статистику
    total_issues = sum(len(scan_results) for scan_results in results.values())
    
    if total_issues == 0:
        console.print("\n[green]✓ Проблемы безопасности не найдены![/green]")
    else:
        # Показываем статистику
        _display_scan_statistics(results)
        
        # Показываем топ проблем
        if verbose:
            _display_top_issues(results)
    
    # Сохраняем результаты
    if output or total_issues > 0:
        output_path = Path(output) if output else Path(f"pyseckit_report.{format}")
        
        report_manager = ReportManager(config.reporting)
        all_results = []
        for scan_results in results.values():
            all_results.extend(scan_results)
        
        if format == 'json':
            report_manager.generate_json_report(all_results, output_path)
        elif format == 'html':
            report_manager.generate_html_report(all_results, output_path)
        elif format == 'csv':
            report_manager.generate_csv_report(all_results, output_path)
        elif format == 'xml':
            report_manager.generate_xml_report(all_results, output_path)
        
        console.print(f"\n[blue]Отчёт сохранён:[/blue] {output_path}")
    
    # Возвращаем код выхода
    if config.cicd.fail_on_critical:
        critical_issues = sum(
            1 for scan_results in results.values() 
            for result in scan_results 
            if result.severity == Severity.CRITICAL
        )
        if critical_issues > 0:
            console.print(f"\n[red]Найдено {critical_issues} критических проблем. Завершение с ошибкой.[/red]")
            sys.exit(1)
    
    if config.cicd.fail_on_high:
        high_issues = sum(
            1 for scan_results in results.values() 
            for result in scan_results 
            if result.severity in [Severity.CRITICAL, Severity.HIGH]
        )
        if high_issues > 0:
            console.print(f"\n[red]Найдено {high_issues} критических/высоких проблем. Завершение с ошибкой.[/red]")
            sys.exit(1)


@cli.command()
@click.pass_context
def init(ctx: click.Context) -> None:
    """Инициализирует конфигурацию PySecKit."""
    
    config_path = Path(".pyseckit.yml")
    
    if config_path.exists():
        if not click.confirm(f"Файл {config_path} уже существует. Перезаписать?"):
            return
    
    # Создаём базовую конфигурацию
    config = Config()
    config.to_file(config_path)
    
    console.print(f"[green]✓ Конфигурация создана:[/green] {config_path}")
    console.print("\n[blue]Настройте файл конфигурации под ваши нужды:[/blue]")
    console.print("- Добавьте пути для сканирования в target_directories")
    console.print("- Настройте исключения в exclude_patterns")
    console.print("- Настройте параметры сканнеров в секции scanners")


@cli.command()
@click.pass_context
def list_scanners(ctx: click.Context) -> None:
    """Показывает список доступных сканнеров."""
    
    scanners_info = [
        ("bandit", "Статический анализ Python кода", BanditScanner().is_available()),
        ("semgrep", "Многоязычный статический анализ", SemgrepScanner().is_available()),
        ("safety", "Проверка уязвимых зависимостей Python", SafetyScanner().is_available()),
    ]
    
    table = Table(title="Доступные сканнеры")
    table.add_column("Сканнер", style="cyan")
    table.add_column("Описание", style="white")
    table.add_column("Статус", style="green")
    
    for name, description, available in scanners_info:
        status = "✓ Доступен" if available else "✗ Не установлен"
        status_style = "green" if available else "red"
        table.add_row(name, description, f"[{status_style}]{status}[/{status_style}]")
    
    console.print(table)


@cli.command()
@click.argument('config_file', type=click.Path())
@click.pass_context
def validate_config(ctx: click.Context, config_file: str) -> None:
    """Проверяет конфигурационный файл."""
    
    config_path = Path(config_file)
    
    try:
        config = Config.from_file(config_path)
        console.print(f"[green]✓ Конфигурация валидна:[/green] {config_path}")
        
        # Показываем краткую информацию
        console.print(f"[blue]Проект:[/blue] {config.project_name}")
        console.print(f"[blue]Целевые директории:[/blue] {', '.join(config.target_directories)}")
        console.print(f"[blue]Сканнеры:[/blue] {len(config.scanners)} настроено")
        
    except Exception as e:
        console.print(f"[red]✗ Ошибка конфигурации: {e}[/red]")
        sys.exit(1)


def _display_scan_statistics(results: Dict[str, List]) -> None:
    """Отображает статистику сканирования."""
    
    table = Table(title="Статистика сканирования")
    table.add_column("Сканнер", style="cyan")
    table.add_column("Всего", style="white")
    table.add_column("Критические", style="red")
    table.add_column("Высокие", style="yellow")
    table.add_column("Средние", style="blue")
    table.add_column("Низкие", style="green")
    
    for scanner_name, scan_results in results.items():
        total = len(scan_results)
        critical = sum(1 for r in scan_results if r.severity == Severity.CRITICAL)
        high = sum(1 for r in scan_results if r.severity == Severity.HIGH)
        medium = sum(1 for r in scan_results if r.severity == Severity.MEDIUM)
        low = sum(1 for r in scan_results if r.severity == Severity.LOW)
        
        table.add_row(
            scanner_name,
            str(total),
            str(critical),
            str(high), 
            str(medium),
            str(low)
        )
    
    console.print("\n")
    console.print(table)


def _display_top_issues(results: Dict[str, List], limit: int = 10) -> None:
    """Отображает топ проблем."""
    
    all_results = []
    for scan_results in results.values():
        all_results.extend(scan_results)
    
    # Сортируем по критичности
    sorted_results = sorted(all_results, key=lambda x: x.severity.priority, reverse=True)
    
    if not sorted_results:
        return
    
    console.print(f"\n[bold]Топ {min(limit, len(sorted_results))} проблем:[/bold]")
    
    for i, result in enumerate(sorted_results[:limit], 1):
        severity_color = {
            Severity.CRITICAL: "red",
            Severity.HIGH: "yellow", 
            Severity.MEDIUM: "blue",
            Severity.LOW: "green",
            Severity.INFO: "white"
        }.get(result.severity, "white")
        
        file_info = f" в {result.file_path}:{result.line_number}" if result.file_path else ""
        
        console.print(
            f"[white]{i}.[/white] "
            f"[{severity_color}]{result.severity.value.upper()}[/{severity_color}] "
            f"[bold]{result.title}[/bold]"
            f"{file_info}"
        )
        
        if result.description:
            console.print(f"   {result.description}")


def main() -> None:
    """Точка входа CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Сканирование прервано пользователем.[/yellow]")
        sys.exit(130)
    except PySecKitException as e:
        console.print(f"\n[red]Ошибка PySecKit: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Неожиданная ошибка: {e}[/red]")
        sys.exit(1)


# Новые команды для расширенной функциональности

@cli.command()
@click.option('--host', default='127.0.0.1', help='Хост для веб-интерфейса')
@click.option('--port', default=5000, help='Порт для веб-интерфейса')
@click.option('--debug', is_flag=True, help='Режим отладки')
@click.pass_context
def web(ctx, host, port, debug):
    """Запускает веб-интерфейс для управления PySecKit."""
    try:
        from pyseckit.web.app import WebInterface
        
        console.print("🚀 Запуск веб-интерфейса PySecKit...", style="bold blue")
        
        web_interface = WebInterface(ctx.obj['config'])
        web_interface.run(host=host, port=port, debug=debug)
        
    except ImportError:
        console.print("❌ Веб-интерфейс недоступен. Установите: pip install flask flask-cors", style="bold red")
    except Exception as e:
        console.print(f"❌ Ошибка запуска веб-интерфейса: {e}", style="bold red")


@cli.command()
@click.argument('target_path')
@click.option('--output', '-o', help='Файл для сохранения модели угроз')
@click.option('--format', 'output_format', default='json', type=click.Choice(['json', 'yaml']), help='Формат вывода')
@click.pass_context
def threat_model(ctx, target_path, output, output_format):
    """Генерирует модель угроз для указанного пути."""
    try:
        from pyseckit.threat_model.advanced_generator import AdvancedThreatModelGenerator
        
        console.print(f"🛡️ Анализ угроз для: {target_path}", style="bold blue")
        
        with console.status("[bold green]Анализируем структуру проекта..."):
            generator = AdvancedThreatModelGenerator()
            threat_model = generator.analyze_codebase(target_path)
        
        console.print(f"✅ Модель угроз создана:", style="bold green")
        console.print(f"   📋 Активов: {len(threat_model.assets)}")
        console.print(f"   🔄 Потоков данных: {len(threat_model.data_flows)}")
        console.print(f"   ⚠️ Угроз: {len(threat_model.threats)}")
        
        if output:
            if output_format == 'json':
                generator.export_to_json(threat_model, output)
            else:
                generator.export_to_yaml(threat_model, output)
            console.print(f"💾 Модель сохранена в: {output}")
        
    except Exception as e:
        console.print(f"❌ Ошибка создания модели угроз: {e}", style="bold red")


@cli.command()
@click.pass_context
def plugins(ctx):
    """Управление плагинами PySecKit."""
    try:
        from pyseckit.plugins.registry import plugin_registry
        
        console.print("🔌 Доступные плагины:", style="bold blue")
        
        plugins = plugin_registry.list_plugins()
        
        if not plugins:
            console.print("   Плагины не найдены", style="dim")
            return
        
        table = Table()
        table.add_column("Название", style="cyan")
        table.add_column("Версия", style="magenta")
        table.add_column("Категория", style="green")
        table.add_column("Статус", style="yellow")
        
        for plugin in plugins:
            status = "✅ Инициализирован" if plugin.get('initialized') else "⏸️ Зарегистрирован"
            table.add_row(
                plugin['name'],
                plugin['version'],
                plugin['category'],
                status
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"❌ Ошибка получения списка плагинов: {e}", style="bold red")


@cli.command()
@click.pass_context
def test_notifications(ctx):
    """Тестирует настроенные уведомления."""
    try:
        from pyseckit.core.config import Config
        from pyseckit.integrations.notifications import NotificationManager
        
        config = Config.from_file(ctx.obj['config'])
        notifications_config = config.config.get('integrations', {}).get('notifications', {})
        
        if not notifications_config:
            console.print("❌ Уведомления не настроены", style="bold red")
            return
        
        console.print("📢 Тестирование уведомлений...", style="bold blue")
        
        notification_manager = NotificationManager(notifications_config)
        results = notification_manager.test_notifications()
        
        for notifier_name, success in results.items():
            status = "✅ Успешно" if success else "❌ Ошибка"
            console.print(f"   {notifier_name}: {status}")
        
    except Exception as e:
        console.print(f"❌ Ошибка тестирования уведомлений: {e}", style="bold red")


if __name__ == "__main__":
    main() 