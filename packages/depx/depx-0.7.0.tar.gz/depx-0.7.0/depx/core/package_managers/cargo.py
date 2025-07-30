"""
Cargo 包管理器实现
"""

import logging
from pathlib import Path
from typing import Optional

from .base import BasePackageManager, PackageManagerResult

logger = logging.getLogger(__name__)


class CargoManager(BasePackageManager):
    """Cargo 包管理器"""

    @property
    def name(self) -> str:
        return "cargo"

    @property
    def command(self) -> str:
        return "cargo"

    def is_available(self) -> bool:
        """检查 cargo 是否可用"""
        return self._is_command_available("cargo")

    def install(
        self, package_name: str, dev: bool = False, global_install: bool = False
    ) -> PackageManagerResult:
        """
        使用 cargo 安装包
        
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
                message="cargo 命令不可用",
                command="",
                error="cargo command not found"
            )

        # 构建命令
        if global_install:
            # 全局安装使用 cargo install
            cmd = ["cargo", "install", package_name]
        else:
            # 项目依赖使用 cargo add (需要 cargo-edit)
            cmd = ["cargo", "add", package_name]
            if dev:
                cmd.append("--dev")

        return self.run_command(cmd)

    def uninstall(
        self, package_name: str, global_uninstall: bool = False
    ) -> PackageManagerResult:
        """
        使用 cargo 卸载包
        
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
                message="cargo 命令不可用",
                command="",
                error="cargo command not found"
            )

        # 构建命令
        if global_uninstall:
            # 全局卸载使用 cargo uninstall
            cmd = ["cargo", "uninstall", package_name]
        else:
            # 项目依赖使用 cargo remove (需要 cargo-edit)
            cmd = ["cargo", "remove", package_name]

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
        if global_install:
            cmd = ["cargo", "install", package_name]
        else:
            cmd = ["cargo", "add", package_name]
            if dev:
                cmd.append("--dev")

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
        if global_uninstall:
            cmd = ["cargo", "uninstall", package_name]
        else:
            cmd = ["cargo", "remove", package_name]

        return " ".join(cmd)
