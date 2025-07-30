"""
Dependency model classes for DepMan.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set
from pathlib import Path


class DependencyType(Enum):
    """Type of dependency."""
    
    # Operating system package managers
    APT = "apt"
    YUM = "yum"
    DNF = "dnf"
    PACMAN = "pacman"
    HOMEBREW = "brew"
    CHOCOLATEY = "choco"
    SCOOP = "scoop"
    
    # Language package managers
    JAVASCRIPT = "javascript"  # General JavaScript/Node.js type
    NPM = "npm"
    YARN = "yarn"
    PNPM = "pnpm"
    PIP = "pip"
    POETRY = "poetry"
    PIPENV = "pipenv"
    MAVEN = "maven"
    GRADLE = "gradle"
    BUNDLER = "bundler"
    RUBYGEMS = "gem"
    GO = "go"
    CARGO = "cargo"
    COMPOSER = "composer"
    NUGET = "nuget"
    
    # Other
    UNKNOWN = "unknown"


class DependencyScope(Enum):
    """Scope of the dependency."""
    
    GLOBAL = "global"  # System-wide or globally installed
    PROJECT = "project"  # Project-specific dependency
    UNKNOWN = "unknown"


@dataclass
class Dependency:
    """Represents a dependency package."""
    
    name: str
    package_manager: DependencyType
    scope: DependencyScope
    version: Optional[str] = None
    path: Optional[Path] = None
    description: Optional[str] = None
    installed_size: Optional[int] = None
    install_date: Optional[str] = None
    dependencies: Set[str] = field(default_factory=set)
    metadata: Dict = field(default_factory=dict)
    
    def __str__(self) -> str:
        """String representation of the dependency."""
        version_str = f" ({self.version})" if self.version else ""
        return f"{self.name}{version_str} - {self.package_manager.value} ({self.scope.value})"
    
    def to_dict(self) -> Dict:
        """Convert the dependency to a dictionary."""
        return {
            "name": self.name,
            "package_manager": self.package_manager.value,
            "scope": self.scope.value,
            "version": self.version,
            "path": str(self.path) if self.path else None,
            "description": self.description,
            "installed_size": self.installed_size,
            "install_date": self.install_date,
            "dependencies": list(self.dependencies),
            "metadata": self.metadata,
        }


@dataclass
class DependencyVulnerability:
    """Represents a security vulnerability in a dependency."""
    
    id: str
    dependency_name: str
    affected_versions: List[str]
    fixed_versions: List[str]
    severity: str
    description: str
    url: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    
    def __str__(self) -> str:
        """String representation of the vulnerability."""
        return (f"{self.dependency_name}: {self.id} ({self.severity})"
                f" - {self.description[:50]}{'...' if len(self.description) > 50 else ''}")


@dataclass
class ProjectDependencies:
    """Represents all dependencies for a project."""
    
    project_path: Path
    package_manager: DependencyType
    dependencies: Dict[str, Dependency] = field(default_factory=dict)
    config_file: Optional[Path] = None
    lock_file: Optional[Path] = None
    metadata: Dict = field(default_factory=dict)
    
    def add_dependency(self, dependency: Dependency) -> None:
        """Add a dependency to the project."""
        self.dependencies[dependency.name] = dependency
    
    def get_dependency(self, name: str) -> Optional[Dependency]:
        """Get a dependency by name."""
        return self.dependencies.get(name)
    
    def remove_dependency(self, name: str) -> None:
        """Remove a dependency by name."""
        if name in self.dependencies:
            del self.dependencies[name]
    
    def get_all_dependencies(self) -> List[Dependency]:
        """Get all dependencies."""
        return list(self.dependencies.values())
    
    def __str__(self) -> str:
        """String representation of the project dependencies."""
        return f"{self.project_path.name} ({self.package_manager.value}): {len(self.dependencies)} dependencies" 