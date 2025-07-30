"""
Java project parser

Parse Java projects with Maven (pom.xml) and Gradle (build.gradle)
"""

import logging
import re
import subprocess
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


class JavaParser(BaseParser):
    """Java project parser"""

    @property
    def project_type(self) -> ProjectType:
        return ProjectType.JAVA

    @property
    def config_files(self) -> List[str]:
        return [
            "pom.xml",
            "build.gradle",
            "build.gradle.kts",
            "gradle.properties",
        ]

    def can_parse(self, project_path: Path) -> bool:
        """Check if this is a Java project"""
        for config_file in self.config_files:
            if (project_path / config_file).exists():
                return True
        return False

    def parse_project(self, project_path: Path) -> Optional[ProjectInfo]:
        """Parse Java project information"""
        if not self.can_parse(project_path):
            return None

        # Determine project name and config file
        project_name = project_path.name
        config_file = None

        # Priority order for config files
        for config_name in ["pom.xml", "build.gradle", "build.gradle.kts"]:
            config_path = project_path / config_name
            if config_path.exists():
                config_file = config_path
                break

        if not config_file:
            return None

        # Try to get project name from config
        if config_file.name == "pom.xml":
            project_name = self._get_name_from_pom(config_file) or project_name
        elif config_file.name.startswith("build.gradle"):
            project_name = self._get_name_from_gradle(config_file) or project_name

        project_info = ProjectInfo(
            name=project_name,
            path=project_path,
            project_type=self.project_type,
            config_file=config_file,
            dependencies=[],
            metadata={
                "java_version": self._detect_java_version(project_path),
                "build_tool": self._detect_build_tool(project_path),
                "has_wrapper": self._has_wrapper(project_path),
            },
        )

        # Parse dependencies
        project_info.dependencies = self.get_dependencies(project_info)

        # Calculate sizes
        self.calculate_dependency_sizes(project_info)

        return project_info

    def get_dependencies(self, project_info: ProjectInfo) -> List[DependencyInfo]:
        """Get Java project dependencies"""
        dependencies = []

        config_file = project_info.config_file

        if config_file.name == "pom.xml":
            dependencies.extend(self._parse_maven_dependencies(config_file))
        elif config_file.name.startswith("build.gradle"):
            dependencies.extend(self._parse_gradle_dependencies(config_file))

        return dependencies

    def calculate_dependency_sizes(self, project_info: ProjectInfo) -> None:
        """Calculate Java dependency sizes"""
        # Look for Maven/Gradle cache directories
        cache_dirs = []

        # Maven local repository
        maven_repo = Path.home() / ".m2" / "repository"
        if maven_repo.exists():
            cache_dirs.append(maven_repo)

        # Gradle cache
        gradle_cache = Path.home() / ".gradle" / "caches"
        if gradle_cache.exists():
            cache_dirs.append(gradle_cache)

        # Project-specific build directories
        build_dirs = [
            project_info.path / "target",  # Maven
            project_info.path / "build",  # Gradle
        ]

        total_size = 0

        for dependency in project_info.dependencies:
            # Try to find dependency in cache directories
            for cache_dir in cache_dirs:
                if self._find_dependency_in_cache(dependency, cache_dir):
                    break

            # Check build directories
            for build_dir in build_dirs:
                if build_dir.exists():
                    size = get_directory_size(build_dir)
                    total_size += size

        project_info.total_size_bytes = total_size

    def _parse_maven_dependencies(self, pom_file: Path) -> List[DependencyInfo]:
        """Parse Maven pom.xml dependencies"""
        dependencies = []

        try:
            tree = ET.parse(pom_file)
            root = tree.getroot()

            # Handle namespace
            namespace = {"maven": "http://maven.apache.org/POM/4.0.0"}
            if root.tag.startswith("{"):
                ns = root.tag[1:].split("}")[0]
                namespace = {"maven": ns}

            # Find dependencies
            deps_element = root.find(".//maven:dependencies", namespace)
            if deps_element is not None:
                for dep in deps_element.findall("maven:dependency", namespace):
                    group_id = dep.find("maven:groupId", namespace)
                    artifact_id = dep.find("maven:artifactId", namespace)
                    version = dep.find("maven:version", namespace)
                    scope = dep.find("maven:scope", namespace)

                    if group_id is not None and artifact_id is not None:
                        name = f"{group_id.text}:{artifact_id.text}"
                        version_text = version.text if version is not None else ""
                        scope_text = scope.text if scope is not None else "compile"

                        dep_type = DependencyType.PRODUCTION
                        if scope_text in ["test", "provided"]:
                            dep_type = DependencyType.DEVELOPMENT

                        dep_info = DependencyInfo(
                            name=name,
                            version=version_text,
                            dependency_type=dep_type,
                        )
                        dependencies.append(dep_info)

        except ET.ParseError as e:
            logger.warning(f"Failed to parse Maven pom.xml: {pom_file}, error: {e}")
        except Exception as e:
            logger.warning(f"Failed to read Maven pom.xml: {pom_file}, error: {e}")

        return dependencies

    def _parse_gradle_dependencies(self, gradle_file: Path) -> List[DependencyInfo]:
        """Parse Gradle build file dependencies"""
        dependencies = []

        try:
            with open(gradle_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse dependencies block
            dep_pattern = r'(implementation|compile|testImplementation|testCompile|api|compileOnly)\s+["\']([^"\']+)["\']'
            matches = re.findall(dep_pattern, content)

            for scope, dep_string in matches:
                # Parse group:artifact:version format
                parts = dep_string.split(":")
                if len(parts) >= 2:
                    name = f"{parts[0]}:{parts[1]}"
                    version = parts[2] if len(parts) > 2 else ""

                    dep_type = DependencyType.PRODUCTION
                    if "test" in scope.lower():
                        dep_type = DependencyType.DEVELOPMENT

                    dep_info = DependencyInfo(
                        name=name,
                        version=version,
                        dependency_type=dep_type,
                    )
                    dependencies.append(dep_info)

        except Exception as e:
            logger.warning(f"Failed to parse Gradle file: {gradle_file}, error: {e}")

        return dependencies

    def _get_name_from_pom(self, pom_file: Path) -> Optional[str]:
        """Get project name from pom.xml"""
        try:
            tree = ET.parse(pom_file)
            root = tree.getroot()

            # Handle namespace
            namespace = {"maven": "http://maven.apache.org/POM/4.0.0"}
            if root.tag.startswith("{"):
                ns = root.tag[1:].split("}")[0]
                namespace = {"maven": ns}

            artifact_id = root.find("maven:artifactId", namespace)
            if artifact_id is not None:
                return artifact_id.text

        except Exception:
            pass
        return None

    def _get_name_from_gradle(self, gradle_file: Path) -> Optional[str]:
        """Get project name from build.gradle"""
        try:
            with open(gradle_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Look for project name
            name_match = re.search(
                r'rootProject\.name\s*=\s*["\']([^"\']+)["\']', content
            )
            if name_match:
                return name_match.group(1)

        except Exception:
            pass
        return None

    def _detect_java_version(self, project_path: Path) -> Optional[str]:
        """Detect Java version requirement"""
        # Check .java-version file
        java_version_file = project_path / ".java-version"
        if java_version_file.exists():
            try:
                with open(java_version_file, "r") as f:
                    return f.read().strip()
            except Exception:
                pass

        return None

    def _detect_build_tool(self, project_path: Path) -> str:
        """Detect build tool"""
        if (project_path / "pom.xml").exists():
            return "maven"
        elif (project_path / "build.gradle").exists() or (
            project_path / "build.gradle.kts"
        ).exists():
            return "gradle"
        else:
            return "unknown"

    def _has_wrapper(self, project_path: Path) -> bool:
        """Check if project has wrapper scripts"""
        return (project_path / "mvnw").exists() or (project_path / "gradlew").exists()

    def _find_dependency_in_cache(
        self, dependency: DependencyInfo, cache_dir: Path
    ) -> bool:
        """Find dependency in cache directory"""
        # This is a simplified implementation
        # In practice, you'd want more sophisticated cache lookup
        return False
