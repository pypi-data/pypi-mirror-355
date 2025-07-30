"""
Core dependency manager for DepMan.
"""
import importlib
import importlib.util
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Type, Any

from depman.adapters.base import PackageManagerAdapter
from depman.core.config import Config
from depman.models.dependency import Dependency, DependencyScope, DependencyType
from depman.utils.cmd_executor import CommandExecutor
from depman.utils.os_utils import OSUtils


class DependencyManager:
    """Core dependency manager class."""
    
    def __init__(self, config: Config):
        """
        Initialize the dependency manager.
        
        Args:
            config (Config): Configuration object.
        """
        self.config = config
        self.logger = logging.getLogger("depman.manager")
        self.cmd_executor = CommandExecutor()
        self.os_utils = OSUtils()
        
        # Dictionary of package manager adapters
        self._adapters: Dict[DependencyType, PackageManagerAdapter] = {}
        
        # Initialize adapters
        self._initialize_adapters()
    
    def _initialize_adapters(self):
        """Initialize package manager adapters."""
        # This will be populated dynamically based on available adapters
        self.logger.debug("Initializing package manager adapters")
        
        # First, try to auto-detect the OS package manager
        os_info = self.os_utils.get_os_info()
        system = os_info.get("system", "").lower()
        
        if system == "linux":
            distro = os_info.get("distribution", "").lower()
            if distro in ["debian", "ubuntu", "linuxmint", "pop"]:
                self._load_adapter("apt")
            elif distro in ["fedora", "rhel", "centos"]:
                self._load_adapter("dnf")
            elif distro in ["arch", "manjaro"]:
                self._load_adapter("pacman")
        elif system == "darwin":
            self._load_adapter("brew")
        elif system == "windows":
            self._load_adapter("choco")
        
        # Try to detect language-specific package managers
        for pm_name in [
            "npm", "yarn", "pip", "poetry", "maven", "gradle", "bundler", 
            "cargo", "composer", "nuget"
        ]:
            self._load_adapter(pm_name)
    
    def _load_adapter(self, adapter_name: str) -> Optional[PackageManagerAdapter]:
        """
        Load a package manager adapter.
        
        Args:
            adapter_name (str): Name of the adapter to load.
            
        Returns:
            Optional[PackageManagerAdapter]: The loaded adapter or None if not found.
        """
        try:
            # Try to import the adapter module
            module_name = f"depman.adapters.{adapter_name}"
            # Check if the module exists first
            self.logger.debug(f"Attempting to load adapter: {adapter_name} from {module_name}")
            if not self._module_exists(module_name):
                self.logger.debug(f"Adapter module {module_name} not found")
                return None
                
            self.logger.debug(f"Found module {module_name}, importing...")
            module = importlib.import_module(module_name)
            
            # Get the adapter class (assuming it follows naming convention)
            adapter_class_name = f"{adapter_name.capitalize()}Adapter"
            self.logger.debug(f"Looking for class {adapter_class_name} in {module_name}")
            adapter_class = getattr(module, adapter_class_name)
            
            # Instantiate the adapter
            self.logger.debug(f"Instantiating adapter class {adapter_class_name}")
            adapter = adapter_class()
            
            # Check if the adapter is available
            is_available = adapter.is_available()
            self.logger.debug(f"Adapter {adapter.name} availability: {is_available}")
            
            if is_available:
                self.logger.debug(f"Loaded adapter for {adapter.name} with dependency type {adapter.dependency_type}")
                self._adapters[adapter.dependency_type] = adapter
                return adapter
            else:
                self.logger.debug(f"Adapter {adapter.name} is not available on this system")
                return None
                
        except (ImportError, AttributeError, Exception) as e:
            self.logger.debug(f"Failed to load adapter {adapter_name}: {e}")
            return None
    
    def _module_exists(self, module_name: str) -> bool:
        """
        Check if a module exists.
        
        Args:
            module_name (str): Name of the module to check.
            
        Returns:
            bool: True if the module exists, False otherwise.
        """
        try:
            importlib.util.find_spec(module_name)
            return True
        except ModuleNotFoundError:
            return False
    
    def _get_adapter_for_project(self, project_dir: Path) -> Optional[PackageManagerAdapter]:
        """
        Get the appropriate adapter for a project.
        
        Args:
            project_dir (Path): Project directory.
            
        Returns:
            Optional[PackageManagerAdapter]: The appropriate adapter or None.
        """
        for adapter in self._adapters.values():
            if adapter.can_handle_project(project_dir):
                return adapter
        return None
    
    def install(self, package_name: str, version: Optional[str] = None, project: bool = False, pkg_manager: Optional[str] = None) -> bool:
        """
        Install a package.
        
        Args:
            package_name (str): Name of the package to install.
            version (Optional[str], optional): Specific version to install. Defaults to None.
            project (bool, optional): Whether to install for the project. Defaults to False.
            pkg_manager (Optional[str], optional): Specific package manager to use. Defaults to None.
            
        Returns:
            bool: True if installation was successful, False otherwise.
            
        Raises:
            ValueError: If no adapter is available for the operation.
        """
        if project:
            # For project installation, determine the adapter from the current directory
            project_dir = Path.cwd()
            
            # If pkg_manager is specified, try to find that specific adapter
            if pkg_manager:
                for adapter in self._adapters.values():
                    if adapter.name.lower() == pkg_manager.lower():
                        if adapter.can_handle_project(project_dir):
                            self.logger.info(f"Installing {package_name} for project using {adapter.name}")
                            return adapter.install(package_name, version=version, global_install=False)
                        else:
                            raise ValueError(f"The project doesn't seem to be a {adapter.name} project")
                
                # If we get here, the specified manager wasn't found
                raise ValueError(f"Package manager '{pkg_manager}' not found or not supported")
            
            # Otherwise use the default adapter for the project
            adapter = self._get_adapter_for_project(project_dir)
            if not adapter:
                raise ValueError(f"No package manager detected for project in {project_dir}")
                
            self.logger.info(f"Installing {package_name} for project using {adapter.name}")
            return adapter.install(package_name, version=version, global_install=False)
        else:
            # For global installation
            if pkg_manager:
                # Use the specified package manager
                for adapter in self._adapters.values():
                    if adapter.name.lower() == pkg_manager.lower():
                        self.logger.info(f"Installing {package_name} globally using {adapter.name}")
                        return adapter.install(package_name, version=version, global_install=True)
                
                # If we get here, the specified manager wasn't found
                raise ValueError(f"Package manager '{pkg_manager}' not found or not supported")
            else:
                # Try to determine the appropriate adapter
                adapter_type = self._get_adapter_type_for_package(package_name)
                if adapter_type and adapter_type in self._adapters:
                    adapter = self._adapters[adapter_type]
                    self.logger.info(f"Installing {package_name} globally using {adapter.name}")
                    return adapter.install(package_name, version=version, global_install=True)
                else:
                    raise ValueError(f"No package manager found for package {package_name}")
    
    def _get_adapter_type_for_package(self, package_name: str) -> Optional[DependencyType]:
        """
        Determine the appropriate adapter type for a package.
        
        Args:
            package_name (str): Name of the package.
            
        Returns:
            Optional[DependencyType]: The dependency type or None.
        """
        # This is a simplification - in a real implementation, you would need
        # a more sophisticated way to determine the appropriate adapter
        
        # Check user's preferred adapter for this package type
        preferred = self.config.get(f"package_managers.preferred.{package_name}")
        if preferred:
            try:
                return DependencyType(preferred)
            except ValueError:
                self.logger.warning(f"Invalid preferred package manager: {preferred}")
        
        # Try to guess based on package name or format
        if package_name.startswith("python-"):
            return DependencyType.PIP
        elif package_name.startswith("node-"):
            return DependencyType.NPM
        elif package_name.endswith(".deb"):
            return DependencyType.APT
        elif package_name.endswith(".rpm"):
            return DependencyType.YUM
        
        # Default to the system package manager if available
        system = self.os_utils.get_os_info().get("system", "").lower()
        if system == "linux":
            distro = self.os_utils.get_os_info().get("distribution", "").lower()
            if distro in ["debian", "ubuntu", "linuxmint", "pop"]:
                return DependencyType.APT
            elif distro in ["fedora", "rhel", "centos"]:
                return DependencyType.DNF
            elif distro in ["arch", "manjaro"]:
                return DependencyType.PACMAN
        elif system == "darwin":
            return DependencyType.HOMEBREW
        elif system == "windows":
            return DependencyType.CHOCOLATEY
        
        # Try all available adapters
        for adapter_type in self._adapters:
            if self._adapters[adapter_type].is_available():
                return adapter_type
                
        return None
    
    def uninstall(self, package_name: str, project: bool = False) -> bool:
        """
        Uninstall a package.
        
        Args:
            package_name (str): Name of the package to uninstall.
            project (bool, optional): Whether it's a project package. Defaults to False.
            
        Returns:
            bool: True if uninstallation was successful, False otherwise.
            
        Raises:
            ValueError: If no adapter is available for the operation.
        """
        if project:
            # For project uninstallation, determine the adapter from the current directory
            project_dir = Path.cwd()
            adapter = self._get_adapter_for_project(project_dir)
            if not adapter:
                raise ValueError(f"No package manager detected for project in {project_dir}")
                
            self.logger.info(f"Uninstalling {package_name} from project using {adapter.name}")
            return adapter.uninstall(package_name, global_install=False)
        else:
            # Try to find which adapter has this package installed
            installed_adapter = None
            for adapter in self._adapters.values():
                if adapter.get_package_info(package_name, global_package=True):
                    installed_adapter = adapter
                    break
            
            if not installed_adapter:
                adapter_type = self._get_adapter_type_for_package(package_name)
                if adapter_type and adapter_type in self._adapters:
                    installed_adapter = self._adapters[adapter_type]
                else:
                    raise ValueError(f"Package {package_name} is not installed or no package manager found")
            
            self.logger.info(f"Uninstalling {package_name} globally using {installed_adapter.name}")
            return installed_adapter.uninstall(package_name, global_install=True)
    
    def upgrade(self, package_name: str, project: bool = False) -> bool:
        """
        Upgrade a package.
        
        Args:
            package_name (str): Name of the package to upgrade.
            project (bool, optional): Whether it's a project package. Defaults to False.
            
        Returns:
            bool: True if upgrade was successful, False otherwise.
            
        Raises:
            ValueError: If no adapter is available for the operation.
        """
        if project:
            # For project upgrade, determine the adapter from the current directory
            project_dir = Path.cwd()
            adapter = self._get_adapter_for_project(project_dir)
            if not adapter:
                raise ValueError(f"No package manager detected for project in {project_dir}")
                
            self.logger.info(f"Upgrading {package_name} in project using {adapter.name}")
            return adapter.upgrade(package_name, global_install=False)
        else:
            # Try to find which adapter has this package installed
            installed_adapter = None
            for adapter in self._adapters.values():
                if adapter.get_package_info(package_name, global_package=True):
                    installed_adapter = adapter
                    break
            
            if not installed_adapter:
                adapter_type = self._get_adapter_type_for_package(package_name)
                if adapter_type and adapter_type in self._adapters:
                    installed_adapter = self._adapters[adapter_type]
                else:
                    raise ValueError(f"Package {package_name} is not installed or no package manager found")
            
            self.logger.info(f"Upgrading {package_name} globally using {installed_adapter.name}")
            return installed_adapter.upgrade(package_name, global_install=True)
    
    def upgrade_all(self, project: bool = False) -> bool:
        """
        Upgrade all packages.
        
        Args:
            project (bool, optional): Whether to upgrade project packages. Defaults to False.
            
        Returns:
            bool: True if all upgrades were successful, False otherwise.
        """
        if project:
            # For project upgrade, determine the adapter from the current directory
            project_dir = Path.cwd()
            adapter = self._get_adapter_for_project(project_dir)
            if not adapter:
                raise ValueError(f"No package manager detected for project in {project_dir}")
                
            self.logger.info(f"Upgrading all packages in project using {adapter.name}")
            return adapter.upgrade(global_install=False)
        else:
            # Upgrade all packages from all adapters
            success = True
            for adapter in self._adapters.values():
                if adapter.is_available():
                    self.logger.info(f"Upgrading all packages for {adapter.name}")
                    if not adapter.upgrade(global_install=True):
                        success = False
            return success
    
    def install_from_file(self, file_path: str) -> bool:
        """
        Install dependencies from a file.
        
        Args:
            file_path (str): Path to the dependency file.
            
        Returns:
            bool: True if installation was successful, False otherwise.
            
        Raises:
            ValueError: If no adapter can handle the file.
        """
        file_path = Path(file_path)
        project_dir = file_path.parent
        
        # Try to find an adapter that can handle this file
        for adapter in self._adapters.values():
            patterns = adapter.get_config_file_patterns()
            if not patterns:  # Skip adapters that don't define patterns
                continue
                
            for pattern in patterns:
                if file_path.match(pattern):
                    self.logger.info(f"Installing dependencies from {file_path} using {adapter.name}")
                    return adapter.install_project_dependencies(project_dir)
        
        raise ValueError(f"No package manager can handle the file: {file_path}")
    
    def install_all_project_dependencies(self) -> bool:
        """
        Install all dependencies for the current project.
        
        Returns:
            bool: True if installation was successful, False otherwise.
            
        Raises:
            ValueError: If no adapter is available for the project.
        """
        project_dir = Path.cwd()
        adapter = self._get_adapter_for_project(project_dir)
        if not adapter:
            raise ValueError(f"No package manager detected for project in {project_dir}")
            
        self.logger.info(f"Installing all dependencies for project using {adapter.name}")
        return adapter.install_project_dependencies(project_dir)
    
    def scan_project(self, project_dir: Path, security: bool = False) -> List[Dict]:
        """
        Scan a project for dependencies.
        
        Args:
            project_dir (Path): Project directory.
            security (bool, optional): Whether to perform a security scan. Defaults to False.
            
        Returns:
            List[Dict]: List of dependency information.
        """
        results = []
        
        # Find adapters that can handle this project
        handlers = []
        for adapter in self._adapters.values():
            if adapter.can_handle_project(project_dir):
                handlers.append(adapter)
        
        if not handlers:
            self.logger.info(f"No package manager detected for project in {project_dir}")
            return []
        
        # Get dependencies from each adapter
        for adapter in handlers:
            try:
                self.logger.info(f"Scanning project dependencies using {adapter.name}")
                project_deps = adapter.get_project_dependencies(project_dir)
                
                for dep in project_deps.get_all_dependencies():
                    results.append(dep.to_dict())
                    
                # Add basic project info
                results.append({
                    "project_name": project_dir.name,
                    "package_manager": adapter.name,
                    "dependency_count": len(project_deps.get_all_dependencies()),
                    "config_file": str(project_deps.config_file) if project_deps.config_file else None,
                })
                
            except Exception as e:
                self.logger.error(f"Error scanning project with {adapter.name}: {e}")
        
        # TODO: Implement security scanning if requested
        if security:
            self.logger.info("Security scanning not implemented yet")
        
        return results
    
    def scan_global(self, security: bool = False) -> List[Dict]:
        """
        Scan global dependencies.
        
        Args:
            security (bool, optional): Whether to perform a security scan. Defaults to False.
            
        Returns:
            List[Dict]: List of dependency information.
        """
        results = []
        
        # Get dependencies from each adapter
        for adapter in self._adapters.values():
            if not adapter.is_available():
                continue
                
            try:
                self.logger.info(f"Scanning global dependencies using {adapter.name}")
                deps = adapter.list_packages(global_packages=True)
                
                for dep in deps:
                    results.append(dep.to_dict())
                    
            except Exception as e:
                self.logger.error(f"Error scanning global dependencies with {adapter.name}: {e}")
        
        # TODO: Implement security scanning if requested
        if security:
            self.logger.info("Security scanning not implemented yet")
        
        return results
    
    def get_package_path(self, package_name: str) -> Optional[str]:
        """
        Get the installation path of a package.
        
        Args:
            package_name (str): Name of the package.
            
        Returns:
            Optional[str]: Path to the package if found, None otherwise.
        """
        # Try all adapters
        for adapter in self._adapters.values():
            if not adapter.is_available():
                continue
                
            path = adapter.get_package_path(package_name, global_package=True)
            if path:
                return str(path)
                
        # Try project-specific adapters
        project_dir = Path.cwd()
        adapter = self._get_adapter_for_project(project_dir)
        if adapter:
            path = adapter.get_package_path(package_name, global_package=False)
            if path:
                return str(path)
                
        return None
    
    def list_project_dependencies(self) -> List[Dict]:
        """
        List project dependencies.
        
        Returns:
            List[Dict]: List of dependency information.
        """
        project_dir = Path.cwd()
        adapter = self._get_adapter_for_project(project_dir)
        if not adapter:
            self.logger.info(f"No package manager detected for project in {project_dir}")
            return []
            
        try:
            self.logger.info(f"Listing project dependencies using {adapter.name}")
            project_deps = adapter.get_project_dependencies(project_dir)
            
            return [dep.to_dict() for dep in project_deps.get_all_dependencies()]
                
        except Exception as e:
            self.logger.error(f"Error listing project dependencies: {e}")
            return []
    
    def list_global_dependencies(self) -> List[Dict]:
        """
        List global dependencies.
        
        Returns:
            List[Dict]: List of dependency information.
        """
        results = []
        
        # Get dependencies from each adapter
        for adapter in self._adapters.values():
            if not adapter.is_available():
                continue
                
            try:
                deps = adapter.list_packages(global_packages=True)
                
                for dep in deps:
                    results.append(dep.to_dict())
                    
            except Exception as e:
                self.logger.error(f"Error listing global dependencies with {adapter.name}: {e}")
        
        return results
    
    def get_project_dependency_tree(self) -> List[str]:
        """
        Get dependency tree for the current project.
        
        Returns:
            List[str]: Dependency tree as a list of formatted strings.
        """
        project_dir = Path.cwd()
        adapter = self._get_adapter_for_project(project_dir)
        if not adapter:
            self.logger.info(f"No package manager detected for project in {project_dir}")
            return []
            
        try:
            self.logger.info(f"Getting dependency tree using {adapter.name}")
            return adapter.get_dependency_tree(project_dir)
                
        except Exception as e:
            self.logger.error(f"Error getting dependency tree: {e}")
            return []
    
    def search_packages(self, query: str) -> List[Dict]:
        """
        Search for packages matching a query.
        
        Args:
            query (str): Search query.
            
        Returns:
            List[Dict]: List of matching packages.
        """
        results = []
        
        # Search using all available adapters
        for adapter in self._adapters.values():
            if not adapter.is_available():
                continue
                
            try:
                adapter_results = adapter.search_packages(query)
                
                for result in adapter_results:
                    result["package_manager"] = adapter.name
                    results.append(result)
                    
            except Exception as e:
                self.logger.error(f"Error searching packages with {adapter.name}: {e}")
        
        return results 