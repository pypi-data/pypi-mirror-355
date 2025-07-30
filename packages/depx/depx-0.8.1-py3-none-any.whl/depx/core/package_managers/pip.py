"""
Pip 包管理器实现
"""

import json
import logging
import re
import urllib.request
import urllib.parse
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

    def search(self, package_name: str, limit: int = 10) -> List[SearchResult]:
        """
        使用 PyPI API 搜索包

        Args:
            package_name: 包名或关键词
            limit: 限制结果数量

        Returns:
            搜索结果列表
        """
        try:
            # 使用 PyPI API 搜索
            search_url = f"https://pypi.org/pypi/{urllib.parse.quote(package_name)}/json"

            with urllib.request.urlopen(search_url, timeout=10) as response:
                data = json.loads(response.read().decode())

                info = data.get("info", {})
                result = SearchResult(
                    name=info.get("name", ""),
                    version=info.get("version", ""),
                    description=info.get("summary", ""),
                    author=info.get("author", ""),
                    downloads="",  # PyPI API 不直接提供下载量
                    homepage=info.get("home_page", ""),
                    repository=info.get("project_url", ""),
                    license=info.get("license", ""),
                    package_manager="pip"
                )
                return [result]

        except Exception as e:
            logger.debug(f"PyPI API 搜索失败，尝试简单搜索: {e}")

        # 如果精确搜索失败，尝试使用 pip search 的替代方案
        # 由于 pip search 已被废弃，我们使用简单的包名验证
        try:
            # 尝试获取包信息来验证包是否存在
            pip_cmd = self._get_pip_command()
            cmd = [pip_cmd, "show", package_name]
            result = self.run_command(cmd, timeout=10)

            if result.success:
                # 解析 pip show 的输出
                info = self._parse_pip_show_output(result.output)
                search_result = SearchResult(
                    name=info.get("Name", ""),
                    version=info.get("Version", ""),
                    description=info.get("Summary", ""),
                    author=info.get("Author", ""),
                    downloads="",
                    homepage=info.get("Home-page", ""),
                    repository="",
                    license=info.get("License", ""),
                    package_manager="pip"
                )
                return [search_result]

        except Exception as e:
            logger.error(f"pip 搜索异常: {e}")

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
            # 使用 pip list --outdated 命令
            pip_cmd = self._get_pip_command()
            cmd = [pip_cmd, "list", "--outdated", "--format=json"]
            result = self.run_command(cmd, timeout=30)

            if result.success and result.output:
                outdated_data = json.loads(result.output)
                outdated_packages = []

                for item in outdated_data:
                    package = OutdatedPackage(
                        name=item.get("name", ""),
                        current_version=item.get("version", ""),
                        latest_version=item.get("latest_version", ""),
                        package_type="production"  # pip 不区分开发依赖
                    )
                    outdated_packages.append(package)

                return outdated_packages

            return []

        except json.JSONDecodeError as e:
            logger.error(f"解析 pip list --outdated 结果失败: {e}")
            return []
        except Exception as e:
            logger.error(f"pip list --outdated 异常: {e}")
            return []

    def update_package(
        self, package_name: Optional[str] = None, dev: bool = False
    ) -> UpdateResult:
        """
        更新包

        Args:
            package_name: 包名，None 表示更新所有包
            dev: 是否包括开发依赖（pip 不区分）

        Returns:
            更新结果
        """
        if not self.is_available():
            return UpdateResult(
                success=False,
                message="pip 命令不可用",
                updated_packages=[],
                error="pip command not found"
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
        pip_cmd = self._get_pip_command()
        if package_name:
            cmd = [pip_cmd, "install", "--upgrade", package_name]
        else:
            # 更新所有过时的包
            package_names = [p.name for p in outdated_packages]
            cmd = [pip_cmd, "install", "--upgrade"] + package_names

        result = self.run_command(cmd, timeout=120)

        return UpdateResult(
            success=result.success,
            message="更新完成" if result.success else f"更新失败: {result.message}",
            updated_packages=outdated_packages if result.success else [],
            command=result.command,
            output=result.output,
            error=result.error
        )

    def _parse_pip_show_output(self, output: str) -> dict:
        """解析 pip show 命令的输出"""
        info = {}
        for line in output.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                info[key.strip()] = value.strip()
        return info
