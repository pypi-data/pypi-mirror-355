"""
Depx - 本地多语言依赖统一管理器

统一发现、信息透明、空间优化、跨平台支持
"""

__version__ = "0.5.1"
__author__ = "Depx Team"
__description__ = "本地多语言依赖统一管理器"

from .core.analyzer import DependencyAnalyzer
from .core.global_scanner import GlobalScanner
from .core.scanner import ProjectScanner

__all__ = [
    "ProjectScanner",
    "DependencyAnalyzer",
    "GlobalScanner",
]
