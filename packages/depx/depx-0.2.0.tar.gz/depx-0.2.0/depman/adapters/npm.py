"""
NPM package manager adapter for Node.js dependencies.
"""
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

from depman.adapters.base import PackageManagerAdapter
from depman.models.dependency import Dependency, DependencyType, DependencyScope, ProjectDependencies
from depman.utils.cmd_executor import CommandExecutor
from depman.utils.os_utils import OSUtils


class NpmAdapter(PackageManagerAdapter):
    """Adapter for NPM package manager."""

    def __init__(self):
        self._cmd_executor = CommandExecutor()
        self._os_utils = OSUtils()

    @property
    def name(self) -> str:
        """Return the name of the package manager."""
        return "npm"

    @property
    def dependency_type(self) -> DependencyType:
        """Return the dependency type."""
        return DependencyType.NPM

    def is_available(self) -> bool:
        """Check if npm is available on the system."""
        return self._cmd_executor.command_exists("npm")

    def install(self, package_name: str, version: Optional[str] = None, global_install: bool = True) -> bool:
        """
        Install a package using npm.
        
        Args:
            package_name (str): Name of the package to install.
            version (Optional[str], optional): Specific version to install. Defaults to None.
            global_install (bool, optional): Whether to install globally. Defaults to True.
            
        Returns:
            bool: True if installation was successful, False otherwise.
        """
        cmd = ["npm", "install"]
        
        if global_install:
            cmd.append("-g")
        
        if version:
            cmd.append(f"{package_name}@{version}")
        else:
            cmd.append(package_name)
            
        # Check if we need elevated privileges
        if global_install and self._os_utils.needs_sudo():
            cmd = self._os_utils.add_sudo_prefix(cmd)
            
        return self._cmd_executor.run_command(cmd).success

    def uninstall(self, package_name: str, global_install: bool = True) -> bool:
        """
        Uninstall a package using npm.
        
        Args:
            package_name (str): Name of the package to uninstall.
            global_install (bool, optional): Whether it's a global package. Defaults to True.
            
        Returns:
            bool: True if uninstallation was successful, False otherwise.
        """
        cmd = ["npm", "uninstall"]
        
        if global_install:
            cmd.append("-g")
            
        cmd.append(package_name)
        
        # Check if we need elevated privileges
        if global_install and self._os_utils.needs_sudo():
            cmd = self._os_utils.add_sudo_prefix(cmd)
            
        return self._cmd_executor.run_command(cmd).success

    def upgrade(self, package_name: Optional[str] = None, global_install: bool = True) -> bool:
        """
        Upgrade a package or all packages using npm.
        
        Args:
            package_name (Optional[str], optional): Name of the package to upgrade. 
                                                   If None, upgrade all packages. Defaults to None.
            global_install (bool, optional): Whether it's a global package. Defaults to True.
            
        Returns:
            bool: True if upgrade was successful, False otherwise.
        """
        if package_name:
            # For npm, updating a single package is the same as installing the latest version
            return self.install(package_name, global_install=global_install)
        else:
            # Update all packages
            cmd = ["npm", "update"]
            
            if global_install:
                cmd.append("-g")
                
            # Check if we need elevated privileges
            if global_install and self._os_utils.needs_sudo():
                cmd = self._os_utils.add_sudo_prefix(cmd)
                
            return self._cmd_executor.run_command(cmd).success

    def list_packages(self, global_packages: bool = True) -> List[Dependency]:
        """
        List all installed npm packages.
        
        Args:
            global_packages (bool, optional): Whether to list global packages. Defaults to True.
            
        Returns:
            List[Dependency]: List of installed dependencies.
        """
        cmd = ["npm", "list", "--json"]
        
        if global_packages:
            cmd.append("-g")
            
        # Check if we need elevated privileges for global packages
        if global_packages and self._os_utils.needs_sudo():
            cmd = self._os_utils.add_sudo_prefix(cmd)
            
        result = self._cmd_executor.run_command(cmd)
        if not result.success:
            return []
            
        try:
            packages_data = json.loads(result.stdout)
            dependencies = []
            
            if "dependencies" in packages_data:
                for name, info in packages_data["dependencies"].items():
                    # Extract version without leading v (e.g., v1.0.0 -> 1.0.0)
                    version = info.get("version", "").lstrip("v")
                    
                    dep = Dependency(
                        name=name,
                        package_manager=self.dependency_type,
                        scope=DependencyScope.GLOBAL if global_packages else DependencyScope.PROJECT,
                        version=version,
                    )
                    dependencies.append(dep)
                    
            return dependencies
            
        except (json.JSONDecodeError, KeyError):
            return []

    def get_package_info(self, package_name: str, global_package: bool = True) -> Optional[Dependency]:
        """
        Get information about an installed npm package.
        
        Args:
            package_name (str): Name of the package.
            global_package (bool, optional): Whether it's a global package. Defaults to True.
            
        Returns:
            Optional[Dependency]: Dependency information if found, None otherwise.
        """
        packages = self.list_packages(global_package)
        for package in packages:
            if package.name == package_name:
                return package
        return None

    def get_package_path(self, package_name: str, global_package: bool = True) -> Optional[Path]:
        """
        Get the installation path of a npm package.
        
        Args:
            package_name (str): Name of the package.
            global_package (bool, optional): Whether it's a global package. Defaults to True.
            
        Returns:
            Optional[Path]: Path to the package if found, None otherwise.
        """
        cmd = ["npm", "root"]
        
        if global_package:
            cmd.append("-g")
            
        # Check if we need elevated privileges for global packages
        if global_package and self._os_utils.needs_sudo():
            cmd = self._os_utils.add_sudo_prefix(cmd)
            
        result = self._cmd_executor.run_command(cmd)
        if not result.success:
            return None
        
        root_path = Path(result.stdout.strip())
        package_path = root_path / package_name
        
        if package_path.exists():
            return package_path
        return None

    def search_packages(self, query: str) -> List[Dict]:
        """
        Search for npm packages matching a query.
        
        Args:
            query (str): Search query.
            
        Returns:
            List[Dict]: List of matching packages.
        """
        cmd = ["npm", "search", "--json", query]
        result = self._cmd_executor.run_command(cmd)
        
        if not result.success:
            return []
            
        try:
            packages = json.loads(result.stdout)
            return [
                {
                    "name": pkg["name"],
                    "description": pkg.get("description", ""),
                    "version": pkg.get("version", ""),
                    "package_manager": self.name
                }
                for pkg in packages
            ]
        except (json.JSONDecodeError, KeyError):
            return []

    def can_handle_project(self, project_dir: Path) -> bool:
        """
        Check if this adapter can handle a Node.js project.
        
        Args:
            project_dir (Path): Project directory.
            
        Returns:
            bool: True if this adapter can handle the project, False otherwise.
        """
        package_json = project_dir / "package.json"
        return package_json.exists()

    def get_project_dependencies(self, project_dir: Path) -> ProjectDependencies:
        """
        Get all dependencies for a Node.js project.
        
        Args:
            project_dir (Path): Project directory.
            
        Returns:
            ProjectDependencies: Object containing all project dependencies.
        """
        package_json_path = project_dir / "package.json"
        if not package_json_path.exists():
            return ProjectDependencies(
                project_path=project_dir,
                package_manager=self.dependency_type,
                dependencies={}
            )
            
        try:
            with open(package_json_path, 'r') as file:
                package_data = json.load(file)
                
            dependencies = {}
            
            # Process regular dependencies
            if "dependencies" in package_data:
                for name, version_spec in package_data["dependencies"].items():
                    # Clean version specifier (remove ^, ~, etc.)
                    clean_version = re.sub(r'^[~^]', '', version_spec)
                    
                    dep = Dependency(
                        name=name,
                        package_manager=self.dependency_type,
                        scope=DependencyScope.PROJECT,
                        version=clean_version,
                        metadata={"is_dev": False}
                    )
                    dependencies[name] = dep
                    
            # Process dev dependencies
            if "devDependencies" in package_data:
                for name, version_spec in package_data["devDependencies"].items():
                    # Clean version specifier (remove ^, ~, etc.)
                    clean_version = re.sub(r'^[~^]', '', version_spec)
                    
                    dep = Dependency(
                        name=name,
                        package_manager=self.dependency_type,
                        scope=DependencyScope.PROJECT,
                        version=clean_version,
                        metadata={"is_dev": True}
                    )
                    dependencies[name] = dep
                    
            return ProjectDependencies(
                project_path=project_dir,
                package_manager=self.dependency_type,
                dependencies=dependencies,
                config_file=package_json_path
            )
            
        except (json.JSONDecodeError, IOError):
            return ProjectDependencies(
                project_path=project_dir,
                package_manager=self.dependency_type,
                dependencies={}
            )

    def install_project_dependencies(self, project_dir: Path) -> bool:
        """
        Install all dependencies for a Node.js project.
        
        Args:
            project_dir (Path): Project directory.
            
        Returns:
            bool: True if installation was successful, False otherwise.
        """
        package_json_path = project_dir / "package.json"
        if not package_json_path.exists():
            return False
            
        # Change to project directory
        original_dir = os.getcwd()
        os.chdir(project_dir)
        
        try:
            # Run npm install
            result = self._cmd_executor.run_command(["npm", "install"])
            return result.success
        finally:
            # Change back to original directory
            os.chdir(original_dir)

    def get_dependency_tree(self, project_dir: Path) -> List[str]:
        """
        Get dependency tree for a Node.js project.
        
        Args:
            project_dir (Path): Project directory.
            
        Returns:
            List[str]: Dependency tree as a list of formatted strings.
        """
        package_json_path = project_dir / "package.json"
        if not package_json_path.exists():
            return []
            
        # Change to project directory
        original_dir = os.getcwd()
        os.chdir(project_dir)
        
        try:
            # Run npm list
            result = self._cmd_executor.run_command(["npm", "list"])
            if result.success:
                return result.stdout.strip().split('\n')
            return []
        finally:
            # Change back to original directory
            os.chdir(original_dir)

    def get_config_file_patterns(self) -> List[str]:
        """
        Get patterns for identifying Node.js config files this adapter can handle.
        
        Returns:
            List[str]: List of glob patterns for config files.
        """
        return ["package.json", "package-lock.json", "npm-shrinkwrap.json"] 