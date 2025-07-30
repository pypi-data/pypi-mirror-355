"""
Operating system utilities for DepMan.
"""
import os
import sys
import platform
import logging
from pathlib import Path
from typing import Dict, Optional, List

from depman.utils.cmd_executor import CommandExecutor


class OSUtils:
    """Utility class for operating system operations."""
    
    def __init__(self):
        """Initialize the OS utilities."""
        self.logger = logging.getLogger("depman.os_utils")
        self.cmd_executor = CommandExecutor()
        self._os_info = None
    
    def get_os_info(self) -> Dict:
        """
        Get information about the operating system.
        
        Returns:
            Dict: Dictionary containing OS information.
        """
        if self._os_info is not None:
            return self._os_info
        
        system = platform.system().lower()
        info = {
            "system": system,
            "platform": sys.platform,
            "release": platform.release(),
            "version": platform.version(),
            "architecture": platform.machine(),
        }
        
        # Add distribution info for Linux
        if system == "linux":
            try:
                # Try using distro package if available
                import distro
                info["distribution"] = distro.id()
                info["distribution_version"] = distro.version()
                info["distribution_codename"] = distro.codename()
            except ImportError:
                # Fallback to os-release
                try:
                    with open("/etc/os-release") as f:
                        os_release = dict(line.strip().split("=", 1) for line in f if "=" in line)
                    info["distribution"] = os_release.get("ID", "").strip('"')
                    info["distribution_version"] = os_release.get("VERSION_ID", "").strip('"')
                    info["distribution_codename"] = os_release.get("VERSION_CODENAME", "").strip('"')
                except (FileNotFoundError, IOError):
                    info["distribution"] = "unknown"
                    info["distribution_version"] = "unknown"
                    info["distribution_codename"] = "unknown"
        
        # Add macOS specific info
        elif system == "darwin":
            macos_version = platform.mac_ver()[0]
            info["macos_version"] = macos_version
            
        # Add Windows specific info
        elif system == "windows":
            win_version = platform.win32_ver()
            info["windows_version"] = win_version[0]
            info["windows_edition"] = win_version[1]
            info["windows_build"] = win_version[2]
        
        self._os_info = info
        return info
    
    def is_linux(self) -> bool:
        """Check if the system is Linux."""
        return sys.platform.startswith('linux')
    
    def is_macos(self) -> bool:
        """Check if the system is macOS."""
        return sys.platform.startswith('darwin')
    
    def is_windows(self) -> bool:
        """Check if the system is Windows."""
        return sys.platform.startswith('win')
    
    def is_admin(self) -> bool:
        """
        Check if the process has administrator privileges.
        
        Returns:
            bool: True if has admin privileges, False otherwise.
        """
        if self.is_windows():
            try:
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            except Exception:
                return False
        else:
            # For Unix-based systems, check if UID is 0 (root)
            return os.geteuid() == 0
    
    def needs_sudo(self) -> bool:
        """
        Check if sudo is needed for operations.
        
        Returns:
            bool: True if sudo is needed, False otherwise.
        """
        if self.is_admin():
            # Already running as admin, no sudo needed
            return False
            
        if self.is_windows():
            # Windows doesn't use sudo
            return False
            
        # For Linux and macOS, check if /usr/local is writable by the current user
        # or if we're in a virtual environment
        if 'VIRTUAL_ENV' in os.environ:
            # In a virtual environment, we generally don't need sudo
            return False
            
        # Check if typical system directories are writable
        if self.is_macos():
            paths_to_check = ['/usr/local/bin', '/usr/local/lib']
        else:  # Linux
            paths_to_check = ['/usr/bin', '/usr/lib']
            
        for path in paths_to_check:
            if os.path.exists(path) and not os.access(path, os.W_OK):
                return True
                
        return False
    
    def add_sudo_prefix(self, cmd: list) -> list:
        """
        Add sudo prefix to a command if needed.
        
        Args:
            cmd (list): Command as a list.
            
        Returns:
            list: Command with sudo prefix if needed.
        """
        if self.needs_sudo():
            return ["sudo"] + cmd
        return cmd
    
    def get_home_dir(self) -> Path:
        """
        Get the user's home directory.
        
        Returns:
            Path: Path to the home directory.
        """
        return Path.home()
    
    def get_temp_dir(self) -> Path:
        """
        Get the temporary directory.
        
        Returns:
            Path: Path to the temp directory.
        """
        import tempfile
        return Path(tempfile.gettempdir())
    
    def get_package_manager(self) -> Optional[str]:
        """
        Detect the system package manager.
        
        Returns:
            Optional[str]: Name of the detected package manager, or None.
        """
        if self.is_linux():
            os_info = self.get_os_info()
            distro = os_info.get("distribution", "").lower()
            
            # Debian, Ubuntu and derivatives
            if distro in ["debian", "ubuntu", "linuxmint", "pop"]:
                return "apt"
            
            # RHEL, CentOS, Fedora
            if distro in ["rhel", "centos", "fedora", "rocky", "almalinux"]:
                # Check if dnf is available, otherwise use yum
                if self.cmd_executor.command_exists("dnf"):
                    return "dnf"
                return "yum"
            
            # Arch Linux and derivatives
            if distro in ["arch", "manjaro"]:
                return "pacman"
            
            # Try to detect by checking commands
            for pm in ["apt", "dnf", "yum", "pacman", "zypper"]:
                if self.cmd_executor.command_exists(pm):
                    return pm
        
        elif self.is_macos():
            if self.cmd_executor.command_exists("brew"):
                return "brew"
        
        elif self.is_windows():
            if self.cmd_executor.command_exists("choco"):
                return "choco"
            if self.cmd_executor.command_exists("scoop"):
                return "scoop"
        
        return None
    
    def run_as_admin(self, cmd):
        """
        Run a command with administrative privileges.
        
        Args:
            cmd: Command to run.
            
        Returns:
            CommandResult: Result of the command.
        """
        if self.is_admin():
            # Already admin, run directly
            return self.cmd_executor.run_command(cmd)
        
        self.logger.info("Requesting administrative privileges...")
        
        if self.is_linux() or self.is_macos():
            sudo_cmd = ["sudo"]
            if isinstance(cmd, list):
                full_cmd = sudo_cmd + cmd
            else:
                full_cmd = f"sudo {cmd}"
            return self.cmd_executor.run_command(full_cmd)
        
        elif self.is_windows():
            # On Windows, running as admin is complex and requires UAC
            import ctypes
            import tempfile
            import subprocess
            
            if isinstance(cmd, list):
                cmd_str = " ".join(cmd)
            else:
                cmd_str = cmd
            
            # Create a temporary batch file
            fd, temp_path = tempfile.mkstemp(suffix='.bat')
            try:
                with os.fdopen(fd, 'w') as f:
                    f.write(cmd_str)
                
                # Use ShellExecute to trigger UAC
                result = ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", "cmd.exe", f"/c {temp_path}", None, 1
                )
                
                # ShellExecute returns a value > 32 if successful
                if result <= 32:
                    self.logger.error(f"Failed to run as admin. Error code: {result}")
                    return self.cmd_executor.CommandResult(
                        returncode=1,
                        stdout='',
                        stderr=f'Failed to elevate privileges. Error code: {result}',
                        cmd=cmd_str,
                        success=False
                    )
                
                # Wait for the process to finish
                # Note: This is not perfect as we can't easily capture stdout/stderr
                # from the elevated process
                return self.cmd_executor.CommandResult(
                    returncode=0,
                    stdout='',
                    stderr='',
                    cmd=cmd_str,
                    success=True
                )
            finally:
                # Clean up the temporary file
                try:
                    os.unlink(temp_path)
                except:
                    pass
        
        return self.cmd_executor.CommandResult(
            returncode=1,
            stdout='',
            stderr='Unsupported platform for admin elevation',
            cmd=cmd if isinstance(cmd, str) else " ".join(cmd),
            success=False
        )

    def search_packages(self, query: str) -> List[Dict]:
        """
        Search for packages matching a query across all available package managers.
        
        Args:
            query (str): Search query.
            
        Returns:
            List[Dict]: List of matching packages with package manager info.
        """
        results = []
        
        # Search in all available adapters
        for adapter_type, adapter in self._adapters.items():
            try:
                adapter_results = adapter.search_packages(query)
                
                # Add package manager info to each result
                for result in adapter_results:
                    result['package_manager'] = adapter.name
                    results.append(result)
            except Exception as e:
                self.logger.error(f"Error searching in {adapter.name}: {e}")
        
        return results 