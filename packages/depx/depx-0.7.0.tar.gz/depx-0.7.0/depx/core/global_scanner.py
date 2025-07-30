"""
全局依赖扫描器模块

负责扫描系统中各种包管理器的全局安装依赖
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import List, Set

from ..parsers.base import GlobalDependencyInfo, PackageManagerType
from ..utils.file_utils import get_directory_size

logger = logging.getLogger(__name__)


class GlobalScanner:
    """全局依赖扫描器"""

    def __init__(self):
        """初始化全局扫描器"""
        self.home_dir = Path.home()
        self.detected_managers: Set[PackageManagerType] = set()

    def scan_all_global_dependencies(self) -> List[GlobalDependencyInfo]:
        """
        扫描所有包管理器的全局依赖

        Returns:
            全局依赖信息列表
        """
        logger.info("开始扫描全局依赖")

        all_dependencies = []

        # 检测并扫描各种包管理器
        scanners = [
            self._scan_npm_global,
            self._scan_yarn_global,
            self._scan_pip_global,
            # 后续可以添加更多包管理器
            # self._scan_cargo_global,
            # self._scan_go_global,
        ]

        for scanner in scanners:
            try:
                deps = scanner()
                all_dependencies.extend(deps)
                scanner_name = getattr(scanner, "__name__", str(scanner))
                logger.info(f"扫描器 {scanner_name} 发现 {len(deps)} 个全局依赖")
            except Exception as e:
                scanner_name = getattr(scanner, "__name__", str(scanner))
                logger.warning(f"扫描器 {scanner_name} 执行失败: {e}")

        logger.info(f"总共发现 {len(all_dependencies)} 个全局依赖")
        return all_dependencies

    def scan_by_package_manager(
        self, manager_type: PackageManagerType
    ) -> List[GlobalDependencyInfo]:
        """
        扫描指定包管理器的全局依赖

        Args:
            manager_type: 包管理器类型

        Returns:
            全局依赖信息列表
        """
        scanner_map = {
            PackageManagerType.NPM: self._scan_npm_global,
            PackageManagerType.YARN: self._scan_yarn_global,
            PackageManagerType.PIP: self._scan_pip_global,
        }

        scanner = scanner_map.get(manager_type)
        if not scanner:
            logger.warning(f"不支持的包管理器类型: {manager_type}")
            return []

        try:
            return scanner()
        except Exception as e:
            logger.error(f"扫描 {manager_type.value} 全局依赖失败: {e}")
            return []

    def get_detected_package_managers(self) -> List[PackageManagerType]:
        """
        获取检测到的包管理器列表

        Returns:
            包管理器类型列表
        """
        return list(self.detected_managers)

    def _scan_npm_global(self) -> List[GlobalDependencyInfo]:
        """扫描 npm 全局依赖"""
        dependencies = []

        # 检查 npm 是否可用
        if not self._is_command_available("npm"):
            return dependencies

        self.detected_managers.add(PackageManagerType.NPM)

        try:
            # 使用 npm list -g --json 获取全局依赖
            result = subprocess.run(
                ["npm", "list", "-g", "--json", "--depth=0"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                logger.warning(f"npm list 命令执行失败: {result.stderr}")
                return dependencies

            data = json.loads(result.stdout)
            npm_deps = data.get("dependencies", {})

            # 获取全局安装路径
            global_path_result = subprocess.run(
                ["npm", "root", "-g"], capture_output=True, text=True, timeout=10
            )

            global_root = (
                Path(global_path_result.stdout.strip())
                if global_path_result.returncode == 0
                else None
            )

            for name, info in npm_deps.items():
                version = info.get("version", "unknown")

                # 计算依赖路径和大小
                dep_path = global_root / name if global_root else None
                size = 0
                if dep_path and dep_path.exists():
                    size = get_directory_size(dep_path)

                dep_info = GlobalDependencyInfo(
                    name=name,
                    version=version,
                    package_manager=PackageManagerType.NPM,
                    install_path=dep_path or Path("unknown"),
                    size_bytes=size,
                    description=info.get("description"),
                )
                dependencies.append(dep_info)

        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
            logger.error(f"扫描 npm 全局依赖时出错: {e}")

        return dependencies

    def _scan_yarn_global(self) -> List[GlobalDependencyInfo]:
        """扫描 yarn 全局依赖"""
        dependencies = []

        if not self._is_command_available("yarn"):
            return dependencies

        self.detected_managers.add(PackageManagerType.YARN)

        try:
            # 使用 yarn global list 获取全局依赖
            result = subprocess.run(
                ["yarn", "global", "list", "--json"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                logger.warning(f"yarn global list 命令执行失败: {result.stderr}")
                return dependencies

            # yarn 输出每行一个 JSON 对象
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if data.get("type") == "info" and "data" in data:
                        # 解析依赖信息
                        info_text = data["data"]
                        # 简单解析，实际可能需要更复杂的逻辑
                        if "@" in info_text:
                            parts = info_text.split("@")
                            if len(parts) >= 2:
                                name = "@".join(parts[:-1])
                                version = parts[-1]

                                dep_info = GlobalDependencyInfo(
                                    name=name,
                                    version=version,
                                    package_manager=PackageManagerType.YARN,
                                    install_path=Path(
                                        "unknown"
                                    ),  # yarn 全局路径较难获取
                                    size_bytes=0,
                                )
                                dependencies.append(dep_info)
                except json.JSONDecodeError:
                    continue

        except (subprocess.TimeoutExpired, Exception) as e:
            logger.error(f"扫描 yarn 全局依赖时出错: {e}")

        return dependencies

    def _scan_pip_global(self) -> List[GlobalDependencyInfo]:
        """扫描 pip 全局依赖"""
        dependencies = []

        # 尝试不同的 pip 命令
        pip_commands = ["pip", "pip3", "python3 -m pip"]

        for pip_cmd in pip_commands:
            if self._is_command_available(pip_cmd.split()[0]):
                self.detected_managers.add(PackageManagerType.PIP)
                break
        else:
            return dependencies

        try:
            # 使用 pip list --format=json 获取已安装的包
            cmd = pip_cmd.split() + ["list", "--format=json"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                logger.warning(f"pip list 命令执行失败: {result.stderr}")
                return dependencies

            packages = json.loads(result.stdout)

            for package in packages:
                name = package.get("name", "unknown")
                version = package.get("version", "unknown")

                dep_info = GlobalDependencyInfo(
                    name=name,
                    version=version,
                    package_manager=PackageManagerType.PIP,
                    install_path=Path("unknown"),  # pip 包路径需要额外查询
                    size_bytes=0,
                )
                dependencies.append(dep_info)

        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
            logger.error(f"扫描 pip 全局依赖时出错: {e}")

        return dependencies

    def _is_command_available(self, command: str) -> bool:
        """检查命令是否可用"""
        try:
            subprocess.run([command, "--version"], capture_output=True, timeout=5)
            return True
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return False
