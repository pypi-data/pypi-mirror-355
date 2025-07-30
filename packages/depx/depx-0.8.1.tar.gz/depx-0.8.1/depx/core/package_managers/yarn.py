"""
Yarn 包管理器实现
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


class YarnManager(BasePackageManager):
    """Yarn 包管理器"""

    @property
    def name(self) -> str:
        return "yarn"

    @property
    def command(self) -> str:
        return "yarn"

    def is_available(self) -> bool:
        """检查 yarn 是否可用"""
        return self._is_command_available("yarn")

    def install(
        self, package_name: str, dev: bool = False, global_install: bool = False
    ) -> PackageManagerResult:
        """
        使用 yarn 安装包
        
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
                message="yarn 命令不可用",
                command="",
                error="yarn command not found"
            )

        # 构建命令
        if global_install:
            cmd = ["yarn", "global", "add", package_name]
        else:
            cmd = ["yarn", "add", package_name]
            if dev:
                cmd.append("--dev")

        return self.run_command(cmd)

    def uninstall(
        self, package_name: str, global_uninstall: bool = False
    ) -> PackageManagerResult:
        """
        使用 yarn 卸载包
        
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
                message="yarn 命令不可用",
                command="",
                error="yarn command not found"
            )

        # 构建命令
        if global_uninstall:
            cmd = ["yarn", "global", "remove", package_name]
        else:
            cmd = ["yarn", "remove", package_name]

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
            cmd = ["yarn", "global", "add", package_name]
        else:
            cmd = ["yarn", "add", package_name]
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
            cmd = ["yarn", "global", "remove", package_name]
        else:
            cmd = ["yarn", "remove", package_name]

        return " ".join(cmd)

    def search(self, package_name: str, limit: int = 10) -> List[SearchResult]:
        """
        使用 yarn 搜索包（基于 npm registry）

        Args:
            package_name: 包名或关键词
            limit: 限制结果数量

        Returns:
            搜索结果列表
        """
        if not self.is_available():
            return []

        try:
            # Yarn 可以使用 npm search，因为它们使用相同的 registry
            cmd = ["npm", "search", package_name, "--json"]
            result = self.run_command(cmd, timeout=30)

            if not result.success:
                logger.warning(f"yarn/npm search 失败: {result.error}")
                return []

            # 解析 JSON 结果
            import json
            search_data = json.loads(result.output)
            results = []

            for item in search_data[:limit]:
                search_result = SearchResult(
                    name=item.get("name", ""),
                    version=item.get("version", ""),
                    description=item.get("description", ""),
                    author=self._get_author_name(item.get("author", {})),
                    downloads=str(item.get("downloads", {}).get("weekly", "")),
                    homepage=item.get("links", {}).get("homepage", ""),
                    repository=item.get("links", {}).get("repository", ""),
                    license=item.get("license", ""),
                    package_manager="yarn"
                )
                results.append(search_result)

            return results

        except Exception as e:
            logger.error(f"yarn search 异常: {e}")
            return []

    def check_outdated(self) -> List[OutdatedPackage]:
        """
        检查过时的包

        Returns:
            过时包列表
        """
        if not self.is_available():
            return []

        try:
            # 使用 yarn outdated 命令
            cmd = ["yarn", "outdated", "--json"]
            result = self.run_command(cmd, timeout=30)

            # 解析结果（yarn outdated 的输出格式可能不同）
            # 这里提供基本框架
            return []

        except Exception as e:
            logger.error(f"yarn outdated 异常: {e}")
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
                message="yarn 命令不可用",
                updated_packages=[],
                error="yarn command not found"
            )

        # 构建更新命令
        if package_name:
            cmd = ["yarn", "upgrade", package_name]
        else:
            cmd = ["yarn", "upgrade"]

        result = self.run_command(cmd, timeout=120)

        return UpdateResult(
            success=result.success,
            message="更新完成" if result.success else f"更新失败: {result.message}",
            updated_packages=[],  # 需要解析输出来获取实际更新的包
            command=result.command,
            output=result.output,
            error=result.error
        )

    def _get_author_name(self, author_data) -> str:
        """从作者数据中提取作者名"""
        if isinstance(author_data, dict):
            return author_data.get("name", "")
        elif isinstance(author_data, str):
            return author_data
        return ""
