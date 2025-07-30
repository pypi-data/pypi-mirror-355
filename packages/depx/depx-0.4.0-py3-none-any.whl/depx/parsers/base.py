"""
基础解析器模块

定义所有语言解析器的基础接口和数据结构
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class ProjectType(Enum):
    """项目类型枚举"""

    NODEJS = "nodejs"
    PYTHON = "python"
    JAVA = "java"
    GO = "go"
    RUST = "rust"
    PHP = "php"
    CSHARP = "csharp"
    UNKNOWN = "unknown"


class DependencyType(Enum):
    """依赖类型枚举"""

    PRODUCTION = "production"  # 生产依赖
    DEVELOPMENT = "development"  # 开发依赖
    OPTIONAL = "optional"  # 可选依赖
    PEER = "peer"  # 同级依赖
    GLOBAL = "global"  # 全局依赖


class PackageManagerType(Enum):
    """包管理器类型枚举"""

    NPM = "npm"
    YARN = "yarn"
    PNPM = "pnpm"
    PIP = "pip"
    CONDA = "conda"
    CARGO = "cargo"
    GO = "go"
    MAVEN = "maven"
    GRADLE = "gradle"
    COMPOSER = "composer"
    UNKNOWN = "unknown"


@dataclass
class DependencyInfo:
    """依赖信息数据类"""

    name: str  # 依赖名称
    version: str  # 声明版本
    installed_version: Optional[str] = None  # 实际安装版本
    dependency_type: DependencyType = DependencyType.PRODUCTION
    size_bytes: int = 0  # 占用空间（字节）
    install_path: Optional[Path] = None  # 安装路径
    description: Optional[str] = None  # 描述


@dataclass
class GlobalDependencyInfo:
    """全局依赖信息数据类"""

    name: str  # 依赖名称
    version: str  # 版本
    package_manager: PackageManagerType  # 包管理器类型
    install_path: Path  # 安装路径
    size_bytes: int = 0  # 占用空间（字节）
    description: Optional[str] = None  # 描述
    last_modified: Optional[str] = None  # 最后修改时间


@dataclass
class ProjectInfo:
    """项目信息数据类"""

    name: str  # 项目名称
    path: Path  # 项目路径
    project_type: ProjectType  # 项目类型
    config_file: Path  # 配置文件路径
    dependencies: List[DependencyInfo]  # 依赖列表
    total_size_bytes: int = 0  # 总占用空间
    metadata: Dict[str, Any] = None  # 额外元数据

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseParser(ABC):
    """基础解析器抽象类"""

    @property
    @abstractmethod
    def project_type(self) -> ProjectType:
        """返回解析器支持的项目类型"""
        pass

    @property
    @abstractmethod
    def config_files(self) -> List[str]:
        """返回该类型项目的配置文件名列表"""
        pass

    @abstractmethod
    def can_parse(self, project_path: Path) -> bool:
        """
        判断是否可以解析指定路径的项目

        Args:
            project_path: 项目路径

        Returns:
            是否可以解析
        """
        pass

    @abstractmethod
    def parse_project(self, project_path: Path) -> Optional[ProjectInfo]:
        """
        解析项目信息

        Args:
            project_path: 项目路径

        Returns:
            项目信息，解析失败时返回 None
        """
        pass

    @abstractmethod
    def get_dependencies(self, project_info: ProjectInfo) -> List[DependencyInfo]:
        """
        获取项目的依赖信息

        Args:
            project_info: 项目信息

        Returns:
            依赖信息列表
        """
        pass

    def calculate_dependency_sizes(self, project_info: ProjectInfo) -> None:
        """
        计算依赖的磁盘占用大小

        Args:
            project_info: 项目信息
        """
        # 默认实现，子类可以重写
        pass
