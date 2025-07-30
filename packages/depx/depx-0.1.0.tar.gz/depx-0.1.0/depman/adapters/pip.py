"""
Adapter for the pip package manager.
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


class PipAdapter(PackageManagerAdapter):
    """Adapter for the pip package manager."""
    
    @property
    def name(self) -> str:
        """Return the name of the package manager."""
        return "pip"
    
    @property
    def dependency_type(self) -> DependencyType:
        """Return the dependency type."""
        return DependencyType.PIP
    
    def __init__(self):
        """Initialize the pip adapter."""
        self.cmd_executor = CommandExecutor()
        self._pip_command = self._find_pip_command()
    
    def _find_pip_command(self) -> List[str]:
        """
        Find the pip command to use.
        
        Returns:
            List[str]: Command parts for pip.
        """
        # Try different pip commands in order of preference
        options = [
            ["pip"],
            ["pip3"],
            ["python", "-m", "pip"],
            ["python3", "-m", "pip"]
        ]
        
        for cmd in options:
            if self.cmd_executor.command_exists(cmd[0]):
                try:
                    # Check if the command works
                    result = self.cmd_executor.run_command(cmd + ["--version"])
                    if result.success:
                        return cmd
                except:
                    pass
        
        # Default to python3 -m pip even if it failed, as a last resort
        return ["python3", "-m", "pip"]
    
    def is_available(self) -> bool:
        """Check if pip is available on the system."""
        try:
            result = self.cmd_executor.run_command(self._pip_command + ["--version"])
            return result.success
        except:
            return False
    
    def install(self, package_name: str, version: Optional[str] = None, global_install: bool = True) -> bool:
        """
        Install a Python package using pip.
        
        Args:
            package_name (str): Name of the package to install.
            version (Optional[str], optional): Specific version to install. Defaults to None.
            global_install (bool, optional): Whether to install globally. Defaults to True.
            
        Returns:
            bool: True if installation was successful, False otherwise.
        """
        cmd = self._pip_command + ["install"]
        
        # Add version constraint if specified
        if version:
            package_spec = f"{package_name}=={version}"
        else:
            package_spec = package_name
        
        # Add user flag for non-global installs
        if not global_install:
            cmd.append("--user")
        
        cmd.append(package_spec)
        
        result = self.cmd_executor.run_command(cmd)
        return result.success
    
    def uninstall(self, package_name: str, global_install: bool = True) -> bool:
        """
        Uninstall a Python package using pip.
        
        Args:
            package_name (str): Name of the package to uninstall.
            global_install (bool, optional): Whether it's a global package. Defaults to True.
            
        Returns:
            bool: True if uninstallation was successful, False otherwise.
        """
        cmd = self._pip_command + ["uninstall", "--yes", package_name]
        
        result = self.cmd_executor.run_command(cmd)
        return result.success
    
    def upgrade(self, package_name: Optional[str] = None, global_install: bool = True) -> bool:
        """
        Upgrade a Python package or all packages using pip.
        
        Args:
            package_name (Optional[str], optional): Name of the package to upgrade. 
                                                  If None, upgrade all packages. Defaults to None.
            global_install (bool, optional): Whether it's a global package. Defaults to True.
            
        Returns:
            bool: True if upgrade was successful, False otherwise.
        """
        cmd = self._pip_command + ["install", "--upgrade"]
        
        # Add user flag for non-global installs
        if not global_install:
            cmd.append("--user")
        
        # Add package name or upgrade pip itself if None
        if package_name:
            cmd.append(package_name)
        else:
            # When upgrading all packages, first get list of outdated packages
            list_cmd = self._pip_command + ["list", "--outdated", "--format=json"]
            list_result = self.cmd_executor.run_command(list_cmd)
            
            if not list_result.success:
                return False
                
            try:
                outdated = json.loads(list_result.stdout)
                packages = [pkg["name"] for pkg in outdated]
                
                if not packages:
                    # No packages to upgrade
                    return True
                    
                cmd.extend(packages)
            except (json.JSONDecodeError, KeyError):
                # Fall back to upgrading pip itself if we can't parse the output
                cmd.append("pip")
        
        result = self.cmd_executor.run_command(cmd)
        return result.success
    
    def list_packages(self, global_packages: bool = True) -> List[Dependency]:
        """
        List all installed Python packages using pip.
        
        Args:
            global_packages (bool, optional): Whether to list global packages. Defaults to True.
            
        Returns:
            List[Dependency]: List of installed dependencies.
        """
        cmd = self._pip_command + ["list", "--format=json"]
        result = self.cmd_executor.run_command(cmd)
        
        if not result.success:
            return []
        
        dependencies = []
        try:
            packages = json.loads(result.stdout)
            
            for pkg in packages:
                name = pkg.get("name", "")
                version = pkg.get("version", "")
                
                # Get more info about the package
                info = self.get_package_info(name, global_packages)
                
                # If we couldn't get more info, create a basic dependency object
                if not info:
                    info = Dependency(
                        name=name,
                        version=version,
                        package_manager=self.dependency_type,
                        scope=DependencyScope.GLOBAL if global_packages else DependencyScope.PROJECT
                    )
                
                dependencies.append(info)
                
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing pip list output: {e}")
        
        return dependencies
    
    def get_package_info(self, package_name: str, global_package: bool = True) -> Optional[Dependency]:
        """
        Get information about an installed Python package.
        
        Args:
            package_name (str): Name of the package.
            global_package (bool, optional): Whether it's a global package. Defaults to True.
            
        Returns:
            Optional[Dependency]: Dependency information if found, None otherwise.
        """
        cmd = self._pip_command + ["show", package_name]
        result = self.cmd_executor.run_command(cmd)
        
        if not result.success:
            return None
        
        info = {}
        for line in result.stdout.split("\n"):
            if not line or ":" not in line:
                continue
                
            key, value = line.split(":", 1)
            key = key.strip().lower()
            value = value.strip()
            
            info[key] = value
        
        # Check if we got any information
        if not info:
            return None
        
        # Extract dependencies
        requires = info.get("requires", "")
        dependencies = set()
        if requires:
            for dep in requires.split(","):
                dep_name = dep.strip()
                if dep_name:
                    dependencies.add(dep_name)
        
        # Get package path
        location = info.get("location", "")
        path = Path(location) / package_name if location else None
        
        return Dependency(
            name=package_name,
            version=info.get("version", ""),
            description=info.get("summary", ""),
            package_manager=self.dependency_type,
            scope=DependencyScope.GLOBAL if global_package else DependencyScope.PROJECT,
            path=path,
            dependencies=dependencies,
            metadata={
                "author": info.get("author", ""),
                "license": info.get("license", ""),
                "homepage": info.get("home-page", ""),
            }
        )
    
    def get_package_path(self, package_name: str, global_package: bool = True) -> Optional[Path]:
        """
        Get the installation path of a Python package.
        
        Args:
            package_name (str): Name of the package.
            global_package (bool, optional): Whether it's a global package. Defaults to True.
            
        Returns:
            Optional[Path]: Path to the package if found, None otherwise.
        """
        package_info = self.get_package_info(package_name, global_package)
        return package_info.path if package_info else None
    
    def search_packages(self, query: str) -> List[Dict]:
        """
        Search for packages matching a query using pip.
        
        Args:
            query (str): Search query.
            
        Returns:
            List[Dict]: List of matching packages.
        """
        # PyPI doesn't have a direct search API through pip, so we'll try to get version info
        # and if that fails, use a minimal implementation
        cmd = self._pip_command + ["index", "versions", query]
        result = self.cmd_executor.run_command(cmd)
        
        if result.success:
            # Try to parse the output to get package information
            lines = result.stdout.strip().split("\n")
            for line in lines:
                if line.startswith(f"Found existing versions of {query}"):
                    # Found a matching package
                    return [{
                        "name": query,
                        "description": f"Python package: {query}",
                        "version": lines[-1].strip() if len(lines) > 1 else "unknown",
                    }]
        
        # Fallback to PyPI API search
        return self._search_pypi(query)
    
    def _search_pypi(self, query: str) -> List[Dict]:
        """
        Search for packages using PyPI API.
        
        Args:
            query (str): Search query.
            
        Returns:
            List[Dict]: List of matching packages.
        """
        # This would normally use the PyPI JSON API, but for simplicity
        # we'll just return a placeholder result here
        return [{
            "name": query,
            "description": "No direct search results available. Check https://pypi.org/search/",
            "version": "N/A",
        }]
    
    def can_handle_project(self, project_dir: Path) -> bool:
        """
        Check if this adapter can handle the Python project in the given directory.
        
        Args:
            project_dir (Path): Project directory.
            
        Returns:
            bool: True if this adapter can handle the project, False otherwise.
        """
        # Check for common Python project files
        return any(
            (project_dir / f).exists()
            for f in ["requirements.txt", "setup.py", "pyproject.toml"]
        )
    
    def get_config_file_patterns(self) -> List[str]:
        """
        Get patterns for identifying Python project config files.
        
        Returns:
            List[str]: List of glob patterns for config files.
        """
        return ["requirements.txt", "setup.py", "pyproject.toml"]
    
    def get_project_dependencies(self, project_dir: Path) -> ProjectDependencies:
        """
        Get all dependencies for a Python project.
        
        Args:
            project_dir (Path): Project directory.
            
        Returns:
            ProjectDependencies: Object containing all project dependencies.
        """
        project_deps = ProjectDependencies(
            project_path=project_dir,
            package_manager=self.dependency_type
        )
        
        # Check for requirements.txt
        req_file = project_dir / "requirements.txt"
        if req_file.exists():
            project_deps.config_file = req_file
            self._parse_requirements_txt(req_file, project_deps)
        
        # Check for setup.py
        setup_file = project_dir / "setup.py"
        if setup_file.exists():
            if not project_deps.config_file:  # Don't overwrite if we already found requirements.txt
                project_deps.config_file = setup_file
            # Parse setup.py dependencies (complex, simplified here)
            self._parse_setup_py(setup_file, project_deps)
        
        # Check for pyproject.toml
        pyproject_file = project_dir / "pyproject.toml"
        if pyproject_file.exists():
            if not project_deps.config_file:  # Don't overwrite if we already found other files
                project_deps.config_file = pyproject_file
            # Parse pyproject.toml (complex, simplified here)
            self._parse_pyproject_toml(pyproject_file, project_deps)
        
        return project_deps
    
    def _parse_requirements_txt(self, req_file: Path, project_deps: ProjectDependencies) -> None:
        """
        Parse a requirements.txt file to extract dependencies.
        
        Args:
            req_file (Path): Path to the requirements.txt file.
            project_deps (ProjectDependencies): Project dependencies to update.
        """
        try:
            with open(req_file, "r") as f:
                for line in f:
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith("#"):
                        continue
                        
                    # Skip options lines
                    if line.startswith("-"):
                        continue
                        
                    # Handle inline comments
                    if "#" in line:
                        line = line.split("#")[0].strip()
                    
                    # Parse requirements with versions
                    name = line
                    version = None
                    
                    # Extract version constraints
                    if "==" in line:
                        name, version = line.split("==", 1)
                    elif ">=" in line:
                        name, version = line.split(">=", 1)
                        version = f">={version}"
                    elif ">" in line:
                        name, version = line.split(">", 1)
                        version = f">{version}"
                    elif "<=" in line:
                        name, version = line.split("<=", 1)
                        version = f"<={version}"
                    elif "<" in line:
                        name, version = line.split("<", 1)
                        version = f"<{version}"
                    elif "~=" in line:
                        name, version = line.split("~=", 1)
                        version = f"~={version}"
                    
                    name = name.strip()
                    if version:
                        version = version.strip()
                    
                    # Create dependency object
                    dep = Dependency(
                        name=name,
                        version=version,
                        package_manager=self.dependency_type,
                        scope=DependencyScope.PROJECT
                    )
                    
                    project_deps.add_dependency(dep)
        except Exception as e:
            print(f"Error parsing requirements.txt: {e}")
    
    def _parse_setup_py(self, setup_file: Path, project_deps: ProjectDependencies) -> None:
        """
        Parse a setup.py file to extract dependencies.
        
        Args:
            setup_file (Path): Path to the setup.py file.
            project_deps (ProjectDependencies): Project dependencies to update.
        """
        # This is a complex task that would typically involve running the setup.py
        # file in a controlled environment to extract its dependencies.
        # For simplicity, we'll just do basic regex-based parsing.
        try:
            with open(setup_file, "r") as f:
                content = f.read()
                
            # Look for install_requires list
            match = re.search(r"install_requires\s*=\s*\[(.*?)\]", content, re.DOTALL)
            if match:
                requires_text = match.group(1)
                # Extract package names
                for pkg in re.finditer(r"['\"]([^'\"]+)['\"]", requires_text):
                    pkg_spec = pkg.group(1)
                    
                    # Parse package name and version
                    name = pkg_spec
                    version = None
                    
                    # Extract version constraints
                    if "==" in pkg_spec:
                        name, version = pkg_spec.split("==", 1)
                    elif ">=" in pkg_spec:
                        name, version = pkg_spec.split(">=", 1)
                        version = f">={version}"
                    elif ">" in pkg_spec:
                        name, version = pkg_spec.split(">", 1)
                        version = f">{version}"
                    elif "<=" in pkg_spec:
                        name, version = pkg_spec.split("<=", 1)
                        version = f"<={version}"
                    elif "<" in pkg_spec:
                        name, version = pkg_spec.split("<", 1)
                        version = f"<{version}"
                    elif "~=" in pkg_spec:
                        name, version = pkg_spec.split("~=", 1)
                        version = f"~={version}"
                    
                    name = name.strip()
                    if version:
                        version = version.strip()
                    
                    # Create dependency object
                    dep = Dependency(
                        name=name,
                        version=version,
                        package_manager=self.dependency_type,
                        scope=DependencyScope.PROJECT
                    )
                    
                    project_deps.add_dependency(dep)
        except Exception as e:
            print(f"Error parsing setup.py: {e}")
    
    def _parse_pyproject_toml(self, pyproject_file: Path, project_deps: ProjectDependencies) -> None:
        """
        Parse a pyproject.toml file to extract dependencies.
        
        Args:
            pyproject_file (Path): Path to the pyproject.toml file.
            project_deps (ProjectDependencies): Project dependencies to update.
        """
        try:
            # Try to import toml package, which might not be available
            try:
                import tomli
                
                with open(pyproject_file, "rb") as f:
                    pyproject = tomli.load(f)
                
                # Check if it's a Poetry project
                if "tool" in pyproject and "poetry" in pyproject["tool"]:
                    poetry_config = pyproject["tool"]["poetry"]
                    
                    if "dependencies" in poetry_config:
                        for name, spec in poetry_config["dependencies"].items():
                            if name == "python":
                                continue  # Skip python version constraint
                                
                            if isinstance(spec, str):
                                version = spec
                            elif isinstance(spec, dict) and "version" in spec:
                                version = spec["version"]
                            else:
                                version = None
                            
                            dep = Dependency(
                                name=name,
                                version=version,
                                package_manager=DependencyType.POETRY,
                                scope=DependencyScope.PROJECT
                            )
                            
                            project_deps.add_dependency(dep)
                
                # Check if it's a standard pyproject.toml with dependencies
                elif "project" in pyproject and "dependencies" in pyproject["project"]:
                    for dep_spec in pyproject["project"]["dependencies"]:
                        # Parse package name and version
                        name = dep_spec
                        version = None
                        
                        # Extract version constraints
                        if "==" in dep_spec:
                            name, version = dep_spec.split("==", 1)
                        elif ">=" in dep_spec:
                            name, version = dep_spec.split(">=", 1)
                            version = f">={version}"
                        elif ">" in dep_spec:
                            name, version = dep_spec.split(">", 1)
                            version = f">{version}"
                        elif "<=" in dep_spec:
                            name, version = dep_spec.split("<=", 1)
                            version = f"<={version}"
                        elif "<" in dep_spec:
                            name, version = dep_spec.split("<", 1)
                            version = f"<{version}"
                        elif "~=" in dep_spec:
                            name, version = dep_spec.split("~=", 1)
                            version = f"~={version}"
                        
                        name = name.strip()
                        if version:
                            version = version.strip()
                        
                        dep = Dependency(
                            name=name,
                            version=version,
                            package_manager=self.dependency_type,
                            scope=DependencyScope.PROJECT
                        )
                        
                        project_deps.add_dependency(dep)
            
            except ImportError:
                # If tomli is not available, use simple regex-based parsing
                with open(pyproject_file, "r") as f:
                    content = f.read()
                
                # Look for dependencies section in various formats
                for section in ["dependencies", "project.dependencies", "tool.poetry.dependencies"]:
                    match = re.search(fr"{section}\s*=\s*\[(.*?)\]", content, re.DOTALL)
                    if match:
                        deps_text = match.group(1)
                        # Extract package specs
                        for pkg in re.finditer(r"['\"]([^'\"]+)['\"]", deps_text):
                            pkg_spec = pkg.group(1)
                            
                            # Parse package name and version
                            name = pkg_spec
                            version = None
                            
                            # Extract version constraints
                            if "==" in pkg_spec:
                                name, version = pkg_spec.split("==", 1)
                            elif ">=" in pkg_spec:
                                name, version = pkg_spec.split(">=", 1)
                                version = f">={version}"
                            
                            name = name.strip()
                            if version:
                                version = version.strip()
                            
                            # Create dependency object
                            dep = Dependency(
                                name=name,
                                version=version,
                                package_manager=self.dependency_type,
                                scope=DependencyScope.PROJECT
                            )
                            
                            project_deps.add_dependency(dep)
        
        except Exception as e:
            print(f"Error parsing pyproject.toml: {e}")
    
    def install_project_dependencies(self, project_dir: Path) -> bool:
        """
        Install project dependencies.
        
        Args:
            project_dir (Path): Project directory.
            
        Returns:
            bool: True if installation was successful, False otherwise.
        """
        # Check for requirements.txt
        req_file = project_dir / "requirements.txt"
        if req_file.exists():
            cmd = self._pip_command + ["install", "-r", str(req_file)]
            result = self.cmd_executor.run_command(cmd)
            return result.success
        
        # Check for setup.py
        setup_file = project_dir / "setup.py"
        if setup_file.exists():
            cmd = self._pip_command + ["install", "-e", "."]
            result = self.cmd_executor.run_command(cmd, cwd=project_dir)
            return result.success
        
        # Check for pyproject.toml
        pyproject_file = project_dir / "pyproject.toml"
        if pyproject_file.exists():
            # Install the project in development mode
            cmd = self._pip_command + ["install", "."]
            result = self.cmd_executor.run_command(cmd, cwd=project_dir)
            return result.success
        
        return False
    
    def get_dependency_tree(self, project_dir: Path) -> List[str]:
        """
        Get dependency tree for a project.
        
        Args:
            project_dir (Path): Project directory.
            
        Returns:
            List[str]: Dependency tree as a list of strings.
        """
        # We'll use pipdeptree for this
        # First, make sure it's installed
        install_cmd = self._pip_command + ["install", "pipdeptree"]
        self.cmd_executor.run_command(install_cmd)
        
        # Then, get the dependency tree
        # We'll use Python's subprocess directly to get the output of pipdeptree
        try:
            # First try to run pipdeptree as a command
            result = subprocess.run(
                ["pipdeptree", "--local-only", "--json"], 
                capture_output=True, 
                text=True, 
                check=False
            )
            
            if result.returncode != 0:
                # If the command failed, try to run it as a module
                result = subprocess.run(
                    [*self._pip_command[:-1], "-m", "pipdeptree", "--local-only", "--json"], 
                    capture_output=True, 
                    text=True, 
                    check=False
                )
                
            if result.returncode == 0 and result.stdout:
                # Parse the JSON output to get a nice tree format
                tree_data = self._parse_pipdeptree_json(result.stdout)
                return tree_data
            else:
                return [f"Error generating dependency tree: {result.stderr}"]
                
        except Exception as e:
            return [f"Error generating dependency tree: {e}"]
    
    def _parse_pipdeptree_json(self, json_str: str) -> List[str]:
        """
        Parse the JSON output of pipdeptree.
        
        Args:
            json_str (str): JSON output from pipdeptree.
            
        Returns:
            List[str]: Formatted dependency tree as a list of strings.
        """
        try:
            tree_data = json.loads(json_str)
            result = []
            
            for pkg in tree_data:
                pkg_name = pkg.get("package", {}).get("project_name", "Unknown")
                pkg_version = pkg.get("package", {}).get("version", "Unknown")
                result.append(f"{pkg_name}=={pkg_version}")
                
                # Add dependencies with indentation
                self._add_dependencies(pkg.get("dependencies", []), result, indent=2)
                
            return result
        except Exception as e:
            return [f"Error parsing dependency tree: {e}"]
    
    def _add_dependencies(self, deps: List[Dict], result: List[str], indent: int = 2) -> None:
        """
        Add dependencies to the result list with indentation.
        
        Args:
            deps (List[Dict]): List of dependency dictionaries.
            result (List[str]): Result list to append to.
            indent (int, optional): Current indentation level. Defaults to 2.
        """
        for dep in deps:
            pkg_name = dep.get("package", {}).get("project_name", "Unknown")
            pkg_version = dep.get("package", {}).get("version", "Unknown")
            result.append(f"{' ' * indent}└── {pkg_name}=={pkg_version}")
            
            # Recursively add sub-dependencies with increased indentation
            self._add_dependencies(dep.get("dependencies", []), result, indent + 4) 