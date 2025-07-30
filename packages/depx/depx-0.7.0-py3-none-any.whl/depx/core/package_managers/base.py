"""
包管理器基类

定义所有包管理器的统一接口
"""

import logging
import subprocess
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class PackageManagerResult:
    """包管理器操作结果"""
    success: bool
    message: str
    command: str
    output: str = ""
    error: str = ""


class BasePackageManager(ABC):
    """包管理器基类"""

    def __init__(self, project_path: Optional[Path] = None):
        """
        初始化包管理器
        
        Args:
            project_path: 项目路径，None 表示全局操作
        """
        self.project_path = project_path
        self.is_global = project_path is None

    @property
    @abstractmethod
    def name(self) -> str:
        """包管理器名称"""
        pass

    @property
    @abstractmethod
    def command(self) -> str:
        """包管理器命令"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查包管理器是否可用"""
        pass

    @abstractmethod
    def install(
        self, package_name: str, dev: bool = False, global_install: bool = False
    ) -> PackageManagerResult:
        """
        安装包
        
        Args:
            package_name: 包名
            dev: 是否为开发依赖
            global_install: 是否全局安装
            
        Returns:
            操作结果
        """
        pass

    @abstractmethod
    def uninstall(
        self, package_name: str, global_uninstall: bool = False
    ) -> PackageManagerResult:
        """
        卸载包
        
        Args:
            package_name: 包名
            global_uninstall: 是否全局卸载
            
        Returns:
            操作结果
        """
        pass

    def run_command(
        self, cmd: List[str], timeout: int = 300
    ) -> PackageManagerResult:
        """
        执行命令
        
        Args:
            cmd: 命令列表
            timeout: 超时时间（秒）
            
        Returns:
            操作结果
        """
        command_str = " ".join(cmd)
        logger.info(f"执行命令: {command_str}")

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            success = result.returncode == 0
            message = (
                "命令执行成功" if success else f"命令执行失败 (退出码: {result.returncode})"
            )

            return PackageManagerResult(
                success=success,
                message=message,
                command=command_str,
                output=result.stdout,
                error=result.stderr
            )

        except subprocess.TimeoutExpired:
            return PackageManagerResult(
                success=False,
                message=f"命令执行超时 ({timeout}秒)",
                command=command_str,
                error="Timeout"
            )
        except Exception as e:
            return PackageManagerResult(
                success=False,
                message=f"命令执行异常: {e}",
                command=command_str,
                error=str(e)
            )

    def validate_package_name(self, package_name: str) -> bool:
        """
        验证包名格式
        
        Args:
            package_name: 包名
            
        Returns:
            是否有效
        """
        if not package_name or not package_name.strip():
            return False
        
        # 基本验证：不能包含空格和特殊字符
        invalid_chars = [" ", "\t", "\n", "\r"]
        return not any(char in package_name for char in invalid_chars)

    def _is_command_available(self, command: str) -> bool:
        """检查命令是否可用"""
        return shutil.which(command) is not None
