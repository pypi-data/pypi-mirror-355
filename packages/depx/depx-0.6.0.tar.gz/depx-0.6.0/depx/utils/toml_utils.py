"""
TOML 解析工具模块

提供跨版本兼容的 TOML 文件解析功能
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def safe_load_toml(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    安全加载 TOML 文件，支持多种解析库

    优先级：
    1. tomllib (Python 3.11+ 内置)
    2. tomli (第三方库)
    3. toml (备用库)

    Args:
        file_path: TOML 文件路径

    Returns:
        解析后的 TOML 数据，失败时返回 None
    """
    if not file_path.exists():
        logger.warning(f"TOML 文件不存在: {file_path}")
        return None

    # 尝试使用 Python 3.11+ 内置的 tomllib
    try:
        import tomllib

        with open(file_path, "rb") as f:
            return tomllib.load(f)
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"使用 tomllib 解析失败: {file_path}, 错误: {e}")

    # 尝试使用 tomli (推荐的第三方库)
    try:
        import tomli

        with open(file_path, "rb") as f:
            return tomli.load(f)
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"使用 tomli 解析失败: {file_path}, 错误: {e}")

    # 尝试使用 toml (备用库)
    try:
        import toml

        with open(file_path, "r", encoding="utf-8") as f:
            return toml.load(f)
    except ImportError:
        logger.error("无法找到 TOML 解析库。请安装: pip install tomli")
        return None
    except Exception as e:
        logger.warning(f"使用 toml 解析失败: {file_path}, 错误: {e}")

    return None


def get_available_toml_library() -> Optional[str]:
    """
    检查可用的 TOML 解析库

    Returns:
        可用的库名称，如果都不可用则返回 None
    """
    try:
        pass

        return "tomllib"
    except ImportError:
        pass

    try:
        pass

        return "tomli"
    except ImportError:
        pass

    try:
        pass

        return "toml"
    except ImportError:
        pass

    return None


def ensure_toml_support() -> bool:
    """
    确保 TOML 支持可用

    Returns:
        是否有可用的 TOML 解析库
    """
    library = get_available_toml_library()
    if library:
        logger.debug(f"使用 TOML 解析库: {library}")
        return True
    else:
        logger.warning(
            "未找到 TOML 解析库。Rust、Go 等项目的解析功能将受限。"
            "建议安装: pip install tomli"
        )
        return False
