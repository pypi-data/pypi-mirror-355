"""
Go project parser

Parse Go projects with go.mod and go.sum files
"""

import logging
import re
import subprocess
from pathlib import Path
from typing import List, Optional

from ..utils.file_utils import get_directory_size
from ..utils.toml_utils import safe_load_toml
from .base import (
    BaseParser,
    DependencyInfo,
    DependencyType,
    ProjectInfo,
    ProjectType,
)

logger = logging.getLogger(__name__)


class GoParser(BaseParser):
    """Go project parser"""

    @property
    def project_type(self) -> ProjectType:
        return ProjectType.GO

    @property
    def config_files(self) -> List[str]:
        return ["go.mod", "go.sum", "Gopkg.toml", "vendor.json"]

    def can_parse(self, project_path: Path) -> bool:
        """Check if this is a Go project"""
        # Primary check: go.mod file
        if (project_path / "go.mod").exists():
            return True

        # Secondary check: Go source files
        go_files = list(project_path.glob("*.go"))
        if go_files:
            return True

        # Legacy dependency managers
        for config_file in ["Gopkg.toml", "vendor.json"]:
            if (project_path / config_file).exists():
                return True

        return False

    def parse_project(self, project_path: Path) -> Optional[ProjectInfo]:
        """Parse Go project information"""
        if not self.can_parse(project_path):
            return None

        # Determine project name and config file
        project_name = project_path.name
        config_file = None

        # Priority order for config files
        for config_name in ["go.mod", "Gopkg.toml", "vendor.json"]:
            config_path = project_path / config_name
            if config_path.exists():
                config_file = config_path
                break

        # If no config file, create a virtual one for Go source files
        if not config_file:
            go_files = list(project_path.glob("*.go"))
            if go_files:
                config_file = go_files[0]  # Use first Go file as reference

        if not config_file:
            return None

        # Try to get project name from go.mod
        if config_file.name == "go.mod":
            project_name = self._get_name_from_go_mod(config_file) or project_name

        project_info = ProjectInfo(
            name=project_name,
            path=project_path,
            project_type=self.project_type,
            config_file=config_file,
            dependencies=[],
            metadata={
                "go_version": self._detect_go_version(project_path),
                "module_path": self._get_module_path(project_path),
                "has_vendor": (project_path / "vendor").exists(),
                "dependency_manager": self._detect_dependency_manager(project_path),
            },
        )

        # Parse dependencies
        project_info.dependencies = self.get_dependencies(project_info)

        # Calculate sizes
        self.calculate_dependency_sizes(project_info)

        return project_info

    def get_dependencies(self, project_info: ProjectInfo) -> List[DependencyInfo]:
        """Get Go project dependencies"""
        dependencies = []

        config_file = project_info.config_file

        if config_file.name == "go.mod":
            dependencies.extend(self._parse_go_mod(config_file))
        elif config_file.name == "Gopkg.toml":
            dependencies.extend(self._parse_gopkg_toml(config_file))

        return dependencies

    def calculate_dependency_sizes(self, project_info: ProjectInfo) -> None:
        """Calculate Go dependency sizes"""
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

        # Check Go module cache
        go_cache = self._get_go_cache_dir()
        if go_cache and go_cache.exists():
            for dependency in project_info.dependencies:
                # Go modules are stored in a specific format in cache
                cache_path = self._find_module_in_cache(dependency.name, go_cache)
                if cache_path:
                    dependency.size_bytes = get_directory_size(cache_path)
                    dependency.install_path = cache_path

        project_info.total_size_bytes = total_size

    def _parse_go_mod(self, go_mod_file: Path) -> List[DependencyInfo]:
        """Parse go.mod file"""
        dependencies = []

        try:
            with open(go_mod_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse require block
            require_pattern = r"require\s*\(\s*(.*?)\s*\)"
            require_match = re.search(require_pattern, content, re.DOTALL)

            if require_match:
                require_block = require_match.group(1)
                # Parse individual requirements
                req_pattern = r"([^\s]+)\s+([^\s]+)(?:\s+//\s*indirect)?"
                for match in re.finditer(req_pattern, require_block):
                    module_path = match.group(1)
                    version = match.group(2)
                    is_indirect = "indirect" in match.group(0)

                    dep_type = (
                        DependencyType.OPTIONAL
                        if is_indirect
                        else DependencyType.PRODUCTION
                    )

                    dep_info = DependencyInfo(
                        name=module_path,
                        version=version,
                        dependency_type=dep_type,
                    )
                    dependencies.append(dep_info)

            # Also parse single-line requires
            single_require_pattern = r"require\s+([^\s]+)\s+([^\s]+)"
            for match in re.finditer(single_require_pattern, content):
                module_path = match.group(1)
                version = match.group(2)

                dep_info = DependencyInfo(
                    name=module_path,
                    version=version,
                    dependency_type=DependencyType.PRODUCTION,
                )
                dependencies.append(dep_info)

        except Exception as e:
            logger.warning(f"Failed to parse go.mod: {go_mod_file}, error: {e}")

        return dependencies

    def _parse_gopkg_toml(self, gopkg_file: Path) -> List[DependencyInfo]:
        """Parse Gopkg.toml file (legacy dep tool)"""
        dependencies = []

        data = safe_load_toml(gopkg_file)
        if not data:
            return dependencies

        try:

            # Parse constraints
            constraints = data.get("constraint", [])
            for constraint in constraints:
                name = constraint.get("name", "")
                version = constraint.get("version", constraint.get("branch", ""))

                if name:
                    dep_info = DependencyInfo(
                        name=name,
                        version=version,
                        dependency_type=DependencyType.PRODUCTION,
                    )
                    dependencies.append(dep_info)

        except Exception as e:
            logger.warning(f"Failed to parse Gopkg.toml: {gopkg_file}, error: {e}")

        return dependencies

    def _get_name_from_go_mod(self, go_mod_file: Path) -> Optional[str]:
        """Get module name from go.mod"""
        try:
            with open(go_mod_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Find module declaration
            module_match = re.search(r"module\s+([^\s]+)", content)
            if module_match:
                module_path = module_match.group(1)
                # Extract last part as project name
                return module_path.split("/")[-1]

        except Exception:
            pass
        return None

    def _get_module_path(self, project_path: Path) -> Optional[str]:
        """Get full module path from go.mod"""
        go_mod_file = project_path / "go.mod"
        if not go_mod_file.exists():
            return None

        try:
            with open(go_mod_file, "r", encoding="utf-8") as f:
                content = f.read()

            module_match = re.search(r"module\s+([^\s]+)", content)
            if module_match:
                return module_match.group(1)

        except Exception:
            pass
        return None

    def _detect_go_version(self, project_path: Path) -> Optional[str]:
        """Detect Go version requirement"""
        go_mod_file = project_path / "go.mod"
        if not go_mod_file.exists():
            return None

        try:
            with open(go_mod_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Find go version declaration
            version_match = re.search(r"go\s+(\d+\.\d+)", content)
            if version_match:
                return version_match.group(1)

        except Exception:
            pass
        return None

    def _detect_dependency_manager(self, project_path: Path) -> str:
        """Detect dependency manager"""
        if (project_path / "go.mod").exists():
            return "go modules"
        elif (project_path / "Gopkg.toml").exists():
            return "dep"
        elif (project_path / "vendor.json").exists():
            return "govendor"
        elif (project_path / "vendor").exists():
            return "vendor"
        else:
            return "unknown"

    def _get_go_cache_dir(self) -> Optional[Path]:
        """Get Go module cache directory"""
        try:
            result = subprocess.run(
                ["go", "env", "GOMODCACHE"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return Path(result.stdout.strip())
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Fallback to default location
        default_cache = Path.home() / "go" / "pkg" / "mod"
        if default_cache.exists():
            return default_cache

        return None

    def _find_module_in_cache(
        self, module_name: str, cache_dir: Path
    ) -> Optional[Path]:
        """Find module in Go cache directory"""
        # Go modules are stored with encoded names
        # This is a simplified implementation
        try:
            # Convert module name to cache path format
            parts = module_name.split("/")
            if len(parts) >= 2:
                cache_path = cache_dir / parts[0] / "/".join(parts[1:])
                if cache_path.exists():
                    return cache_path
        except Exception:
            pass

        return None
