"""
Base abstract class for package manager adapters.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from depman.models.dependency import Dependency, DependencyType, ProjectDependencies


class PackageManagerAdapter(ABC):
    """Abstract base class for package manager adapters."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the package manager."""
        pass
    
    @property
    @abstractmethod
    def dependency_type(self) -> DependencyType:
        """Return the dependency type."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the package manager is available on the system."""
        pass
    
    @abstractmethod
    def install(self, package_name: str, version: Optional[str] = None, global_install: bool = True) -> bool:
        """
        Install a package.
        
        Args:
            package_name (str): Name of the package to install.
            version (Optional[str], optional): Specific version to install. Defaults to None.
            global_install (bool, optional): Whether to install globally. Defaults to True.
            
        Returns:
            bool: True if installation was successful, False otherwise.
        """
        pass
    
    @abstractmethod
    def uninstall(self, package_name: str, global_install: bool = True) -> bool:
        """
        Uninstall a package.
        
        Args:
            package_name (str): Name of the package to uninstall.
            global_install (bool, optional): Whether it's a global package. Defaults to True.
            
        Returns:
            bool: True if uninstallation was successful, False otherwise.
        """
        pass
    
    @abstractmethod
    def upgrade(self, package_name: Optional[str] = None, global_install: bool = True) -> bool:
        """
        Upgrade a package or all packages.
        
        Args:
            package_name (Optional[str], optional): Name of the package to upgrade. 
                                                   If None, upgrade all packages. Defaults to None.
            global_install (bool, optional): Whether it's a global package. Defaults to True.
            
        Returns:
            bool: True if upgrade was successful, False otherwise.
        """
        pass
    
    @abstractmethod
    def list_packages(self, global_packages: bool = True) -> List[Dependency]:
        """
        List all installed packages.
        
        Args:
            global_packages (bool, optional): Whether to list global packages. Defaults to True.
            
        Returns:
            List[Dependency]: List of installed dependencies.
        """
        pass
    
    @abstractmethod
    def get_package_info(self, package_name: str, global_package: bool = True) -> Optional[Dependency]:
        """
        Get information about an installed package.
        
        Args:
            package_name (str): Name of the package.
            global_package (bool, optional): Whether it's a global package. Defaults to True.
            
        Returns:
            Optional[Dependency]: Dependency information if found, None otherwise.
        """
        pass
    
    @abstractmethod
    def get_package_path(self, package_name: str, global_package: bool = True) -> Optional[Path]:
        """
        Get the installation path of a package.
        
        Args:
            package_name (str): Name of the package.
            global_package (bool, optional): Whether it's a global package. Defaults to True.
            
        Returns:
            Optional[Path]: Path to the package if found, None otherwise.
        """
        pass
    
    @abstractmethod
    def search_packages(self, query: str) -> List[Dict]:
        """
        Search for packages matching a query.
        
        Args:
            query (str): Search query.
            
        Returns:
            List[Dict]: List of matching packages.
        """
        pass
    
    @abstractmethod
    def can_handle_project(self, project_dir: Path) -> bool:
        """
        Check if this adapter can handle the project in the given directory.
        
        Args:
            project_dir (Path): Project directory.
            
        Returns:
            bool: True if this adapter can handle the project, False otherwise.
        """
        pass
    
    @abstractmethod
    def get_project_dependencies(self, project_dir: Path) -> ProjectDependencies:
        """
        Get all dependencies for a project.
        
        Args:
            project_dir (Path): Project directory.
            
        Returns:
            ProjectDependencies: Object containing all project dependencies.
        """
        pass
    
    @abstractmethod
    def install_project_dependencies(self, project_dir: Path) -> bool:
        """
        Install all dependencies for a project.
        
        Args:
            project_dir (Path): Project directory.
            
        Returns:
            bool: True if installation was successful, False otherwise.
        """
        pass
    
    @abstractmethod
    def get_dependency_tree(self, project_dir: Path) -> List[str]:
        """
        Get dependency tree for a project.
        
        Args:
            project_dir (Path): Project directory.
            
        Returns:
            List[str]: Dependency tree as a list of formatted strings.
        """
        pass
    
    def get_config_file_patterns(self) -> List[str]:
        """
        Get patterns for identifying config files this adapter can handle.
        
        Returns:
            List[str]: List of glob patterns for config files.
        """
        return [] 