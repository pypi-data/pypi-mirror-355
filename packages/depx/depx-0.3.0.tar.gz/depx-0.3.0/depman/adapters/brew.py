"""
Adapter for the Homebrew package manager (macOS).
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set

from depman.adapters.base import PackageManagerAdapter
from depman.models.dependency import Dependency, DependencyScope, DependencyType, ProjectDependencies
from depman.utils.cmd_executor import CommandExecutor


class BrewAdapter(PackageManagerAdapter):
    """Adapter for the Homebrew package manager."""
    
    @property
    def name(self) -> str:
        """Return the name of the package manager."""
        return "homebrew"
    
    @property
    def dependency_type(self) -> DependencyType:
        """Return the dependency type."""
        return DependencyType.HOMEBREW
    
    def __init__(self):
        """Initialize the homebrew adapter."""
        self.cmd_executor = CommandExecutor()
    
    def is_available(self) -> bool:
        """Check if homebrew is available on the system."""
        return self.cmd_executor.command_exists("brew")
    
    def install(self, package_name: str, version: Optional[str] = None, global_install: bool = True) -> bool:
        """
        Install a package using homebrew.
        
        Args:
            package_name (str): Name of the package to install.
            version (Optional[str], optional): Specific version to install. Defaults to None.
            global_install (bool, optional): Whether to install globally. Defaults to True.
            
        Returns:
            bool: True if installation was successful, False otherwise.
        """
        # Homebrew is always global, so global_install is ignored
        cmd = ["brew", "install"]
        
        # Add version constraint if specified
        if version:
            # Homebrew uses different patterns for versioning
            if self._is_cask(package_name):
                # For casks, we can't specify versions directly
                self.cmd_executor.run_command(["brew", "tap", "homebrew/cask-versions"])
                # Try to find a versioned cask
                versioned_cask = f"{package_name}@{version}"
                cmd.append(versioned_cask)
            else:
                # For formulae, we can specify a version
                cmd.append(f"{package_name}@{version}")
        else:
            cmd.append(package_name)
        
        result = self.cmd_executor.run_command(cmd)
        return result.success
    
    def _is_cask(self, package_name: str) -> bool:
        """
        Check if a package is a cask.
        
        Args:
            package_name (str): Name of the package.
            
        Returns:
            bool: True if the package is a cask, False otherwise.
        """
        cmd = ["brew", "info", "--cask", package_name]
        result = self.cmd_executor.run_command(cmd)
        return result.success
    
    def uninstall(self, package_name: str, global_install: bool = True) -> bool:
        """
        Uninstall a package using homebrew.
        
        Args:
            package_name (str): Name of the package to uninstall.
            global_install (bool, optional): Whether it's a global package. Defaults to True.
            
        Returns:
            bool: True if uninstallation was successful, False otherwise.
        """
        # Check if it's a cask
        is_cask = self._is_cask(package_name)
        
        cmd = ["brew", "uninstall"]
        if is_cask:
            cmd.append("--cask")
        
        cmd.append(package_name)
        
        result = self.cmd_executor.run_command(cmd)
        return result.success
    
    def upgrade(self, package_name: Optional[str] = None, global_install: bool = True) -> bool:
        """
        Upgrade a package or all packages using homebrew.
        
        Args:
            package_name (Optional[str], optional): Name of the package to upgrade. 
                                                  If None, upgrade all packages. Defaults to None.
            global_install (bool, optional): Whether it's a global package. Defaults to True.
            
        Returns:
            bool: True if upgrade was successful, False otherwise.
        """
        cmd = ["brew", "upgrade"]
        
        if package_name:
            # Check if it's a cask
            is_cask = self._is_cask(package_name)
            if is_cask:
                cmd.append("--cask")
            cmd.append(package_name)
        
        result = self.cmd_executor.run_command(cmd)
        return result.success
    
    def list_packages(self, global_packages: bool = True) -> List[Dependency]:
        """
        List all installed packages using homebrew.
        
        Args:
            global_packages (bool, optional): Whether to list global packages. Defaults to True.
            
        Returns:
            List[Dependency]: List of installed dependencies.
        """
        # List formulae
        cmd_formulae = ["brew", "list", "--formula", "--versions"]
        result_formulae = self.cmd_executor.run_command(cmd_formulae)
        
        # List casks
        cmd_casks = ["brew", "list", "--cask", "--versions"]
        result_casks = self.cmd_executor.run_command(cmd_casks)
        
        dependencies = []
        
        # Parse formulae
        if result_formulae.success:
            for line in result_formulae.stdout.strip().split("\n"):
                if not line:
                    continue
                    
                parts = line.split()
                if len(parts) >= 2:
                    name = parts[0]
                    version = parts[1]
                    
                    # Get more info about the package
                    info = self.get_package_info(name)
                    
                    # If we couldn't get more info, create a basic dependency object
                    if not info:
                        info = Dependency(
                            name=name,
                            version=version,
                            package_manager=self.dependency_type,
                            scope=DependencyScope.GLOBAL
                        )
                    
                    dependencies.append(info)
        
        # Parse casks
        if result_casks.success:
            for line in result_casks.stdout.strip().split("\n"):
                if not line:
                    continue
                    
                parts = line.split()
                if len(parts) >= 2:
                    name = parts[0]
                    version = parts[1]
                    
                    # Get more info about the package
                    info = self.get_package_info(name, is_cask=True)
                    
                    # If we couldn't get more info, create a basic dependency object
                    if not info:
                        info = Dependency(
                            name=name,
                            version=version,
                            package_manager=self.dependency_type,
                            scope=DependencyScope.GLOBAL
                        )
                    
                    dependencies.append(info)
        
        return dependencies
    
    def get_package_info(self, package_name: str, global_package: bool = True, is_cask: bool = False) -> Optional[Dependency]:
        """
        Get information about a homebrew package.
        
        Args:
            package_name (str): Name of the package.
            global_package (bool, optional): Whether it's a global package. Defaults to True.
            is_cask (bool, optional): Whether the package is a cask. Defaults to False.
            
        Returns:
            Optional[Dependency]: Dependency information if found, None otherwise.
        """
        # Use --json=v2 instead of v1 for better compatibility with --cask
        cmd = ["brew", "info", "--json=v2"]
        if is_cask:
            cmd.extend(["--cask", package_name])
        else:
            cmd.append(package_name)
        
        result = self.cmd_executor.run_command(cmd)
        
        if not result.success or not result.stdout.strip():
            return None
        
        try:
            info = json.loads(result.stdout)
            
            if not info or (is_cask and not info.get('casks')) or (not is_cask and not info.get('formulae')):
                return None
                
            # Extract the correct object based on whether it's a cask or formula
            if is_cask:
                if not info.get('casks') or len(info['casks']) == 0:
                    return None
                package_info = info['casks'][0]
            else:
                if not info.get('formulae') or len(info['formulae']) == 0:
                    return None
                package_info = info['formulae'][0]
            
            # Get the path
            if is_cask:
                path = Path("/opt/homebrew/Caskroom") / package_name
                if not path.exists():
                    # Try the Intel path
                    path = Path("/usr/local/Caskroom") / package_name
            else:
                path = Path("/opt/homebrew/Cellar") / package_name
                if not path.exists():
                    # Try the Intel path
                    path = Path("/usr/local/Cellar") / package_name
            
            # Get dependencies
            dependencies = set()
            if is_cask:
                deps = package_info.get("depends_on", {}).get("formula", [])
            else:
                deps = package_info.get("dependencies", [])
                
            for dep in deps:
                if isinstance(dep, str):
                    dependencies.add(dep)
                    
            # Get metadata
            metadata = {
                "homepage": package_info.get("homepage", ""),
                "license": package_info.get("license", ""),
                "installed_as_dependency": package_info.get("installed_as_dependency", False),
                "installed_on_request": package_info.get("installed_on_request", False),
                "full_name": package_info.get("full_name", ""),
            }
            
            # Description and version
            if is_cask:
                description = package_info.get("desc", "")
                version = package_info.get("version", "")
            else:
                description = package_info.get("desc", "")
                version = package_info.get("installed", [{}])[0].get("version", "") if package_info.get("installed") else ""
            
            return Dependency(
                name=package_name,
                version=version,
                description=description,
                package_manager=self.dependency_type,
                scope=DependencyScope.GLOBAL,
                path=path,
                dependencies=dependencies,
                metadata=metadata
            )
                
        except (json.JSONDecodeError, IndexError, KeyError) as e:
            print(f"Error parsing brew info output: {e}")
            return None
    
    def get_package_path(self, package_name: str, global_package: bool = True) -> Optional[Path]:
        """
        Get the installation path of a package.
        
        Args:
            package_name (str): Name of the package.
            global_package (bool, optional): Whether it's a global package. Defaults to True.
            
        Returns:
            Optional[Path]: Path to the package if found, None otherwise.
        """
        # Try as a formula first
        package_info = self.get_package_info(package_name)
        if package_info and package_info.path:
            return package_info.path
            
        # Try as a cask
        package_info = self.get_package_info(package_name, is_cask=True)
        if package_info and package_info.path:
            return package_info.path
            
        return None
    
    def search_packages(self, query: str) -> List[Dict]:
        """
        Search for packages matching a query using homebrew.
        
        Args:
            query (str): Search query.
            
        Returns:
            List[Dict]: List of matching packages.
        """
        cmd = ["brew", "search", query]
        result = self.cmd_executor.run_command(cmd)
        
        packages = []
        
        if result.success:
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                    
                # Get package info
                name = line.strip()
                
                # Only process if it looks like a package name
                if re.match(r"^[a-zA-Z0-9_\-\./@]+$", name):
                    # Try to get more info
                    info_cmd = ["brew", "info", name]
                    info_result = self.cmd_executor.run_command(info_cmd)
                    
                    description = ""
                    version = ""
                    
                    if info_result.success:
                        # Extract description and version
                        info_lines = info_result.stdout.strip().split("\n")
                        if len(info_lines) > 1:
                            # First line typically has the name and version
                            if ": " in info_lines[0]:
                                version = info_lines[0].split(": ")[1].split(",")[0].strip()
                                
                            # Second line typically has the description
                            description = info_lines[1].strip()
                    
                    packages.append({
                        "name": name,
                        "description": description,
                        "version": version,
                    })
        
        return packages
    
    def can_handle_project(self, project_dir: Path) -> bool:
        """
        Check if this adapter can handle the project in the given directory.
        
        Args:
            project_dir (Path): Project directory.
            
        Returns:
            bool: True if this adapter can handle the project, False otherwise.
        """
        # Check for Brewfile
        return (project_dir / "Brewfile").exists()
    
    def get_config_file_patterns(self) -> List[str]:
        """
        Get patterns for identifying config files this adapter can handle.
        
        Returns:
            List[str]: List of glob patterns for config files.
        """
        return ["Brewfile"]
    
    def get_project_dependencies(self, project_dir: Path) -> ProjectDependencies:
        """
        Get all dependencies for a project.
        
        Args:
            project_dir (Path): Project directory.
            
        Returns:
            ProjectDependencies: Object containing all project dependencies.
        """
        brewfile_path = project_dir / "Brewfile"
        
        project_deps = ProjectDependencies(
            project_path=project_dir,
            package_manager=self.dependency_type,
            config_file=brewfile_path if brewfile_path.exists() else None
        )
        
        if brewfile_path.exists():
            self._parse_brewfile(brewfile_path, project_deps)
        
        return project_deps
    
    def _parse_brewfile(self, brewfile_path: Path, project_deps: ProjectDependencies) -> None:
        """
        Parse a Brewfile to extract dependencies.
        
        Args:
            brewfile_path (Path): Path to the Brewfile.
            project_deps (ProjectDependencies): Project dependencies to update.
        """
        try:
            with open(brewfile_path, "r") as f:
                for line in f:
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith("#"):
                        continue
                    
                    # Parse the line
                    if line.startswith("brew ") or line.startswith("cask "):
                        parts = line.split(" ", 1)
                        if len(parts) < 2:
                            continue
                        
                        dep_type = parts[0]  # brew or cask
                        dep_spec = parts[1].strip().strip('"\'')
                        
                        # Handle arguments and options
                        if "," in dep_spec:
                            dep_spec = dep_spec.split(",")[0].strip().strip('"\'')
                        
                        # Parse name and version
                        name = dep_spec
                        version = None
                        
                        # Create dependency object
                        dep = Dependency(
                            name=name,
                            version=version,
                            package_manager=self.dependency_type,
                            scope=DependencyScope.PROJECT,
                            metadata={
                                "type": dep_type,  # brew or cask
                            }
                        )
                        
                        project_deps.add_dependency(dep)
                    
        except Exception as e:
            print(f"Error parsing Brewfile: {e}")
    
    def install_project_dependencies(self, project_dir: Path) -> bool:
        """
        Install all dependencies for a project.
        
        Args:
            project_dir (Path): Project directory.
            
        Returns:
            bool: True if installation was successful, False otherwise.
        """
        brewfile_path = project_dir / "Brewfile"
        
        if brewfile_path.exists():
            # Install Brewfile dependencies using brew bundle
            cmd = ["brew", "bundle", "--file", str(brewfile_path)]
            result = self.cmd_executor.run_command(cmd)
            return result.success
        
        return False
    
    def get_dependency_tree(self, project_dir: Path) -> List[str]:
        """
        Get dependency tree for a project.
        
        Args:
            project_dir (Path): Project directory.
            
        Returns:
            List[str]: Dependency tree as a list of formatted strings.
        """
        # Homebrew doesn't have a built-in dependency tree visualization
        # so we'll create our own basic representation
        
        project_deps = self.get_project_dependencies(project_dir)
        dependencies = project_deps.get_all_dependencies()
        
        if not dependencies:
            return ["No dependencies found in this project"]
        
        result = ["Dependencies from Brewfile:"]
        
        # Group by type (brew or cask)
        brews = []
        casks = []
        others = []
        
        for dep in dependencies:
            dep_type = dep.metadata.get("type", "")
            if dep_type == "brew":
                brews.append(dep)
            elif dep_type == "cask":
                casks.append(dep)
            else:
                others.append(dep)
        
        # Add brews to the tree
        if brews:
            result.append("├── Formulae:")
            for i, brew in enumerate(brews):
                is_last = i == len(brews) - 1
                prefix = "│   └── " if is_last else "│   ├── "
                result.append(f"{prefix}{brew.name}{' (' + brew.version + ')' if brew.version else ''}")
                
                # Get actual dependencies for this formula
                info = self.get_package_info(brew.name)
                if info and info.dependencies:
                    deps_prefix = "    " if is_last else "│   "
                    result.append(f"{deps_prefix}    └── Dependencies:")
                    for j, dep_name in enumerate(info.dependencies):
                        is_dep_last = j == len(info.dependencies) - 1
                        dep_prefix = f"{deps_prefix}        └── " if is_dep_last else f"{deps_prefix}        ├── "
                        result.append(f"{dep_prefix}{dep_name}")
        
        # Add casks to the tree
        if casks:
            result.append("└── Casks:")
            for i, cask in enumerate(casks):
                is_last = i == len(casks) - 1
                prefix = "    └── " if is_last else "    ├── "
                result.append(f"{prefix}{cask.name}{' (' + cask.version + ')' if cask.version else ''}")
        
        return result 