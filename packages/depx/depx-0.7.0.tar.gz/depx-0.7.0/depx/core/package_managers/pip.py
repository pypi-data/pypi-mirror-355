"""
Pip 包管理器实现
"""

import logging
from pathlib import Path
from typing import Optional

from .base import BasePackageManager, PackageManagerResult

logger = logging.getLogger(__name__)


class PipManager(BasePackageManager):
    """Pip 包管理器"""

    @property
    def name(self) -> str:
        return "pip"

    @property
    def command(self) -> str:
        return "pip"

    def is_available(self) -> bool:
        """检查 pip 是否可用"""
        return self._is_command_available("pip") or self._is_command_available(
            "pip3"
        )

    def _get_pip_command(self) -> str:
        """获取可用的 pip 命令"""
        if self._is_command_available("pip"):
            return "pip"
        elif self._is_command_available("pip3"):
            return "pip3"
        else:
            return "pip"

    def install(
        self, package_name: str, dev: bool = False, global_install: bool = False
    ) -> PackageManagerResult:
        """
        使用 pip 安装包
        
        Args:
            package_name: 包名
            dev: 是否为开发依赖（pip 不区分，但会记录）
            global_install: 是否全局安装（pip 默认全局，除非在虚拟环境中）
            
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
                message="pip 命令不可用",
                command="",
                error="pip command not found"
            )

        # 构建命令
        pip_cmd = self._get_pip_command()
        cmd = [pip_cmd, "install", package_name]

        return self.run_command(cmd)

    def uninstall(
        self, package_name: str, global_uninstall: bool = False
    ) -> PackageManagerResult:
        """
        使用 pip 卸载包
        
        Args:
            package_name: 包名
            global_uninstall: 是否全局卸载（pip 默认全局，除非在虚拟环境中）
            
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
                message="pip 命令不可用",
                command="",
                error="pip command not found"
            )

        # 构建命令
        pip_cmd = self._get_pip_command()
        cmd = [pip_cmd, "uninstall", "--yes", package_name]

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
        pip_cmd = self._get_pip_command()
        cmd = [pip_cmd, "install", package_name]
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
        pip_cmd = self._get_pip_command()
        cmd = [pip_cmd, "uninstall", "--yes", package_name]
        return " ".join(cmd)
