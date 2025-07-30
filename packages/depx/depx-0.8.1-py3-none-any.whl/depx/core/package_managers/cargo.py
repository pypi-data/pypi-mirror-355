"""
Cargo 包管理器实现
"""

import logging
from pathlib import Path
from typing import List, Optional

from .base import (
    BasePackageManager,
    OutdatedPackage,
    PackageManagerResult,
    SearchResult,
    UpdateResult,
)

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

    def search(self, package_name: str, limit: int = 10) -> List[SearchResult]:
        """
        使用 cargo 搜索包

        Args:
            package_name: 包名或关键词
            limit: 限制结果数量

        Returns:
            搜索结果列表
        """
        if not self.is_available():
            return []

        try:
            # 使用 cargo search 命令
            cmd = ["cargo", "search", package_name, "--registry", "crates-io", "--limit", str(limit)]
            result = self.run_command(cmd, timeout=30)

            if result.success:
                # 解析 cargo search 的输出
                return self._parse_cargo_search_output(result.output)

            return []

        except Exception as e:
            logger.error(f"cargo search 异常: {e}")
            return []

    def check_outdated(self) -> List[OutdatedPackage]:
        """
        检查过时的包

        Returns:
            过时包列表
        """
        # Cargo 没有内置的 outdated 命令，需要 cargo-outdated 插件
        # 这里提供基本框架
        return []

    def update_package(
        self, package_name: Optional[str] = None, dev: bool = False
    ) -> UpdateResult:
        """
        更新包

        Args:
            package_name: 包名，None 表示更新所有包
            dev: 是否包括开发依赖

        Returns:
            更新结果
        """
        if not self.is_available():
            return UpdateResult(
                success=False,
                message="cargo 命令不可用",
                updated_packages=[],
                error="cargo command not found"
            )

        # 构建更新命令
        if package_name:
            cmd = ["cargo", "update", "-p", package_name]
        else:
            cmd = ["cargo", "update"]

        result = self.run_command(cmd, timeout=120)

        return UpdateResult(
            success=result.success,
            message="更新完成" if result.success else f"更新失败: {result.message}",
            updated_packages=[],  # 需要解析输出来获取实际更新的包
            command=result.command,
            output=result.output,
            error=result.error
        )

    def _parse_cargo_search_output(self, output: str) -> List[SearchResult]:
        """解析 cargo search 命令的输出"""
        results = []
        lines = output.strip().split('\n')

        for line in lines:
            if '=' in line and '#' in line:
                # 格式: package_name = "version"    # description
                parts = line.split('#', 1)
                if len(parts) == 2:
                    name_version = parts[0].strip()
                    description = parts[1].strip()

                    # 提取包名和版本
                    if '=' in name_version:
                        name = name_version.split('=')[0].strip()
                        version = name_version.split('=')[1].strip().strip('"')

                        result = SearchResult(
                            name=name,
                            version=version,
                            description=description,
                            author="",
                            downloads="",
                            homepage="",
                            repository="",
                            license="",
                            package_manager="cargo"
                        )
                        results.append(result)

        return results
