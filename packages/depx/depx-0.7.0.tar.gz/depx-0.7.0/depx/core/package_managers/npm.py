"""
NPM 包管理器实现
"""

import logging
from pathlib import Path
from typing import Optional

from .base import BasePackageManager, PackageManagerResult

logger = logging.getLogger(__name__)


class NPMManager(BasePackageManager):
    """NPM 包管理器"""

    @property
    def name(self) -> str:
        return "npm"

    @property
    def command(self) -> str:
        return "npm"

    def is_available(self) -> bool:
        """检查 npm 是否可用"""
        return self._is_command_available("npm")

    def install(
        self, package_name: str, dev: bool = False, global_install: bool = False
    ) -> PackageManagerResult:
        """
        使用 npm 安装包
        
        Args:
            package_name: 包名
            dev: 是否为开发依赖
            global_install: 是否全局安装
            
        Returns:
            操作结果
        """
        if not self.validate_package_name(package_name):
            return PackageManagerResult(
                success=False,
                message="无效的包名",
                command="",
                error="Invalid package name"
            )

        if not self.is_available():
            return PackageManagerResult(
                success=False,
                message="npm 命令不可用",
                command="",
                error="npm command not found"
            )

        # 构建命令
        cmd = ["npm", "install"]

        if global_install:
            cmd.append("--global")
        elif dev:
            cmd.append("--save-dev")
        else:
            cmd.append("--save")

        cmd.append(package_name)

        return self.run_command(cmd)

    def uninstall(
        self, package_name: str, global_uninstall: bool = False
    ) -> PackageManagerResult:
        """
        使用 npm 卸载包
        
        Args:
            package_name: 包名
            global_uninstall: 是否全局卸载
            
        Returns:
            操作结果
        """
        if not self.validate_package_name(package_name):
            return PackageManagerResult(
                success=False,
                message="无效的包名",
                command="",
                error="Invalid package name"
            )

        if not self.is_available():
            return PackageManagerResult(
                success=False,
                message="npm 命令不可用",
                command="",
                error="npm command not found"
            )

        # 构建命令
        cmd = ["npm", "uninstall"]

        if global_uninstall:
            cmd.append("--global")

        cmd.append(package_name)

        return self.run_command(cmd)

    def get_install_preview(
        self, package_name: str, dev: bool = False, global_install: bool = False
    ) -> str:
        """
        获取安装预览命令
        
        Args:
            package_name: 包名
            dev: 是否为开发依赖
            global_install: 是否全局安装
            
        Returns:
            预览命令字符串
        """
        cmd = ["npm", "install"]

        if global_install:
            cmd.append("--global")
        elif dev:
            cmd.append("--save-dev")
        else:
            cmd.append("--save")

        cmd.append(package_name)

        return " ".join(cmd)

    def get_uninstall_preview(
        self, package_name: str, global_uninstall: bool = False
    ) -> str:
        """
        获取卸载预览命令
        
        Args:
            package_name: 包名
            global_uninstall: 是否全局卸载
            
        Returns:
            预览命令字符串
        """
        cmd = ["npm", "uninstall"]

        if global_uninstall:
            cmd.append("--global")

        cmd.append(package_name)

        return " ".join(cmd)
