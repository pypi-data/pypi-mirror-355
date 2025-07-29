"""
GitLeaks сканнер для поиска секретов в Git репозиториях.
"""

import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..core.exceptions import ScannerException
from ..core.scanner import Scanner, ScanResult, Severity


class GitleaksScanner(Scanner):
    """Сканнер GitLeaks для поиска секретов."""
    
    @property
    def scanner_name(self) -> str:
        return "gitleaks"
    
    @property
    def version(self) -> str:
        return "8.18.0"
    
    @property
    def supported_formats(self) -> List[str]:
        return [".git", "*"]
    
    def is_available(self) -> bool:
        return shutil.which("gitleaks") is not None
    
    def scan(self, target: Union[str, Path], **kwargs) -> List[ScanResult]:
        """Выполняет поиск секретов с помощью GitLeaks."""
        # Заглушка - в реальной реализации здесь будет интеграция с GitLeaks
        return [] 