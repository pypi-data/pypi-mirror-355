"""
依赖分析器模块

提供依赖统计、分析和报告功能
"""

import logging
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from ..parsers.base import DependencyType, ProjectInfo, ProjectType
from ..utils.file_utils import format_size

logger = logging.getLogger(__name__)


@dataclass
class DependencyStats:
    """依赖统计信息"""

    total_dependencies: int = 0
    total_size_bytes: int = 0
    by_type: Dict[DependencyType, int] = None
    by_project_type: Dict[ProjectType, int] = None
    largest_dependencies: List[Tuple[str, int]] = None  # (name, size)

    def __post_init__(self):
        if self.by_type is None:
            self.by_type = {}
        if self.by_project_type is None:
            self.by_project_type = {}
        if self.largest_dependencies is None:
            self.largest_dependencies = []


@dataclass
class ProjectStats:
    """项目统计信息"""

    total_projects: int = 0
    by_type: Dict[ProjectType, int] = None
    total_size_bytes: int = 0
    largest_projects: List[Tuple[str, int]] = None  # (name, size)

    def __post_init__(self):
        if self.by_type is None:
            self.by_type = {}
        if self.largest_projects is None:
            self.largest_projects = []


class DependencyAnalyzer:
    """依赖分析器"""

    def __init__(self):
        """初始化分析器"""

    def analyze_projects(self, projects: List[ProjectInfo]) -> Dict[str, Any]:
        """
        分析项目列表，生成综合报告

        Args:
            projects: 项目信息列表

        Returns:
            分析报告字典
        """
        if not projects:
            return self._empty_report()

        logger.info(f"开始分析 {len(projects)} 个项目")

        # 统计项目信息
        project_stats = self._analyze_projects(projects)

        # 统计依赖信息
        dependency_stats = self._analyze_dependencies(projects)

        # 查找重复依赖
        duplicate_deps = self._find_duplicate_dependencies(projects)

        # 生成清理建议
        cleanup_suggestions = self._generate_cleanup_suggestions(projects)

        report = {
            "summary": {
                "total_projects": len(projects),
                "total_dependencies": dependency_stats.total_dependencies,
                "total_size": dependency_stats.total_size_bytes,
                "total_size_formatted": format_size(dependency_stats.total_size_bytes),
            },
            "project_stats": project_stats,
            "dependency_stats": dependency_stats,
            "duplicate_dependencies": duplicate_deps,
            "cleanup_suggestions": cleanup_suggestions,
        }

        logger.info("分析完成")
        return report

    def _analyze_projects(self, projects: List[ProjectInfo]) -> ProjectStats:
        """分析项目统计信息"""
        stats = ProjectStats()
        stats.total_projects = len(projects)

        # 按类型统计
        type_counter = Counter(project.project_type for project in projects)
        stats.by_type = dict(type_counter)

        # 计算总大小和最大项目
        project_sizes = []
        total_size = 0

        for project in projects:
            size = project.total_size_bytes
            total_size += size
            project_sizes.append((project.name, size))

        stats.total_size_bytes = total_size

        # 排序获取最大的项目
        project_sizes.sort(key=lambda x: x[1], reverse=True)
        stats.largest_projects = project_sizes[:10]  # 前10个最大的项目

        return stats

    def _analyze_dependencies(self, projects: List[ProjectInfo]) -> DependencyStats:
        """分析依赖统计信息"""
        stats = DependencyStats()

        all_dependencies = []
        for project in projects:
            all_dependencies.extend(project.dependencies)

        stats.total_dependencies = len(all_dependencies)

        # 按类型统计
        type_counter = Counter(dep.dependency_type for dep in all_dependencies)
        stats.by_type = dict(type_counter)

        # 按项目类型统计
        project_type_deps = defaultdict(int)
        for project in projects:
            project_type_deps[project.project_type] += len(project.dependencies)
        stats.by_project_type = dict(project_type_deps)

        # 计算总大小和最大依赖
        dep_sizes = []
        total_size = 0

        for dep in all_dependencies:
            size = dep.size_bytes
            total_size += size
            if size > 0:  # 只包含有大小信息的依赖
                dep_sizes.append((dep.name, size))

        stats.total_size_bytes = total_size

        # 排序获取最大的依赖
        dep_sizes.sort(key=lambda x: x[1], reverse=True)
        stats.largest_dependencies = dep_sizes[:20]  # 前20个最大的依赖

        return stats

    def _find_duplicate_dependencies(
        self, projects: List[ProjectInfo]
    ) -> Dict[str, Any]:
        """查找重复的依赖"""
        dep_projects = defaultdict(list)  # dependency_name -> [project_names]
        dep_versions = defaultdict(set)  # dependency_name -> {versions}
        dep_sizes = defaultdict(list)  # dependency_name -> [sizes]

        for project in projects:
            for dep in project.dependencies:
                dep_projects[dep.name].append(project.name)
                if dep.installed_version:
                    dep_versions[dep.name].add(dep.installed_version)
                if dep.size_bytes > 0:
                    dep_sizes[dep.name].append(dep.size_bytes)

        # 找出在多个项目中出现的依赖
        duplicates = []
        for dep_name, project_names in dep_projects.items():
            if len(project_names) > 1:
                versions = list(dep_versions.get(dep_name, set()))
                sizes = dep_sizes.get(dep_name, [])
                total_size = sum(sizes)

                duplicates.append(
                    {
                        "name": dep_name,
                        "projects": project_names,
                        "project_count": len(project_names),
                        "versions": versions,
                        "version_count": len(versions),
                        "total_size_bytes": total_size,
                        "total_size_formatted": format_size(total_size),
                        "potential_savings": total_size - max(sizes) if sizes else 0,
                    }
                )

        # 按潜在节省空间排序
        duplicates.sort(key=lambda x: x["potential_savings"], reverse=True)

        return {
            "count": len(duplicates),
            "dependencies": duplicates[:50],  # 前50个重复依赖
            "total_potential_savings": sum(d["potential_savings"] for d in duplicates),
        }

    def _generate_cleanup_suggestions(
        self, projects: List[ProjectInfo]
    ) -> List[Dict[str, Any]]:
        """生成清理建议"""
        suggestions = []

        # 建议1: 清理大型依赖
        large_deps = []
        for project in projects:
            for dep in project.dependencies:
                if dep.size_bytes > 100 * 1024 * 1024:  # 大于100MB
                    large_deps.append(
                        {
                            "project": project.name,
                            "dependency": dep.name,
                            "size": dep.size_bytes,
                            "size_formatted": format_size(dep.size_bytes),
                        }
                    )

        if large_deps:
            large_deps.sort(key=lambda x: x["size"], reverse=True)
            suggestions.append(
                {
                    "type": "large_dependencies",
                    "title": "清理大型依赖",
                    "description": "以下依赖占用空间较大，考虑是否真的需要",
                    "items": large_deps[:10],
                    "potential_savings": sum(d["size"] for d in large_deps),
                }
            )

        # 建议2: 清理开发依赖
        dev_deps = []
        for project in projects:
            dev_dep_size = sum(
                dep.size_bytes
                for dep in project.dependencies
                if dep.dependency_type == DependencyType.DEVELOPMENT
            )
            if dev_dep_size > 0:
                dev_deps.append(
                    {
                        "project": project.name,
                        "size": dev_dep_size,
                        "size_formatted": format_size(dev_dep_size),
                    }
                )

        if dev_deps:
            dev_deps.sort(key=lambda x: x["size"], reverse=True)
            suggestions.append(
                {
                    "type": "development_dependencies",
                    "title": "清理开发依赖",
                    "description": "开发依赖在生产环境中不需要，可以考虑清理",
                    "items": dev_deps,
                    "potential_savings": sum(d["size"] for d in dev_deps),
                }
            )

        return suggestions

    def _empty_report(self) -> Dict[str, Any]:
        """返回空报告"""
        return {
            "summary": {
                "total_projects": 0,
                "total_dependencies": 0,
                "total_size": 0,
                "total_size_formatted": "0 B",
            },
            "project_stats": ProjectStats(),
            "dependency_stats": DependencyStats(),
            "duplicate_dependencies": {
                "count": 0,
                "dependencies": [],
                "total_potential_savings": 0,
            },
            "cleanup_suggestions": [],
        }
