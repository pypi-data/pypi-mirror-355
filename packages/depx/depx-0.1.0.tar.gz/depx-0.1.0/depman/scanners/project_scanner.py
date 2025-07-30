"""
Project scanner for DepMan.
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from depman.models.dependency import DependencyType


class ProjectScanner:
    """Scans a project directory to detect its type and configuration."""
    
    # Mapping of file patterns to dependency types
    FILE_PATTERNS = {
        "package.json": DependencyType.NPM,
        "yarn.lock": DependencyType.YARN,
        "pnpm-lock.yaml": DependencyType.PNPM,
        "requirements.txt": DependencyType.PIP,
        "pyproject.toml": [DependencyType.POETRY, DependencyType.PIP],
        "Pipfile": DependencyType.PIPENV,
        "Pipfile.lock": DependencyType.PIPENV,
        "pom.xml": DependencyType.MAVEN,
        "build.gradle": DependencyType.GRADLE,
        "build.gradle.kts": DependencyType.GRADLE,
        "Gemfile": DependencyType.BUNDLER,
        "go.mod": DependencyType.GO,
        "Cargo.toml": DependencyType.CARGO,
        "composer.json": DependencyType.COMPOSER,
        "*.csproj": DependencyType.NUGET,
        "*.fsproj": DependencyType.NUGET,
        "packages.config": DependencyType.NUGET,
    }
    
    def __init__(self):
        """Initialize the project scanner."""
        self.logger = logging.getLogger("depman.scanner")
    
    def scan_directory(self, directory: Path) -> Dict[DependencyType, List[Path]]:
        """
        Scan a directory to detect project types based on configuration files.
        
        Args:
            directory (Path): Directory to scan.
            
        Returns:
            Dict[DependencyType, List[Path]]: Mapping of detected dependency types to config files.
        """
        self.logger.debug(f"Scanning directory: {directory}")
        results: Dict[DependencyType, List[Path]] = {}
        
        if not directory.is_dir():
            self.logger.warning(f"Not a directory: {directory}")
            return results
        
        # Check for each file pattern
        for pattern, dep_type in self.FILE_PATTERNS.items():
            # Handle glob patterns
            if "*" in pattern:
                matches = list(directory.glob(pattern))
            else:
                file_path = directory / pattern
                matches = [file_path] if file_path.exists() else []
            
            if matches:
                self.logger.debug(f"Found {pattern} in {directory}")
                # Handle multiple possible dependency types
                if isinstance(dep_type, list):
                    for dt in dep_type:
                        if dt not in results:
                            results[dt] = []
                        results[dt].extend(matches)
                else:
                    if dep_type not in results:
                        results[dep_type] = []
                    results[dep_type].extend(matches)
        
        return results
    
    def scan_recursive(
        self, 
        directory: Path, 
        max_depth: int = 3,
        include_hidden: bool = False
    ) -> Dict[Path, Dict[DependencyType, List[Path]]]:
        """
        Recursively scan directories to find project configurations.
        
        Args:
            directory (Path): Root directory to scan.
            max_depth (int, optional): Maximum recursion depth. Defaults to 3.
            include_hidden (bool, optional): Include hidden directories. Defaults to False.
            
        Returns:
            Dict[Path, Dict[DependencyType, List[Path]]]: Directory to dependency type mapping.
        """
        results = {}
        self._scan_recursive_impl(directory, results, 0, max_depth, include_hidden)
        return results
    
    def _scan_recursive_impl(
        self,
        directory: Path,
        results: Dict[Path, Dict[DependencyType, List[Path]]],
        current_depth: int,
        max_depth: int,
        include_hidden: bool
    ) -> None:
        """
        Implementation of recursive scanning.
        
        Args:
            directory (Path): Current directory to scan.
            results (Dict[Path, Dict[DependencyType, List[Path]]]): Results dictionary to populate.
            current_depth (int): Current recursion depth.
            max_depth (int): Maximum recursion depth.
            include_hidden (bool): Whether to include hidden directories.
        """
        if current_depth > max_depth:
            return
        
        # Scan the current directory
        dir_results = self.scan_directory(directory)
        if dir_results:
            results[directory] = dir_results
        
        # Recursively scan subdirectories
        if current_depth < max_depth:
            try:
                for subdir in directory.iterdir():
                    if not subdir.is_dir():
                        continue
                        
                    # Skip hidden directories unless include_hidden is True
                    if not include_hidden and subdir.name.startswith("."):
                        continue
                        
                    # Skip common directories to avoid scanning too much
                    if subdir.name in ["node_modules", "venv", ".venv", "dist", "build", "target", 
                                      "__pycache__", ".git", ".svn", ".hg"]:
                        continue
                        
                    self._scan_recursive_impl(
                        subdir, results, current_depth + 1, max_depth, include_hidden
                    )
            except PermissionError:
                self.logger.warning(f"Permission denied for directory: {directory}")
            except Exception as e:
                self.logger.error(f"Error scanning directory {directory}: {e}")
    
    def detect_project_type(self, directory: Path) -> Optional[DependencyType]:
        """
        Detect the primary project type for a directory.
        
        Args:
            directory (Path): Directory to scan.
            
        Returns:
            Optional[DependencyType]: Detected project type or None.
        """
        results = self.scan_directory(directory)
        
        if not results:
            return None
        
        # Prioritize certain project types
        for priority_type in [
            DependencyType.POETRY, DependencyType.NPM, DependencyType.MAVEN,
            DependencyType.GRADLE, DependencyType.CARGO, DependencyType.PIP,
            DependencyType.BUNDLER
        ]:
            if priority_type in results:
                return priority_type
        
        # Otherwise return the first result
        return next(iter(results.keys())) 