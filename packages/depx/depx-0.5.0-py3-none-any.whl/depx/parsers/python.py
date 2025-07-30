"""
Python project parser

Parse Python projects with requirements.txt, setup.py, pyproject.toml
"""

import logging
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..utils.file_utils import get_directory_size, safe_read_json
from .base import BaseParser, DependencyInfo, DependencyType, ProjectInfo, ProjectType

logger = logging.getLogger(__name__)


class PythonParser(BaseParser):
    """Python project parser"""

    @property
    def project_type(self) -> ProjectType:
        return ProjectType.PYTHON

    @property
    def config_files(self) -> List[str]:
        return [
            "requirements.txt",
            "setup.py",
            "pyproject.toml",
            "Pipfile",
            "environment.yml",
        ]

    def can_parse(self, project_path: Path) -> bool:
        """Check if this is a Python project"""
        for config_file in self.config_files:
            if (project_path / config_file).exists():
                return True
        return False

    def parse_project(self, project_path: Path) -> Optional[ProjectInfo]:
        """Parse Python project information"""
        if not self.can_parse(project_path):
            return None

        # Determine project name and config file
        project_name = project_path.name
        config_file = None

        # Priority order for config files
        for config_name in [
            "pyproject.toml",
            "setup.py",
            "requirements.txt",
            "Pipfile",
        ]:
            config_path = project_path / config_name
            if config_path.exists():
                config_file = config_path
                break

        if not config_file:
            return None

        # Try to get project name from config
        if config_file.name == "pyproject.toml":
            project_name = self._get_name_from_pyproject(config_file) or project_name
        elif config_file.name == "setup.py":
            project_name = self._get_name_from_setup_py(config_file) or project_name

        project_info = ProjectInfo(
            name=project_name,
            path=project_path,
            project_type=self.project_type,
            config_file=config_file,
            dependencies=[],
            metadata={
                "python_version": self._detect_python_version(project_path),
                "virtual_env": self._detect_virtual_env(project_path),
                "package_manager": self._detect_package_manager(project_path),
            },
        )

        # Parse dependencies
        project_info.dependencies = self.get_dependencies(project_info)

        # Calculate sizes
        self.calculate_dependency_sizes(project_info)

        return project_info

    def get_dependencies(self, project_info: ProjectInfo) -> List[DependencyInfo]:
        """Get Python project dependencies"""
        dependencies = []

        config_file = project_info.config_file

        if config_file.name == "requirements.txt":
            dependencies.extend(self._parse_requirements_txt(config_file))
        elif config_file.name == "pyproject.toml":
            dependencies.extend(self._parse_pyproject_toml(config_file))
        elif config_file.name == "setup.py":
            dependencies.extend(self._parse_setup_py(config_file))
        elif config_file.name == "Pipfile":
            dependencies.extend(self._parse_pipfile(config_file))

        # Also check for additional requirements files
        for req_file in [
            "requirements-dev.txt",
            "dev-requirements.txt",
            "test-requirements.txt",
        ]:
            req_path = project_info.path / req_file
            if req_path.exists():
                dev_deps = self._parse_requirements_txt(
                    req_path, DependencyType.DEVELOPMENT
                )
                dependencies.extend(dev_deps)

        return dependencies

    def calculate_dependency_sizes(self, project_info: ProjectInfo) -> None:
        """Calculate Python dependency sizes"""
        # Look for virtual environment directories
        venv_dirs = ["venv", ".venv", "env", ".env", "virtualenv"]
        site_packages_dirs = []

        for venv_dir in venv_dirs:
            venv_path = project_info.path / venv_dir
            if venv_path.exists():
                # Find site-packages directory
                site_packages = list(venv_path.rglob("site-packages"))
                site_packages_dirs.extend(site_packages)

        if not site_packages_dirs:
            # Try to find global site-packages
            try:
                result = subprocess.run(
                    ["python", "-c", "import site; print(site.getsitepackages()[0])"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    global_site_packages = Path(result.stdout.strip())
                    if global_site_packages.exists():
                        site_packages_dirs.append(global_site_packages)
            except (subprocess.TimeoutExpired, Exception):
                pass

        total_size = 0

        for dependency in project_info.dependencies:
            for site_packages in site_packages_dirs:
                # Look for package directory
                package_dirs = [
                    site_packages / dependency.name,
                    site_packages / dependency.name.replace("-", "_"),
                ]

                # Also look for .dist-info directories
                dist_info_pattern = f"{dependency.name}*.dist-info"
                dist_info_dirs = list(site_packages.glob(dist_info_pattern))
                package_dirs.extend(dist_info_dirs)

                for package_dir in package_dirs:
                    if package_dir.exists():
                        size = get_directory_size(package_dir)
                        dependency.size_bytes = max(dependency.size_bytes, size)
                        dependency.install_path = package_dir
                        break

                if dependency.size_bytes > 0:
                    break

            total_size += dependency.size_bytes

        project_info.total_size_bytes = total_size

    def _parse_requirements_txt(
        self, file_path: Path, dep_type: DependencyType = DependencyType.PRODUCTION
    ) -> List[DependencyInfo]:
        """Parse requirements.txt file"""
        dependencies = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or line.startswith("-"):
                        continue

                    # Parse package name and version
                    match = re.match(r"^([a-zA-Z0-9_-]+)([>=<~!]+.*)?", line)
                    if match:
                        name = match.group(1)
                        version = match.group(2) or ""

                        dep_info = DependencyInfo(
                            name=name, version=version, dependency_type=dep_type
                        )
                        dependencies.append(dep_info)
        except (OSError, IOError) as e:
            logger.warning(f"Failed to read requirements file: {file_path}, error: {e}")

        return dependencies

    def _parse_pyproject_toml(self, file_path: Path) -> List[DependencyInfo]:
        """Parse pyproject.toml file"""
        dependencies = []

        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                logger.warning(
                    "tomllib/tomli not available, cannot parse pyproject.toml"
                )
                return dependencies

        try:
            with open(file_path, "rb") as f:
                data = tomllib.load(f)

            # Parse dependencies from project.dependencies
            project_deps = data.get("project", {}).get("dependencies", [])
            for dep_spec in project_deps:
                name, version = self._parse_dependency_spec(dep_spec)
                if name:
                    dep_info = DependencyInfo(
                        name=name,
                        version=version,
                        dependency_type=DependencyType.PRODUCTION,
                    )
                    dependencies.append(dep_info)

            # Parse optional dependencies
            optional_deps = data.get("project", {}).get("optional-dependencies", {})
            for group_name, deps in optional_deps.items():
                dep_type = (
                    DependencyType.DEVELOPMENT
                    if "dev" in group_name.lower()
                    else DependencyType.OPTIONAL
                )
                for dep_spec in deps:
                    name, version = self._parse_dependency_spec(dep_spec)
                    if name:
                        dep_info = DependencyInfo(
                            name=name, version=version, dependency_type=dep_type
                        )
                        dependencies.append(dep_info)

        except Exception as e:
            logger.warning(f"Failed to parse pyproject.toml: {file_path}, error: {e}")

        return dependencies

    def _parse_setup_py(self, file_path: Path) -> List[DependencyInfo]:
        """Parse setup.py file (basic parsing)"""
        dependencies = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Look for install_requires
            install_requires_match = re.search(
                r"install_requires\s*=\s*\[(.*?)\]", content, re.DOTALL
            )
            if install_requires_match:
                deps_str = install_requires_match.group(1)
                # Extract quoted strings
                dep_matches = re.findall(r'["\']([^"\']+)["\']', deps_str)
                for dep_spec in dep_matches:
                    name, version = self._parse_dependency_spec(dep_spec)
                    if name:
                        dep_info = DependencyInfo(
                            name=name,
                            version=version,
                            dependency_type=DependencyType.PRODUCTION,
                        )
                        dependencies.append(dep_info)

        except Exception as e:
            logger.warning(f"Failed to parse setup.py: {file_path}, error: {e}")

        return dependencies

    def _parse_pipfile(self, file_path: Path) -> List[DependencyInfo]:
        """Parse Pipfile"""
        dependencies = []

        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                logger.warning("tomllib/tomli not available, cannot parse Pipfile")
                return dependencies

        try:
            with open(file_path, "rb") as f:
                data = tomllib.load(f)

            # Parse packages (production dependencies)
            packages = data.get("packages", {})
            for name, version_spec in packages.items():
                version = (
                    version_spec
                    if isinstance(version_spec, str)
                    else str(version_spec.get("version", ""))
                )
                dep_info = DependencyInfo(
                    name=name,
                    version=version,
                    dependency_type=DependencyType.PRODUCTION,
                )
                dependencies.append(dep_info)

            # Parse dev-packages
            dev_packages = data.get("dev-packages", {})
            for name, version_spec in dev_packages.items():
                version = (
                    version_spec
                    if isinstance(version_spec, str)
                    else str(version_spec.get("version", ""))
                )
                dep_info = DependencyInfo(
                    name=name,
                    version=version,
                    dependency_type=DependencyType.DEVELOPMENT,
                )
                dependencies.append(dep_info)

        except Exception as e:
            logger.warning(f"Failed to parse Pipfile: {file_path}, error: {e}")

        return dependencies

    def _parse_dependency_spec(self, dep_spec: str) -> Tuple[str, str]:
        """Parse dependency specification like 'requests>=2.25.0'"""
        match = re.match(r"^([a-zA-Z0-9_-]+)([>=<~!]+.*)?", dep_spec.strip())
        if match:
            name = match.group(1)
            version = match.group(2) or ""
            return name, version
        return "", ""

    def _get_name_from_pyproject(self, file_path: Path) -> Optional[str]:
        """Get project name from pyproject.toml"""
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                return None

        try:
            with open(file_path, "rb") as f:
                data = tomllib.load(f)
            return data.get("project", {}).get("name")
        except Exception:
            return None

    def _get_name_from_setup_py(self, file_path: Path) -> Optional[str]:
        """Get project name from setup.py"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
            if name_match:
                return name_match.group(1)
        except Exception:
            pass
        return None

    def _detect_python_version(self, project_path: Path) -> Optional[str]:
        """Detect Python version requirement"""
        # Check .python-version file
        python_version_file = project_path / ".python-version"
        if python_version_file.exists():
            try:
                with open(python_version_file, "r") as f:
                    return f.read().strip()
            except Exception:
                pass

        # Check runtime.txt (Heroku style)
        runtime_file = project_path / "runtime.txt"
        if runtime_file.exists():
            try:
                with open(runtime_file, "r") as f:
                    content = f.read().strip()
                    if content.startswith("python-"):
                        return content[7:]  # Remove "python-" prefix
            except Exception:
                pass

        return None

    def _detect_virtual_env(self, project_path: Path) -> Optional[str]:
        """Detect virtual environment"""
        venv_dirs = ["venv", ".venv", "env", ".env", "virtualenv"]
        for venv_dir in venv_dirs:
            if (project_path / venv_dir).exists():
                return venv_dir
        return None

    def _detect_package_manager(self, project_path: Path) -> str:
        """Detect package manager"""
        if (project_path / "Pipfile").exists():
            return "pipenv"
        elif (project_path / "poetry.lock").exists():
            return "poetry"
        elif (project_path / "pyproject.toml").exists():
            return "pip/pyproject"
        elif (project_path / "requirements.txt").exists():
            return "pip"
        else:
            return "unknown"
