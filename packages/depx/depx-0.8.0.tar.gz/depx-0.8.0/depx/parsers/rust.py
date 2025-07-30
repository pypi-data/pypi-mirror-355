"""
Rust project parser

Parse Rust projects with Cargo.toml and Cargo.lock files
"""

import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

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


class RustParser(BaseParser):
    """Rust project parser"""

    @property
    def project_type(self) -> ProjectType:
        return ProjectType.RUST

    @property
    def config_files(self) -> List[str]:
        return ["Cargo.toml", "Cargo.lock"]

    def can_parse(self, project_path: Path) -> bool:
        """Check if this is a Rust project"""
        return (project_path / "Cargo.toml").exists()

    def parse_project(self, project_path: Path) -> Optional[ProjectInfo]:
        """Parse Rust project information"""
        if not self.can_parse(project_path):
            return None

        cargo_toml = project_path / "Cargo.toml"
        project_name = self._get_name_from_cargo_toml(cargo_toml) or project_path.name

        project_info = ProjectInfo(
            name=project_name,
            path=project_path,
            project_type=self.project_type,
            config_file=cargo_toml,
            dependencies=[],
            metadata={
                "rust_version": self._detect_rust_version(project_path),
                "edition": self._get_edition(cargo_toml),
                "workspace": self._is_workspace(cargo_toml),
                "has_lock": (project_path / "Cargo.lock").exists(),
            },
        )

        # Parse dependencies
        project_info.dependencies = self.get_dependencies(project_info)

        # Calculate sizes
        self.calculate_dependency_sizes(project_info)

        return project_info

    def get_dependencies(self, project_info: ProjectInfo) -> List[DependencyInfo]:
        """Get Rust project dependencies"""
        dependencies = []

        cargo_toml = project_info.config_file
        dependencies.extend(self._parse_cargo_toml(cargo_toml))

        # Also parse Cargo.lock if available for exact versions
        cargo_lock = project_info.path / "Cargo.lock"
        if cargo_lock.exists():
            lock_deps = self._parse_cargo_lock(cargo_lock)
            self._merge_lock_info(dependencies, lock_deps)

        return dependencies

    def calculate_dependency_sizes(self, project_info: ProjectInfo) -> None:
        """Calculate Rust dependency sizes"""
        total_size = 0

        # Check target directory
        target_dir = project_info.path / "target"
        if target_dir.exists():
            target_size = get_directory_size(target_dir)
            total_size += target_size

        # Check Cargo registry cache
        cargo_cache = self._get_cargo_cache_dir()
        if cargo_cache and cargo_cache.exists():
            for dependency in project_info.dependencies:
                cache_path = self._find_crate_in_cache(dependency.name, cargo_cache)
                if cache_path:
                    dependency.size_bytes = get_directory_size(cache_path)
                    dependency.install_path = cache_path

        project_info.total_size_bytes = total_size

    def _parse_cargo_toml(self, cargo_toml: Path) -> List[DependencyInfo]:
        """Parse Cargo.toml dependencies"""
        dependencies = []

        data = safe_load_toml(cargo_toml)
        if not data:
            return dependencies

        try:

            # Parse regular dependencies
            deps = data.get("dependencies", {})
            for name, spec in deps.items():
                version = self._extract_version(spec)
                dep_info = DependencyInfo(
                    name=name,
                    version=version,
                    dependency_type=DependencyType.PRODUCTION,
                )
                dependencies.append(dep_info)

            # Parse dev dependencies
            dev_deps = data.get("dev-dependencies", {})
            for name, spec in dev_deps.items():
                version = self._extract_version(spec)
                dep_info = DependencyInfo(
                    name=name,
                    version=version,
                    dependency_type=DependencyType.DEVELOPMENT,
                )
                dependencies.append(dep_info)

            # Parse build dependencies
            build_deps = data.get("build-dependencies", {})
            for name, spec in build_deps.items():
                version = self._extract_version(spec)
                dep_info = DependencyInfo(
                    name=name,
                    version=version,
                    dependency_type=DependencyType.DEVELOPMENT,
                )
                dependencies.append(dep_info)

        except Exception as e:
            logger.warning(f"Failed to parse Cargo.toml: {cargo_toml}, error: {e}")

        return dependencies

    def _parse_cargo_lock(self, cargo_lock: Path) -> Dict[str, str]:
        """Parse Cargo.lock for exact versions"""
        lock_deps = {}

        data = safe_load_toml(cargo_lock)
        if not data:
            return lock_deps

        try:

            packages = data.get("package", [])
            for package in packages:
                name = package.get("name")
                version = package.get("version")
                if name and version:
                    lock_deps[name] = version

        except Exception as e:
            logger.warning(f"Failed to parse Cargo.lock: {cargo_lock}, error: {e}")

        return lock_deps

    def _extract_version(self, spec) -> str:
        """Extract version from dependency specification"""
        if isinstance(spec, str):
            return spec
        elif isinstance(spec, dict):
            return spec.get("version", "")
        else:
            return ""

    def _merge_lock_info(
        self, dependencies: List[DependencyInfo], lock_deps: Dict[str, str]
    ) -> None:
        """Merge exact versions from Cargo.lock"""
        for dep in dependencies:
            if dep.name in lock_deps:
                dep.installed_version = lock_deps[dep.name]

    def _get_name_from_cargo_toml(self, cargo_toml: Path) -> Optional[str]:
        """Get package name from Cargo.toml"""
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                return None

        try:
            with open(cargo_toml, "rb") as f:
                data = tomllib.load(f)

            package = data.get("package", {})
            return package.get("name")

        except Exception:
            pass
        return None

    def _get_edition(self, cargo_toml: Path) -> Optional[str]:
        """Get Rust edition from Cargo.toml"""
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                return None

        try:
            with open(cargo_toml, "rb") as f:
                data = tomllib.load(f)

            package = data.get("package", {})
            return package.get("edition")

        except Exception:
            pass
        return None

    def _is_workspace(self, cargo_toml: Path) -> bool:
        """Check if this is a Cargo workspace"""
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                return False

        try:
            with open(cargo_toml, "rb") as f:
                data = tomllib.load(f)

            return "workspace" in data

        except Exception:
            pass
        return False

    def _detect_rust_version(self, project_path: Path) -> Optional[str]:
        """Detect Rust version requirement"""
        # Check rust-toolchain file
        toolchain_file = project_path / "rust-toolchain"
        if toolchain_file.exists():
            try:
                with open(toolchain_file, "r") as f:
                    return f.read().strip()
            except Exception:
                pass

        # Check rust-toolchain.toml
        toolchain_toml = project_path / "rust-toolchain.toml"
        if toolchain_toml.exists():
            try:
                import tomllib
            except ImportError:
                try:
                    import tomli as tomllib
                except ImportError:
                    return None

            try:
                with open(toolchain_toml, "rb") as f:
                    data = tomllib.load(f)
                return data.get("toolchain", {}).get("channel")
            except Exception:
                pass

        return None

    def _get_cargo_cache_dir(self) -> Optional[Path]:
        """Get Cargo cache directory"""
        try:
            result = subprocess.run(
                ["cargo", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                # Cargo cache is typically in ~/.cargo
                cargo_home = Path.home() / ".cargo"
                if cargo_home.exists():
                    return cargo_home / "registry"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return None

    def _find_crate_in_cache(self, crate_name: str, cache_dir: Path) -> Optional[Path]:
        """Find crate in Cargo cache directory"""
        # Cargo stores crates in registry/src/index.crates.io-*/crate_name-version
        try:
            src_dirs = list(cache_dir.glob("src/index.crates.io-*"))
            for src_dir in src_dirs:
                crate_dirs = list(src_dir.glob(f"{crate_name}-*"))
                if crate_dirs:
                    # Return the first match (could be improved to find latest version)
                    return crate_dirs[0]
        except Exception:
            pass

        return None
