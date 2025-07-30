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
    OutdatedPackage,
    PackageManagerResult,
    PipManager,
    SearchResult,
    UpdateResult,
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

    def _is_package_manager_compatible(
        self, manager_type: PackageManagerType, project_type: Optional[ProjectType]
    ) -> bool:
        """
        检查包管理器是否与项目类型兼容

        Args:
            manager_type: 包管理器类型
            project_type: 项目类型

        Returns:
            是否兼容
        """
        if not project_type:
            return True  # 如果无法检测项目类型，允许使用任何包管理器

        compatibility_map = {
            PackageManagerType.NPM: [ProjectType.NODEJS],
            PackageManagerType.YARN: [ProjectType.NODEJS],
            PackageManagerType.PIP: [ProjectType.PYTHON],
            PackageManagerType.CARGO: [ProjectType.RUST],
        }

        compatible_types = compatibility_map.get(manager_type, [])
        return project_type in compatible_types

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

                # 检查包管理器与项目类型的兼容性
                if not self._is_package_manager_compatible(manager_type, project_type):
                    return PackageManagerResult(
                        success=False,
                        message=f"包管理器 {package_manager} 与项目类型 {project_type.value if project_type else 'unknown'} 不兼容。请在对应的项目目录中使用，或使用 --type 参数指定正确的项目类型。",
                        command="",
                        error=f"Package manager {package_manager} is not compatible with project type {project_type.value if project_type else 'unknown'}",
                    )

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

    def search_package(
        self,
        package_name: str,
        project_path: Optional[Path] = None,
        project_type: Optional[ProjectType] = None,
        package_manager: Optional[str] = None,
        limit: int = 10,
        search_all: bool = False,
    ) -> List[SearchResult]:
        """
        搜索包

        Args:
            package_name: 包名或关键词
            project_path: 项目路径
            project_type: 项目类型
            package_manager: 指定的包管理器
            limit: 限制结果数量
            search_all: 是否搜索所有可用的包管理器

        Returns:
            搜索结果列表
        """
        # 如果指定了包管理器，只搜索该包管理器
        if package_manager:
            try:
                manager_type = PackageManagerType(package_manager.lower())
                manager_class = self.package_managers.get(manager_type)
                if manager_class:
                    manager = manager_class(project_path)
                    if manager.is_available():
                        return manager.search(package_name, limit=limit)
            except ValueError:
                pass
            return []

        # 如果启用搜索所有包管理器
        if search_all:
            all_results = []
            for manager_type, manager_class in self.package_managers.items():
                manager = manager_class(project_path)
                if manager.is_available():
                    try:
                        results = manager.search(package_name, limit=limit)
                        all_results.extend(results)
                    except Exception as e:
                        logger.debug(f"搜索 {manager_type.value} 失败: {e}")
            return all_results

        # 默认行为：根据项目类型选择包管理器
        if not project_type and project_path:
            project_type = self.detect_project_type(project_path)

        if project_type:
            manager = self.detect_preferred_package_manager(project_path, project_type)
            if manager and manager.is_available():
                return manager.search(package_name, limit=limit)

        return []

    def check_outdated_packages(
        self,
        project_path: Optional[Path] = None,
        project_type: Optional[ProjectType] = None,
        package_manager: Optional[str] = None,
    ) -> List[OutdatedPackage]:
        """
        检查过时的包

        Args:
            project_path: 项目路径
            project_type: 项目类型
            package_manager: 指定的包管理器

        Returns:
            过时包列表
        """
        # 如果没有指定项目类型，尝试检测
        if not project_type and project_path:
            project_type = self.detect_project_type(project_path)

        if not project_type:
            return []

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
                return []
        else:
            # 自动检测包管理器
            manager = self.detect_preferred_package_manager(project_path, project_type)

        if not manager or not manager.is_available():
            return []

        # 检查过时的包
        return manager.check_outdated()

    def update_packages(
        self,
        package_name: Optional[str] = None,
        project_path: Optional[Path] = None,
        project_type: Optional[ProjectType] = None,
        package_manager: Optional[str] = None,
        dev: bool = False,
    ) -> UpdateResult:
        """
        更新包

        Args:
            package_name: 包名，None 表示更新所有包
            project_path: 项目路径
            project_type: 项目类型
            package_manager: 指定的包管理器
            dev: 是否包括开发依赖

        Returns:
            更新结果
        """
        # 如果没有指定项目类型，尝试检测
        if not project_type and project_path:
            project_type = self.detect_project_type(project_path)

        if not project_type:
            return UpdateResult(
                success=False,
                message="无法检测项目类型，请使用 --type 参数指定",
                updated_packages=[],
                error="Unknown project type",
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
                return UpdateResult(
                    success=False,
                    message=f"不支持的包管理器: {package_manager}",
                    updated_packages=[],
                    error="Unsupported package manager",
                )
        else:
            # 自动检测包管理器
            manager = self.detect_preferred_package_manager(project_path, project_type)

        if not manager:
            return UpdateResult(
                success=False,
                message="没有找到可用的包管理器",
                updated_packages=[],
                error="No available package manager",
            )

        if not manager.is_available():
            return UpdateResult(
                success=False,
                message=f"{manager.name} 命令不可用",
                updated_packages=[],
                error=f"{manager.name} command not found",
            )

        # 执行更新
        return manager.update_package(package_name, dev=dev)
