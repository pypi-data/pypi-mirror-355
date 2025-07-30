"""
包管理器模块

提供各种编程语言包管理器的统一接口
"""

from .base import (
    BasePackageManager,
    OutdatedPackage,
    PackageManagerResult,
    SearchResult,
    UpdateResult,
)
from .npm import NPMManager
from .pip import PipManager
from .yarn import YarnManager
from .cargo import CargoManager

__all__ = [
    "BasePackageManager",
    "PackageManagerResult",
    "SearchResult",
    "OutdatedPackage",
    "UpdateResult",
    "NPMManager",
    "PipManager",
    "YarnManager",
    "CargoManager",
]
