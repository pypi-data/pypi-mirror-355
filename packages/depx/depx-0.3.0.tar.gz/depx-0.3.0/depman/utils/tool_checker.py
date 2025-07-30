"""
Tool availability checker for DepMan.
This module provides utilities for checking if required command line tools are available.
"""
from typing import Dict, List, Optional, Set, Tuple
import shutil
import logging
from pathlib import Path


class ToolAvailabilityChecker:
    """Utility class for checking if required tools are available."""
    
    def __init__(self):
        """Initialize the tool availability checker."""
        self.logger = logging.getLogger("depman.tool_checker")
        self._tool_availability_cache = {}  # Cache for tool availability checks
        
    def check_tool(self, tool_name: str) -> bool:
        """
        Check if a command-line tool is available in the system PATH.
        
        Args:
            tool_name (str): Name of the tool to check.
            
        Returns:
            bool: True if the tool is available, False otherwise.
        """
        # Use cache if available
        if tool_name in self._tool_availability_cache:
            return self._tool_availability_cache[tool_name]
        
        # 使用更可靠的方法检查工具是否可用
        import platform
        
        # 首先尝试使用shutil.which（跨平台）
        is_available = shutil.which(tool_name) is not None
        
        # 如果shutil.which无法找到，尝试使用平台特定的命令进行回退检查
        if not is_available:
            is_windows = platform.system().lower() == 'windows'
            try:
                import subprocess
                if is_windows:
                    # 在Windows上使用where命令
                    result = subprocess.run(['where', tool_name], 
                                           stdout=subprocess.PIPE, 
                                           stderr=subprocess.PIPE, 
                                           text=True, 
                                           check=False)
                else:
                    # 在Unix系统上使用which命令
                    result = subprocess.run(['which', tool_name], 
                                           stdout=subprocess.PIPE, 
                                           stderr=subprocess.PIPE, 
                                           text=True, 
                                           check=False)
                is_available = result.returncode == 0
            except Exception:
                # 如果出现任何错误，就认为工具不可用
                is_available = False
        
        # 缓存结果
        self._tool_availability_cache[tool_name] = is_available
        
        if not is_available:
            self.logger.debug(f"Tool '{tool_name}' is not available in the PATH")
        
        return is_available
    
    def check_tools(self, tool_names: List[str]) -> Dict[str, bool]:
        """
        Check if multiple command-line tools are available.
        
        Args:
            tool_names (List[str]): List of tool names to check.
            
        Returns:
            Dict[str, bool]: Dictionary mapping tool names to availability status.
        """
        return {tool: self.check_tool(tool) for tool in tool_names}
    
    def get_missing_tools(self, tool_names: List[str]) -> List[str]:
        """
        Get a list of tools that are not available.
        
        Args:
            tool_names (List[str]): List of tool names to check.
            
        Returns:
            List[str]: List of tool names that are not available.
        """
        availability = self.check_tools(tool_names)
        return [tool for tool, available in availability.items() if not available]
    
    def get_installation_instructions(self, tool_name: str) -> str:
        """
        Get installation instructions for a tool.
        
        Args:
            tool_name (str): Name of the tool.
            
        Returns:
            str: Installation instructions for the tool.
        """
        instructions = {
            # Python 相关
            "pip": "安装 pip: https://pip.pypa.io/en/stable/installation/",
            "pip3": "安装 pip3: https://pip.pypa.io/en/stable/installation/",
            "python": "安装 Python: https://www.python.org/downloads/",
            "python3": "安装 Python 3: https://www.python.org/downloads/",
            "poetry": "安装 Poetry: https://python-poetry.org/docs/#installation",
            "pipenv": "安装 Pipenv: pip install pipenv",
            
            # JavaScript/Node.js 相关
            "npm": "安装 npm: https://docs.npmjs.com/downloading-and-installing-node-js-and-npm",
            "yarn": "安装 yarn: https://classic.yarnpkg.com/en/docs/install",
            "pnpm": "安装 pnpm: https://pnpm.io/installation",
            "node": "安装 Node.js: https://nodejs.org/en/download/",
            
            # 系统包管理器
            "brew": "安装 Homebrew: https://brew.sh/",
            "apt": "apt 通常预装在基于 Debian 的 Linux 发行版中",
            "apt-get": "apt-get 通常预装在基于 Debian 的 Linux 发行版中",
            "yum": "yum 通常预装在基于 RPM 的 Linux 发行版中",
            "dnf": "dnf 通常预装在较新的基于 RPM 的 Linux 发行版中",
            "pacman": "pacman 通常预装在基于 Arch 的 Linux 发行版中",
            "choco": "安装 Chocolatey: https://chocolatey.org/install",
            "scoop": "安装 Scoop: https://scoop.sh/",
            
            # 其他语言包管理器
            "cargo": "安装 Cargo (Rust): https://doc.rust-lang.org/cargo/getting-started/installation.html",
            "rustup": "安装 Rustup (Rust): https://rustup.rs/",
            "go": "安装 Go: https://golang.org/doc/install",
            "mvn": "安装 Maven: https://maven.apache.org/install.html",
            "maven": "安装 Maven: https://maven.apache.org/install.html",
            "gradle": "安装 Gradle: https://gradle.org/install/",
            "composer": "安装 Composer (PHP): https://getcomposer.org/download/",
            "gem": "安装 RubyGems: https://rubygems.org/pages/download",
            "bundle": "安装 Bundler (Ruby): gem install bundler",
            "bundler": "安装 Bundler (Ruby): gem install bundler",
            "dotnet": "安装 .NET SDK: https://dotnet.microsoft.com/download",
            "nuget": "安装 NuGet CLI: https://docs.microsoft.com/en-us/nuget/install-nuget-client-tools",
            "swift": "安装 Swift: https://swift.org/download/",
            "dart": "安装 Dart SDK: https://dart.dev/get-dart",
            "pub": "安装 Dart Pub (包含在 Dart SDK 中): https://dart.dev/get-dart",
            "flutter": "安装 Flutter: https://flutter.dev/docs/get-started/install",
        }
        
        return instructions.get(tool_name, f"请安装 {tool_name} 以使用此功能")
    
    def get_formatted_missing_tools_message(self, tools: List[str]) -> str:
        """
        Get a formatted message for missing tools with installation instructions.
        
        Args:
            tools (List[str]): List of missing tool names.
            
        Returns:
            str: Formatted message with installation instructions.
        """
        if not tools:
            return ""
            
        message = "以下工具在您的系统中不可用:\n"
        for tool in tools:
            message += f"- {tool}: {self.get_installation_instructions(tool)}\n"
        
        return message 