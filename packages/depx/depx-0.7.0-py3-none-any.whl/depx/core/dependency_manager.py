"""
依赖管理器

提供统一的依赖安装和卸载功能
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Type

from ..parsers.base import PackageManagerType, ProjectType
from .package_managers import (
    BasePackageManager,
    CargoManager,
    NPMManager,
    PackageManagerResult,
    PipManager,
    YarnManager,
)
from .scanner import ProjectScanner

logger = logging.getLogger(__name__)


class DependencyManager:
    """依赖管理器"""

    def __init__(self):
        """初始化依赖管理器"""
        self.scanner = ProjectScanner()

        # 包管理器映射
        self.package_managers: Dict[PackageManagerType, Type[BasePackageManager]] = {
            PackageManagerType.NPM: NPMManager,
            PackageManagerType.YARN: YarnManager,
            PackageManagerType.PIP: PipManager,
            PackageManagerType.CARGO: CargoManager,
        }

        # 项目类型到包管理器的映射
        self.project_to_managers: Dict[ProjectType, List[PackageManagerType]] = {
            ProjectType.NODEJS: [PackageManagerType.NPM, PackageManagerType.YARN],
            ProjectType.PYTHON: [PackageManagerType.PIP],
            ProjectType.RUST: [PackageManagerType.CARGO],
        }

    def detect_project_type(self, project_path: Path) -> Optional[ProjectType]:
        """
        检测项目类型
        
        Args:
            project_path: 项目路径
            
        Returns:
            项目类型，如果无法检测则返回 None
        """
        project = self.scanner.scan_single_project(project_path)
        return project.project_type if project else None

    def get_available_package_managers(
        self, project_type: ProjectType, project_path: Optional[Path] = None
    ) -> List[BasePackageManager]:
        """
        获取可用的包管理器
        
        Args:
            project_type: 项目类型
            project_path: 项目路径
            
        Returns:
            可用的包管理器列表
        """
        available_managers = []
        manager_types = self.project_to_managers.get(project_type, [])

        for manager_type in manager_types:
            manager_class = self.package_managers.get(manager_type)
            if manager_class:
                manager = manager_class(project_path)
                if manager.is_available():
                    available_managers.append(manager)

        return available_managers

    def detect_preferred_package_manager(
        self, project_path: Path, project_type: ProjectType
    ) -> Optional[BasePackageManager]:
        """
        检测首选的包管理器
        
        Args:
            project_path: 项目路径
            project_type: 项目类型
            
        Returns:
            首选的包管理器，如果没有则返回 None
        """
        if project_type == ProjectType.NODEJS:
            # 检查 Node.js 项目的锁文件来确定包管理器
            if (project_path / "yarn.lock").exists():
                return YarnManager(project_path)
            elif (project_path / "package-lock.json").exists():
                return NPMManager(project_path)
            else:
                # 默认使用 npm
                npm_manager = NPMManager(project_path)
                return npm_manager if npm_manager.is_available() else None

        elif project_type == ProjectType.PYTHON:
            pip_manager = PipManager(project_path)
            return pip_manager if pip_manager.is_available() else None

        elif project_type == ProjectType.RUST:
            cargo_manager = CargoManager(project_path)
            return cargo_manager if cargo_manager.is_available() else None

        return None

    def install_package(
        self,
        package_name: str,
        project_path: Optional[Path] = None,
        project_type: Optional[ProjectType] = None,
        package_manager: Optional[str] = None,
        dev: bool = False,
        global_install: bool = False,
    ) -> PackageManagerResult:
        """
        安装包
        
        Args:
            package_name: 包名
            project_path: 项目路径
            project_type: 项目类型
            package_manager: 指定的包管理器
            dev: 是否为开发依赖
            global_install: 是否全局安装
            
        Returns:
            操作结果
        """
        # 如果没有指定项目类型，尝试检测
        if not project_type and project_path:
            project_type = self.detect_project_type(project_path)

        if not project_type:
            return PackageManagerResult(
                success=False,
                message="无法检测项目类型，请使用 --type 参数指定",
                command="",
                error="Unknown project type"
            )

        # 获取包管理器
        manager = None
        if package_manager:
            # 使用指定的包管理器
            try:
                manager_type = PackageManagerType(package_manager.lower())
                manager_class = self.package_managers.get(manager_type)
                if manager_class:
                    manager = manager_class(project_path)
            except ValueError:
                return PackageManagerResult(
                    success=False,
                    message=f"不支持的包管理器: {package_manager}",
                    command="",
                    error="Unsupported package manager"
                )
        else:
            # 自动检测包管理器
            manager = self.detect_preferred_package_manager(project_path, project_type)

        if not manager:
            return PackageManagerResult(
                success=False,
                message="没有找到可用的包管理器",
                command="",
                error="No available package manager"
            )

        if not manager.is_available():
            return PackageManagerResult(
                success=False,
                message=f"{manager.name} 命令不可用",
                command="",
                error=f"{manager.name} command not found"
            )

        # 执行安装
        return manager.install(package_name, dev=dev, global_install=global_install)

    def uninstall_package(
        self,
        package_name: str,
        project_path: Optional[Path] = None,
        project_type: Optional[ProjectType] = None,
        package_manager: Optional[str] = None,
        global_uninstall: bool = False,
    ) -> PackageManagerResult:
        """
        卸载包
        
        Args:
            package_name: 包名
            project_path: 项目路径
            project_type: 项目类型
            package_manager: 指定的包管理器
            global_uninstall: 是否全局卸载
            
        Returns:
            操作结果
        """
        # 如果没有指定项目类型，尝试检测
        if not project_type and project_path:
            project_type = self.detect_project_type(project_path)

        if not project_type:
            return PackageManagerResult(
                success=False,
                message="无法检测项目类型，请使用 --type 参数指定",
                command="",
                error="Unknown project type"
            )

        # 获取包管理器
        manager = None
        if package_manager:
            # 使用指定的包管理器
            try:
                manager_type = PackageManagerType(package_manager.lower())
                manager_class = self.package_managers.get(manager_type)
                if manager_class:
                    manager = manager_class(project_path)
            except ValueError:
                return PackageManagerResult(
                    success=False,
                    message=f"不支持的包管理器: {package_manager}",
                    command="",
                    error="Unsupported package manager"
                )
        else:
            # 自动检测包管理器
            manager = self.detect_preferred_package_manager(project_path, project_type)

        if not manager:
            return PackageManagerResult(
                success=False,
                message="没有找到可用的包管理器",
                command="",
                error="No available package manager"
            )

        if not manager.is_available():
            return PackageManagerResult(
                success=False,
                message=f"{manager.name} 命令不可用",
                command="",
                error=f"{manager.name} command not found"
            )

        # 执行卸载
        return manager.uninstall(package_name, global_uninstall=global_uninstall)
