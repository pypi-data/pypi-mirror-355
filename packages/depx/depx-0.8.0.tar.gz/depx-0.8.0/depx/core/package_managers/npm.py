"""
NPM 包管理器实现
"""

import json
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

    def search(self, package_name: str, limit: int = 10) -> List[SearchResult]:
        """
        使用 npm 搜索包

        Args:
            package_name: 包名或关键词
            limit: 限制结果数量

        Returns:
            搜索结果列表
        """
        if not self.is_available():
            return []

        try:
            # 使用 npm search 命令
            cmd = ["npm", "search", package_name, "--json"]
            result = self.run_command(cmd, timeout=30)

            if not result.success:
                logger.warning(f"npm search 失败: {result.error}")
                return []

            # 解析 JSON 结果
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
                    package_manager="npm"
                )
                results.append(search_result)

            return results

        except json.JSONDecodeError as e:
            logger.error(f"解析 npm search 结果失败: {e}")
            return []
        except Exception as e:
            logger.error(f"npm search 异常: {e}")
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
            # 使用 npm outdated 命令
            cmd = ["npm", "outdated", "--json"]
            result = self.run_command(cmd, timeout=30)

            # npm outdated 在有过时包时返回非零退出码，这是正常的
            if result.output:
                outdated_data = json.loads(result.output)
                outdated_packages = []

                for name, info in outdated_data.items():
                    package = OutdatedPackage(
                        name=name,
                        current_version=info.get("current", ""),
                        latest_version=info.get("latest", ""),
                        package_type="development" if info.get("type") == "devDependencies" else "production"
                    )
                    outdated_packages.append(package)

                return outdated_packages

            return []

        except json.JSONDecodeError as e:
            logger.error(f"解析 npm outdated 结果失败: {e}")
            return []
        except Exception as e:
            logger.error(f"npm outdated 异常: {e}")
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
                message="npm 命令不可用",
                updated_packages=[],
                error="npm command not found"
            )

        # 先检查过时的包
        outdated_packages = self.check_outdated()

        if package_name:
            # 更新特定包
            outdated_packages = [p for p in outdated_packages if p.name == package_name]
            if not outdated_packages:
                return UpdateResult(
                    success=True,
                    message=f"包 {package_name} 已是最新版本",
                    updated_packages=[]
                )

        if not outdated_packages:
            return UpdateResult(
                success=True,
                message="所有包都是最新版本",
                updated_packages=[]
            )

        # 构建更新命令
        if package_name:
            cmd = ["npm", "update", package_name]
        else:
            cmd = ["npm", "update"]

        result = self.run_command(cmd, timeout=120)

        return UpdateResult(
            success=result.success,
            message="更新完成" if result.success else f"更新失败: {result.message}",
            updated_packages=outdated_packages if result.success else [],
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
