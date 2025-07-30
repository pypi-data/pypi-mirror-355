"""
C# project parser

Parse C# projects with .csproj, packages.config, and PackageReference files
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree as ET

from ..utils.file_utils import get_directory_size, safe_read_json
from .base import (
    BaseParser,
    DependencyInfo,
    DependencyType,
    ProjectInfo,
    ProjectType,
)

logger = logging.getLogger(__name__)


class CSharpParser(BaseParser):
    """C# project parser"""

    @property
    def project_type(self) -> ProjectType:
        return ProjectType.CSHARP

    @property
    def config_files(self) -> List[str]:
        return [
            "*.csproj",
            "*.vbproj",
            "*.fsproj",
            "packages.config",
            "project.json",
            "*.sln",
        ]

    def can_parse(self, project_path: Path) -> bool:
        """Check if this is a C# project"""
        # Check for project files
        project_files = (
            list(project_path.glob("*.csproj"))
            + list(project_path.glob("*.vbproj"))
            + list(project_path.glob("*.fsproj"))
        )
        if project_files:
            return True

        # Check for packages.config
        if (project_path / "packages.config").exists():
            return True

        # Check for project.json (legacy .NET Core)
        if (project_path / "project.json").exists():
            return True

        # Check for C# source files
        cs_files = list(project_path.glob("*.cs"))
        if cs_files:
            return True

        return False

    def parse_project(self, project_path: Path) -> Optional[ProjectInfo]:
        """Parse C# project information"""
        if not self.can_parse(project_path):
            return None

        # Find primary project file
        project_name = project_path.name
        config_file = None

        # Priority order for config files
        project_files = (
            list(project_path.glob("*.csproj"))
            + list(project_path.glob("*.vbproj"))
            + list(project_path.glob("*.fsproj"))
        )

        if project_files:
            config_file = project_files[0]
            project_name = self._get_name_from_project_file(config_file) or project_name
        elif (project_path / "packages.config").exists():
            config_file = project_path / "packages.config"
        elif (project_path / "project.json").exists():
            config_file = project_path / "project.json"

        if not config_file:
            return None

        project_info = ProjectInfo(
            name=project_name,
            path=project_path,
            project_type=self.project_type,
            config_file=config_file,
            dependencies=[],
            metadata={
                "dotnet_version": self._detect_dotnet_version(project_path),
                "framework": self._detect_framework(project_path),
                "project_type": self._detect_project_type(project_path),
                "has_packages_folder": (project_path / "packages").exists(),
            },
        )

        # Parse dependencies
        project_info.dependencies = self.get_dependencies(project_info)

        # Calculate sizes
        self.calculate_dependency_sizes(project_info)

        return project_info

    def get_dependencies(self, project_info: ProjectInfo) -> List[DependencyInfo]:
        """Get C# project dependencies"""
        dependencies = []

        config_file = project_info.config_file

        if config_file.suffix in [".csproj", ".vbproj", ".fsproj"]:
            dependencies.extend(self._parse_project_file(config_file))
        elif config_file.name == "packages.config":
            dependencies.extend(self._parse_packages_config(config_file))
        elif config_file.name == "project.json":
            dependencies.extend(self._parse_project_json(config_file))

        return dependencies

    def calculate_dependency_sizes(self, project_info: ProjectInfo) -> None:
        """Calculate C# dependency sizes"""
        total_size = 0

        # Check packages folder (legacy NuGet)
        packages_dir = project_info.path / "packages"
        if packages_dir.exists():
            packages_size = get_directory_size(packages_dir)
            total_size += packages_size

            # Update dependency sizes based on packages directory
            for dependency in project_info.dependencies:
                package_dirs = list(packages_dir.glob(f"{dependency.name}.*"))
                if package_dirs:
                    dependency.size_bytes = get_directory_size(package_dirs[0])
                    dependency.install_path = package_dirs[0]

        # Check bin and obj directories
        for build_dir in ["bin", "obj"]:
            build_path = project_info.path / build_dir
            if build_path.exists():
                total_size += get_directory_size(build_path)

        project_info.total_size_bytes = total_size

    def _parse_project_file(self, project_file: Path) -> List[DependencyInfo]:
        """Parse .csproj/.vbproj/.fsproj file"""
        dependencies = []

        try:
            tree = ET.parse(project_file)
            root = tree.getroot()

            # Find PackageReference elements (modern .NET)
            for package_ref in root.findall(".//PackageReference"):
                include = package_ref.get("Include")
                version = package_ref.get("Version")

                if include:
                    dep_info = DependencyInfo(
                        name=include,
                        version=version or "",
                        dependency_type=DependencyType.PRODUCTION,
                    )
                    dependencies.append(dep_info)

            # Find Reference elements with HintPath (legacy)
            for reference in root.findall(".//Reference"):
                include = reference.get("Include")
                hint_path = reference.find("HintPath")

                if include and hint_path is not None:
                    # Extract package name from hint path
                    hint_text = hint_path.text or ""
                    if "packages" in hint_text:
                        package_match = re.search(r"packages[/\\]([^/\\]+)", hint_text)
                        if package_match:
                            package_name = package_match.group(1).split(".")[0]
                            dep_info = DependencyInfo(
                                name=package_name,
                                version="",
                                dependency_type=DependencyType.PRODUCTION,
                            )
                            dependencies.append(dep_info)

        except ET.ParseError as e:
            logger.warning(f"Failed to parse project file: {project_file}, error: {e}")
        except Exception as e:
            logger.warning(f"Failed to read project file: {project_file}, error: {e}")

        return dependencies

    def _parse_packages_config(self, packages_config: Path) -> List[DependencyInfo]:
        """Parse packages.config file"""
        dependencies = []

        try:
            tree = ET.parse(packages_config)
            root = tree.getroot()

            for package in root.findall("package"):
                package_id = package.get("id")
                version = package.get("version")
                target_framework = package.get("targetFramework")

                if package_id:
                    dep_info = DependencyInfo(
                        name=package_id,
                        version=version or "",
                        dependency_type=DependencyType.PRODUCTION,
                    )
                    dependencies.append(dep_info)

        except ET.ParseError as e:
            logger.warning(
                f"Failed to parse packages.config: {packages_config}, error: {e}"
            )
        except Exception as e:
            logger.warning(
                f"Failed to read packages.config: {packages_config}, error: {e}"
            )

        return dependencies

    def _parse_project_json(self, project_json: Path) -> List[DependencyInfo]:
        """Parse project.json file (legacy .NET Core)"""
        dependencies = []

        data = safe_read_json(project_json)
        if not data:
            return dependencies

        # Parse dependencies
        deps = data.get("dependencies", {})
        for name, version in deps.items():
            dep_info = DependencyInfo(
                name=name,
                version=str(version),
                dependency_type=DependencyType.PRODUCTION,
            )
            dependencies.append(dep_info)

        return dependencies

    def _get_name_from_project_file(self, project_file: Path) -> Optional[str]:
        """Get project name from project file"""
        try:
            tree = ET.parse(project_file)
            root = tree.getroot()

            # Look for AssemblyName
            assembly_name = root.find(".//AssemblyName")
            if assembly_name is not None and assembly_name.text:
                return assembly_name.text

            # Look for RootNamespace
            root_namespace = root.find(".//RootNamespace")
            if root_namespace is not None and root_namespace.text:
                return root_namespace.text

        except Exception:
            pass

        # Fallback to filename without extension
        return project_file.stem

    def _detect_dotnet_version(self, project_path: Path) -> Optional[str]:
        """Detect .NET version"""
        # Check global.json
        global_json = project_path / "global.json"
        if global_json.exists():
            data = safe_read_json(global_json)
            if data:
                sdk = data.get("sdk", {})
                version = sdk.get("version")
                if version:
                    return version

        # Check project files for TargetFramework
        project_files = (
            list(project_path.glob("*.csproj"))
            + list(project_path.glob("*.vbproj"))
            + list(project_path.glob("*.fsproj"))
        )

        for project_file in project_files:
            try:
                tree = ET.parse(project_file)
                root = tree.getroot()

                target_framework = root.find(".//TargetFramework")
                if target_framework is not None and target_framework.text:
                    return target_framework.text

                target_frameworks = root.find(".//TargetFrameworks")
                if target_frameworks is not None and target_frameworks.text:
                    # Return first framework if multiple
                    return target_frameworks.text.split(";")[0]

            except Exception:
                continue

        return None

    def _detect_framework(self, project_path: Path) -> Optional[str]:
        """Detect .NET framework type"""
        project_files = (
            list(project_path.glob("*.csproj"))
            + list(project_path.glob("*.vbproj"))
            + list(project_path.glob("*.fsproj"))
        )

        for project_file in project_files:
            try:
                tree = ET.parse(project_file)
                root = tree.getroot()

                # Check for SDK-style project (modern .NET)
                if root.get("Sdk"):
                    return ".NET Core/5+"

                # Check for legacy .NET Framework
                target_framework = root.find(".//TargetFrameworkVersion")
                if target_framework is not None:
                    return ".NET Framework"

            except Exception:
                continue

        return None

    def _detect_project_type(self, project_path: Path) -> str:
        """Detect project type"""
        if list(project_path.glob("*.csproj")):
            return "C#"
        elif list(project_path.glob("*.vbproj")):
            return "VB.NET"
        elif list(project_path.glob("*.fsproj")):
            return "F#"
        else:
            return "Unknown"
