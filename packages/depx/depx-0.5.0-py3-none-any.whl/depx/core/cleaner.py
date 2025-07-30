"""
Dependency cleaner module

Provides safe dependency cleanup functionality
"""

import logging
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..parsers.base import DependencyInfo, PackageManagerType, ProjectInfo, ProjectType
from ..utils.file_utils import format_size

logger = logging.getLogger(__name__)


@dataclass
class CleanupResult:
    """Cleanup operation result"""

    success: bool
    cleaned_items: List[str]
    freed_space: int
    errors: List[str]

    def __post_init__(self):
        if self.cleaned_items is None:
            self.cleaned_items = []
        if self.errors is None:
            self.errors = []


@dataclass
class CleanupPlan:
    """Cleanup plan with items to be cleaned"""

    project_dependencies: List[Dict[str, Any]]
    global_caches: List[Dict[str, Any]]
    total_size: int

    def __post_init__(self):
        if self.project_dependencies is None:
            self.project_dependencies = []
        if self.global_caches is None:
            self.global_caches = []


class DependencyCleaner:
    """Dependency cleaner"""

    def __init__(self, dry_run: bool = True):
        """
        Initialize cleaner

        Args:
            dry_run: If True, only simulate cleanup without actual deletion
        """
        self.dry_run = dry_run

    def create_cleanup_plan(
        self, projects: List[ProjectInfo], cleanup_types: List[str] = None
    ) -> CleanupPlan:
        """
        Create a cleanup plan

        Args:
            projects: List of projects to analyze
            cleanup_types: Types of cleanup to include ['dev', 'cache', 'unused', 'large']

        Returns:
            Cleanup plan
        """
        if cleanup_types is None:
            cleanup_types = ["dev", "cache"]

        plan = CleanupPlan(project_dependencies=[], global_caches=[], total_size=0)

        # Analyze project dependencies
        for project in projects:
            if "dev" in cleanup_types:
                plan.project_dependencies.extend(self._find_dev_dependencies(project))

            if "large" in cleanup_types:
                plan.project_dependencies.extend(self._find_large_dependencies(project))

            if "unused" in cleanup_types:
                plan.project_dependencies.extend(
                    self._find_unused_dependencies(project)
                )

        # Analyze global caches
        if "cache" in cleanup_types:
            plan.global_caches.extend(self._find_global_caches())

        # Calculate total size
        plan.total_size = sum(
            item["size"] for item in plan.project_dependencies + plan.global_caches
        )

        return plan

    def execute_cleanup_plan(self, plan: CleanupPlan) -> CleanupResult:
        """
        Execute cleanup plan

        Args:
            plan: Cleanup plan to execute

        Returns:
            Cleanup result
        """
        result = CleanupResult(success=True, cleaned_items=[], freed_space=0, errors=[])

        # Clean project dependencies
        for item in plan.project_dependencies:
            try:
                if self._clean_project_dependency(item):
                    result.cleaned_items.append(f"Project dependency: {item['name']}")
                    result.freed_space += item["size"]
            except Exception as e:
                result.errors.append(f"Failed to clean {item['name']}: {e}")
                result.success = False

        # Clean global caches
        for item in plan.global_caches:
            try:
                if self._clean_global_cache(item):
                    result.cleaned_items.append(f"Global cache: {item['name']}")
                    result.freed_space += item["size"]
            except Exception as e:
                result.errors.append(f"Failed to clean cache {item['name']}: {e}")
                result.success = False

        return result

    def clean_project_dependencies(
        self, project: ProjectInfo, dependency_types: List[str] = None
    ) -> CleanupResult:
        """
        Clean specific project dependencies

        Args:
            project: Project to clean
            dependency_types: Types of dependencies to clean ['dev', 'all']

        Returns:
            Cleanup result
        """
        if dependency_types is None:
            dependency_types = ["dev"]

        result = CleanupResult(success=True, cleaned_items=[], freed_space=0, errors=[])

        if project.project_type == ProjectType.NODEJS:
            result = self._clean_nodejs_dependencies(project, dependency_types)
        elif project.project_type == ProjectType.PYTHON:
            result = self._clean_python_dependencies(project, dependency_types)

        return result

    def clean_global_caches(
        self, package_managers: List[PackageManagerType] = None
    ) -> CleanupResult:
        """
        Clean global package manager caches

        Args:
            package_managers: List of package managers to clean

        Returns:
            Cleanup result
        """
        if package_managers is None:
            package_managers = [PackageManagerType.NPM, PackageManagerType.PIP]

        result = CleanupResult(success=True, cleaned_items=[], freed_space=0, errors=[])

        for pm in package_managers:
            try:
                if pm == PackageManagerType.NPM:
                    cleaned = self._clean_npm_cache()
                elif pm == PackageManagerType.PIP:
                    cleaned = self._clean_pip_cache()
                elif pm == PackageManagerType.YARN:
                    cleaned = self._clean_yarn_cache()
                else:
                    continue

                if cleaned:
                    result.cleaned_items.append(f"{pm.value} cache")
                    # Note: Cache cleaning doesn't report exact size freed

            except Exception as e:
                result.errors.append(f"Failed to clean {pm.value} cache: {e}")
                result.success = False

        return result

    def _find_dev_dependencies(self, project: ProjectInfo) -> List[Dict[str, Any]]:
        """Find development dependencies"""
        dev_deps = []

        for dep in project.dependencies:
            if dep.dependency_type.value in ["development", "dev"]:
                dev_deps.append(
                    {
                        "name": dep.name,
                        "path": dep.install_path,
                        "size": dep.size_bytes,
                        "project": project.name,
                        "type": "dev_dependency",
                    }
                )

        return dev_deps

    def _find_large_dependencies(
        self, project: ProjectInfo, threshold: int = 50 * 1024 * 1024
    ) -> List[Dict[str, Any]]:
        """Find large dependencies (>50MB by default)"""
        large_deps = []

        for dep in project.dependencies:
            if dep.size_bytes > threshold:
                large_deps.append(
                    {
                        "name": dep.name,
                        "path": dep.install_path,
                        "size": dep.size_bytes,
                        "project": project.name,
                        "type": "large_dependency",
                    }
                )

        return large_deps

    def _find_unused_dependencies(self, project: ProjectInfo) -> List[Dict[str, Any]]:
        """Find potentially unused dependencies (basic heuristic)"""
        # This is a simplified implementation
        # In practice, you'd want more sophisticated analysis
        unused_deps = []

        # For now, just mark dependencies that don't have install paths
        for dep in project.dependencies:
            if not dep.install_path or not dep.install_path.exists():
                unused_deps.append(
                    {
                        "name": dep.name,
                        "path": dep.install_path,
                        "size": dep.size_bytes,
                        "project": project.name,
                        "type": "unused_dependency",
                    }
                )

        return unused_deps

    def _find_global_caches(self) -> List[Dict[str, Any]]:
        """Find global package manager caches"""
        caches = []

        # NPM cache
        npm_cache = self._get_npm_cache_path()
        if npm_cache and npm_cache.exists():
            from ..utils.file_utils import get_directory_size

            size = get_directory_size(npm_cache)
            caches.append(
                {
                    "name": "npm cache",
                    "path": npm_cache,
                    "size": size,
                    "type": "npm_cache",
                }
            )

        # Pip cache
        pip_cache = self._get_pip_cache_path()
        if pip_cache and pip_cache.exists():
            from ..utils.file_utils import get_directory_size

            size = get_directory_size(pip_cache)
            caches.append(
                {
                    "name": "pip cache",
                    "path": pip_cache,
                    "size": size,
                    "type": "pip_cache",
                }
            )

        return caches

    def _clean_project_dependency(self, item: Dict[str, Any]) -> bool:
        """Clean a single project dependency"""
        if self.dry_run:
            logger.info(
                f"[DRY RUN] Would clean: {item['name']} ({format_size(item['size'])})"
            )
            return True

        if item["path"] and Path(item["path"]).exists():
            try:
                if Path(item["path"]).is_dir():
                    shutil.rmtree(item["path"])
                else:
                    Path(item["path"]).unlink()
                logger.info(f"Cleaned: {item['name']} ({format_size(item['size'])})")
                return True
            except Exception as e:
                logger.error(f"Failed to clean {item['name']}: {e}")
                return False

        return False

    def _clean_global_cache(self, item: Dict[str, Any]) -> bool:
        """Clean a global cache"""
        if self.dry_run:
            logger.info(
                f"[DRY RUN] Would clean cache: {item['name']} ({format_size(item['size'])})"
            )
            return True

        cache_type = item["type"]

        if cache_type == "npm_cache":
            return self._clean_npm_cache()
        elif cache_type == "pip_cache":
            return self._clean_pip_cache()

        return False

    def _clean_nodejs_dependencies(
        self, project: ProjectInfo, dependency_types: List[str]
    ) -> CleanupResult:
        """Clean Node.js project dependencies"""
        result = CleanupResult(success=True, cleaned_items=[], freed_space=0, errors=[])

        if "all" in dependency_types:
            # Remove entire node_modules
            node_modules = project.path / "node_modules"
            if node_modules.exists():
                if self.dry_run:
                    logger.info(f"[DRY RUN] Would remove: {node_modules}")
                    result.cleaned_items.append("node_modules")
                    result.freed_space = project.total_size_bytes
                else:
                    try:
                        shutil.rmtree(node_modules)
                        result.cleaned_items.append("node_modules")
                        result.freed_space = project.total_size_bytes
                        logger.info(
                            f"Removed node_modules: {format_size(project.total_size_bytes)}"
                        )
                    except Exception as e:
                        result.errors.append(f"Failed to remove node_modules: {e}")
                        result.success = False

        return result

    def _clean_python_dependencies(
        self, project: ProjectInfo, dependency_types: List[str]
    ) -> CleanupResult:
        """Clean Python project dependencies"""
        result = CleanupResult(success=True, cleaned_items=[], freed_space=0, errors=[])

        if "all" in dependency_types:
            # Remove virtual environment
            venv_dirs = ["venv", ".venv", "env", ".env"]
            for venv_dir in venv_dirs:
                venv_path = project.path / venv_dir
                if venv_path.exists():
                    if self.dry_run:
                        logger.info(f"[DRY RUN] Would remove: {venv_path}")
                        result.cleaned_items.append(venv_dir)
                        result.freed_space = project.total_size_bytes
                    else:
                        try:
                            shutil.rmtree(venv_path)
                            result.cleaned_items.append(venv_dir)
                            result.freed_space = project.total_size_bytes
                            logger.info(
                                f"Removed {venv_dir}: {format_size(project.total_size_bytes)}"
                            )
                        except Exception as e:
                            result.errors.append(f"Failed to remove {venv_dir}: {e}")
                            result.success = False
                    break

        return result

    def _clean_npm_cache(self) -> bool:
        """Clean npm cache"""
        try:
            if self.dry_run:
                logger.info("[DRY RUN] Would run: npm cache clean --force")
                return True

            result = subprocess.run(
                ["npm", "cache", "clean", "--force"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Failed to clean npm cache: {e}")
            return False

    def _clean_pip_cache(self) -> bool:
        """Clean pip cache"""
        try:
            if self.dry_run:
                logger.info("[DRY RUN] Would run: pip cache purge")
                return True

            result = subprocess.run(
                ["pip", "cache", "purge"], capture_output=True, text=True, timeout=60
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Failed to clean pip cache: {e}")
            return False

    def _clean_yarn_cache(self) -> bool:
        """Clean yarn cache"""
        try:
            if self.dry_run:
                logger.info("[DRY RUN] Would run: yarn cache clean")
                return True

            result = subprocess.run(
                ["yarn", "cache", "clean"], capture_output=True, text=True, timeout=60
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Failed to clean yarn cache: {e}")
            return False

    def _get_npm_cache_path(self) -> Optional[Path]:
        """Get npm cache path"""
        try:
            result = subprocess.run(
                ["npm", "config", "get", "cache"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return Path(result.stdout.strip())
        except Exception:
            pass
        return None

    def _get_pip_cache_path(self) -> Optional[Path]:
        """Get pip cache path"""
        try:
            result = subprocess.run(
                ["pip", "cache", "dir"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return Path(result.stdout.strip())
        except Exception:
            pass
        return None
