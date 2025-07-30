"""
Node.js 项目解析器

解析 Node.js 项目的 package.json 和 node_modules
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..utils.file_utils import get_directory_size, safe_read_json
from .base import BaseParser, DependencyInfo, DependencyType, ProjectInfo, ProjectType

logger = logging.getLogger(__name__)


class NodeJSParser(BaseParser):
    """Node.js 项目解析器"""

    @property
    def project_type(self) -> ProjectType:
        return ProjectType.NODEJS

    @property
    def config_files(self) -> List[str]:
        return ["package.json"]

    def can_parse(self, project_path: Path) -> bool:
        """检查是否为 Node.js 项目"""
        package_json = project_path / "package.json"
        return package_json.exists() and package_json.is_file()

    def parse_project(self, project_path: Path) -> Optional[ProjectInfo]:
        """解析 Node.js 项目信息"""
        package_json_path = project_path / "package.json"

        if not self.can_parse(project_path):
            return None

        package_data = safe_read_json(package_json_path)
        if not package_data:
            logger.warning(f"无法解析 package.json: {package_json_path}")
            return None

        project_name = package_data.get("name", project_path.name)

        project_info = ProjectInfo(
            name=project_name,
            path=project_path,
            project_type=self.project_type,
            config_file=package_json_path,
            dependencies=[],
            metadata={
                "version": package_data.get("version"),
                "description": package_data.get("description"),
                "scripts": package_data.get("scripts", {}),
                "package_manager": self._detect_package_manager(project_path),
            },
        )

        # 解析依赖
        project_info.dependencies = self.get_dependencies(project_info)

        # 计算总大小
        self.calculate_dependency_sizes(project_info)

        return project_info

    def get_dependencies(self, project_info: ProjectInfo) -> List[DependencyInfo]:
        """获取 Node.js 项目的依赖信息"""
        package_data = safe_read_json(project_info.config_file)
        if not package_data:
            return []

        dependencies = []

        # 解析生产依赖
        prod_deps = package_data.get("dependencies", {})
        for name, version in prod_deps.items():
            dep_info = DependencyInfo(
                name=name, version=version, dependency_type=DependencyType.PRODUCTION
            )
            dependencies.append(dep_info)

        # 解析开发依赖
        dev_deps = package_data.get("devDependencies", {})
        for name, version in dev_deps.items():
            dep_info = DependencyInfo(
                name=name, version=version, dependency_type=DependencyType.DEVELOPMENT
            )
            dependencies.append(dep_info)

        # 解析可选依赖
        optional_deps = package_data.get("optionalDependencies", {})
        for name, version in optional_deps.items():
            dep_info = DependencyInfo(
                name=name, version=version, dependency_type=DependencyType.OPTIONAL
            )
            dependencies.append(dep_info)

        # 解析同级依赖
        peer_deps = package_data.get("peerDependencies", {})
        for name, version in peer_deps.items():
            dep_info = DependencyInfo(
                name=name, version=version, dependency_type=DependencyType.PEER
            )
            dependencies.append(dep_info)

        # 获取实际安装的依赖信息
        self._enrich_with_installed_info(project_info, dependencies)

        return dependencies

    def calculate_dependency_sizes(self, project_info: ProjectInfo) -> None:
        """计算 Node.js 依赖的磁盘占用"""
        node_modules_path = project_info.path / "node_modules"

        if not node_modules_path.exists():
            logger.info(f"node_modules 不存在: {node_modules_path}")
            return

        total_size = 0

        for dependency in project_info.dependencies:
            dep_path = node_modules_path / dependency.name
            if dep_path.exists() and dep_path.is_dir():
                size = get_directory_size(dep_path)
                dependency.size_bytes = size
                dependency.install_path = dep_path
                total_size += size
            else:
                logger.debug(f"依赖目录不存在: {dep_path}")

        project_info.total_size_bytes = total_size

    def _detect_package_manager(self, project_path: Path) -> str:
        """检测使用的包管理器"""
        if (project_path / "yarn.lock").exists():
            return "yarn"
        elif (project_path / "pnpm-lock.yaml").exists():
            return "pnpm"
        elif (project_path / "package-lock.json").exists():
            return "npm"
        else:
            return "unknown"

    def _enrich_with_installed_info(
        self, project_info: ProjectInfo, dependencies: List[DependencyInfo]
    ) -> None:
        """丰富依赖信息，添加实际安装的版本等信息"""
        node_modules_path = project_info.path / "node_modules"

        if not node_modules_path.exists():
            return

        for dependency in dependencies:
            dep_package_json = node_modules_path / dependency.name / "package.json"
            if dep_package_json.exists():
                dep_data = safe_read_json(dep_package_json)
                if dep_data:
                    dependency.installed_version = dep_data.get("version")
                    dependency.description = dep_data.get("description")
