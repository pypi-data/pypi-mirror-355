"""
PHP project parser

Parse PHP projects with composer.json and composer.lock files
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..utils.file_utils import get_directory_size, safe_read_json
from .base import (
    BaseParser,
    DependencyInfo,
    DependencyType,
    ProjectInfo,
    ProjectType,
)

logger = logging.getLogger(__name__)


class PHPParser(BaseParser):
    """PHP project parser"""

    @property
    def project_type(self) -> ProjectType:
        return ProjectType.PHP

    @property
    def config_files(self) -> List[str]:
        return ["composer.json", "composer.lock"]

    def can_parse(self, project_path: Path) -> bool:
        """Check if this is a PHP project"""
        # Primary check: composer.json
        if (project_path / "composer.json").exists():
            return True

        # Secondary check: PHP files
        php_files = list(project_path.glob("*.php"))
        if php_files:
            return True

        return False

    def parse_project(self, project_path: Path) -> Optional[ProjectInfo]:
        """Parse PHP project information"""
        if not self.can_parse(project_path):
            return None

        # Determine project name and config file
        project_name = project_path.name
        config_file = None

        composer_json = project_path / "composer.json"
        if composer_json.exists():
            config_file = composer_json
            project_name = self._get_name_from_composer(composer_json) or project_name
        else:
            # Use first PHP file as reference
            php_files = list(project_path.glob("*.php"))
            if php_files:
                config_file = php_files[0]

        if not config_file:
            return None

        project_info = ProjectInfo(
            name=project_name,
            path=project_path,
            project_type=self.project_type,
            config_file=config_file,
            dependencies=[],
            metadata={
                "php_version": self._detect_php_version(project_path),
                "framework": self._detect_framework(project_path),
                "has_vendor": (project_path / "vendor").exists(),
                "has_lock": (project_path / "composer.lock").exists(),
            },
        )

        # Parse dependencies
        project_info.dependencies = self.get_dependencies(project_info)

        # Calculate sizes
        self.calculate_dependency_sizes(project_info)

        return project_info

    def get_dependencies(self, project_info: ProjectInfo) -> List[DependencyInfo]:
        """Get PHP project dependencies"""
        dependencies = []

        composer_json = project_info.path / "composer.json"
        if composer_json.exists():
            dependencies.extend(self._parse_composer_json(composer_json))

            # Also parse composer.lock if available for exact versions
            composer_lock = project_info.path / "composer.lock"
            if composer_lock.exists():
                lock_deps = self._parse_composer_lock(composer_lock)
                self._merge_lock_info(dependencies, lock_deps)

        return dependencies

    def calculate_dependency_sizes(self, project_info: ProjectInfo) -> None:
        """Calculate PHP dependency sizes"""
        total_size = 0

        # Check vendor directory
        vendor_dir = project_info.path / "vendor"
        if vendor_dir.exists():
            vendor_size = get_directory_size(vendor_dir)
            total_size += vendor_size

            # Update dependency sizes based on vendor directory
            for dependency in project_info.dependencies:
                vendor_path = vendor_dir / dependency.name
                if vendor_path.exists():
                    dependency.size_bytes = get_directory_size(vendor_path)
                    dependency.install_path = vendor_path

        project_info.total_size_bytes = total_size

    def _parse_composer_json(self, composer_json: Path) -> List[DependencyInfo]:
        """Parse composer.json dependencies"""
        dependencies = []

        data = safe_read_json(composer_json)
        if not data:
            return dependencies

        # Parse regular dependencies
        require = data.get("require", {})
        for name, version in require.items():
            # Skip PHP itself
            if name == "php":
                continue

            dep_info = DependencyInfo(
                name=name,
                version=version,
                dependency_type=DependencyType.PRODUCTION,
            )
            dependencies.append(dep_info)

        # Parse dev dependencies
        require_dev = data.get("require-dev", {})
        for name, version in require_dev.items():
            # Skip PHP itself
            if name == "php":
                continue

            dep_info = DependencyInfo(
                name=name,
                version=version,
                dependency_type=DependencyType.DEVELOPMENT,
            )
            dependencies.append(dep_info)

        return dependencies

    def _parse_composer_lock(self, composer_lock: Path) -> Dict[str, str]:
        """Parse composer.lock for exact versions"""
        lock_deps = {}

        data = safe_read_json(composer_lock)
        if not data:
            return lock_deps

        # Parse packages
        packages = data.get("packages", [])
        for package in packages:
            name = package.get("name")
            version = package.get("version")
            if name and version:
                lock_deps[name] = version

        # Parse dev packages
        packages_dev = data.get("packages-dev", [])
        for package in packages_dev:
            name = package.get("name")
            version = package.get("version")
            if name and version:
                lock_deps[name] = version

        return lock_deps

    def _merge_lock_info(
        self, dependencies: List[DependencyInfo], lock_deps: Dict[str, str]
    ) -> None:
        """Merge exact versions from composer.lock"""
        for dep in dependencies:
            if dep.name in lock_deps:
                dep.installed_version = lock_deps[dep.name]

    def _get_name_from_composer(self, composer_json: Path) -> Optional[str]:
        """Get package name from composer.json"""
        data = safe_read_json(composer_json)
        if not data:
            return None

        name = data.get("name")
        if name:
            # Extract package name from vendor/package format
            parts = name.split("/")
            if len(parts) == 2:
                return parts[1]
            return name

        return None

    def _detect_php_version(self, project_path: Path) -> Optional[str]:
        """Detect PHP version requirement"""
        composer_json = project_path / "composer.json"
        if composer_json.exists():
            data = safe_read_json(composer_json)
            if data:
                require = data.get("require", {})
                php_version = require.get("php")
                if php_version:
                    return php_version

        # Check .php-version file
        php_version_file = project_path / ".php-version"
        if php_version_file.exists():
            try:
                with open(php_version_file, "r") as f:
                    return f.read().strip()
            except Exception:
                pass

        return None

    def _detect_framework(self, project_path: Path) -> Optional[str]:
        """Detect PHP framework"""
        composer_json = project_path / "composer.json"
        if not composer_json.exists():
            return None

        data = safe_read_json(composer_json)
        if not data:
            return None

        require = data.get("require", {})

        # Check for common frameworks
        frameworks = {
            "laravel/framework": "Laravel",
            "symfony/symfony": "Symfony",
            "symfony/framework-bundle": "Symfony",
            "codeigniter4/framework": "CodeIgniter",
            "cakephp/cakephp": "CakePHP",
            "yiisoft/yii2": "Yii2",
            "zendframework/zendframework": "Zend",
            "laminas/laminas-mvc": "Laminas",
            "slim/slim": "Slim",
            "phalcon/cphalcon": "Phalcon",
        }

        for package, framework in frameworks.items():
            if package in require:
                return framework

        # Check for WordPress
        if (project_path / "wp-config.php").exists():
            return "WordPress"

        # Check for Drupal
        if (project_path / "core" / "drupal.info.yml").exists():
            return "Drupal"

        return None
