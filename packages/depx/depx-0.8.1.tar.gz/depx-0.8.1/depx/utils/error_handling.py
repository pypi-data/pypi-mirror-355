"""
错误处理工具模块

提供统一的错误处理、重试机制和异常类定义
"""

import functools
import logging
import time
from typing import Any, Callable, Optional, Union

logger = logging.getLogger(__name__)


# 自定义异常类
class DepxError(Exception):
    """Depx 基础异常类"""


class DependencyParseError(DepxError):
    """依赖解析异常"""


class ProjectScanError(DepxError):
    """项目扫描异常"""


class ConfigurationError(DepxError):
    """配置错误异常"""


class NetworkError(DepxError):
    """网络相关异常"""


def with_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None,
):
    """
    重试装饰器

    Args:
        max_attempts: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff_factor: 退避因子
        exceptions: 需要重试的异常类型
        on_retry: 重试时的回调函数
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_attempts - 1:
                        logger.error(
                            f"函数 {func.__name__} 在 {max_attempts} 次尝试后仍然失败: {e}"
                        )
                        raise

                    wait_time = delay * (backoff_factor**attempt)
                    logger.warning(
                        f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败: {e}, "
                        f"{wait_time:.1f}秒后重试"
                    )

                    if on_retry:
                        on_retry(attempt, e)

                    time.sleep(wait_time)

            # 这行代码理论上不会执行到，但为了类型检查
            raise last_exception

        return wrapper

    return decorator


def safe_execute(
    func: Callable,
    default_value: Any = None,
    log_errors: bool = True,
    error_message: Optional[str] = None,
) -> Any:
    """
    安全执行函数，捕获异常并返回默认值

    Args:
        func: 要执行的函数
        default_value: 异常时返回的默认值
        log_errors: 是否记录错误日志
        error_message: 自定义错误消息

    Returns:
        函数执行结果或默认值
    """
    try:
        return func()
    except Exception as e:
        if log_errors:
            message = error_message or f"执行函数 {func.__name__} 时发生错误"
            logger.warning(f"{message}: {e}")
        return default_value


def validate_path(path: Union[str, Any], must_exist: bool = True) -> bool:
    """
    验证路径是否有效

    Args:
        path: 路径对象
        must_exist: 是否必须存在

    Returns:
        路径是否有效
    """
    try:
        from pathlib import Path

        if not isinstance(path, (str, Path)):
            return False

        path_obj = Path(path)

        if must_exist and not path_obj.exists():
            return False

        return True
    except Exception:
        return False


def handle_file_operation(operation: str):
    """
    文件操作错误处理装饰器

    Args:
        operation: 操作描述
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except FileNotFoundError as e:
                logger.error(f"{operation} - 文件未找到: {e}")
                raise DependencyParseError(f"文件未找到: {e}")
            except PermissionError as e:
                logger.error(f"{operation} - 权限不足: {e}")
                raise DependencyParseError(f"权限不足: {e}")
            except OSError as e:
                logger.error(f"{operation} - 系统错误: {e}")
                raise DependencyParseError(f"系统错误: {e}")
            except Exception as e:
                logger.error(f"{operation} - 未知错误: {e}")
                raise DependencyParseError(f"未知错误: {e}")

        return wrapper

    return decorator


class ErrorCollector:
    """错误收集器，用于收集和报告多个错误"""

    def __init__(self):
        self.errors = []
        self.warnings = []

    def add_error(self, error: str, exception: Optional[Exception] = None):
        """添加错误"""
        self.errors.append(
            {"message": error, "exception": exception, "timestamp": time.time()}
        )
        logger.error(error)

    def add_warning(self, warning: str):
        """添加警告"""
        self.warnings.append({"message": warning, "timestamp": time.time()})
        logger.warning(warning)

    def has_errors(self) -> bool:
        """是否有错误"""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """是否有警告"""
        return len(self.warnings) > 0

    def get_summary(self) -> dict:
        """获取错误摘要"""
        return {
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": self.errors,
            "warnings": self.warnings,
        }

    def clear(self):
        """清空错误和警告"""
        self.errors.clear()
        self.warnings.clear()


def create_user_friendly_error(error: Exception, context: str = "") -> str:
    """
    创建用户友好的错误消息

    Args:
        error: 原始异常
        context: 错误上下文

    Returns:
        用户友好的错误消息
    """
    error_type = type(error).__name__
    error_message = str(error)

    # 常见错误的友好提示
    friendly_messages = {
        "FileNotFoundError": "文件或目录不存在",
        "PermissionError": "权限不足，请检查文件访问权限",
        "JSONDecodeError": "JSON 文件格式错误",
        "TimeoutError": "操作超时，请检查网络连接",
        "ImportError": "缺少必要的依赖库",
        "ModuleNotFoundError": "缺少必要的 Python 模块",
    }

    friendly_msg = friendly_messages.get(error_type, error_message)

    if context:
        return f"{context}: {friendly_msg}"
    else:
        return friendly_msg
