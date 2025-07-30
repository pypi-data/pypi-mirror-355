"""
文件操作工具模块

提供文件系统相关的通用工具函数
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Generator, Optional

logger = logging.getLogger(__name__)


def get_directory_size(directory: Path) -> int:
    """
    计算目录的总大小（字节）

    Args:
        directory: 目录路径

    Returns:
        目录总大小（字节）
    """
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
                except (OSError, IOError) as e:
                    logger.warning(f"无法获取文件大小: {filepath}, 错误: {e}")
                    continue
    except (OSError, IOError) as e:
        logger.error(f"无法访问目录: {directory}, 错误: {e}")
        return 0

    return total_size


def find_files_by_pattern(root_dir: Path, pattern: str) -> Generator[Path, None, None]:
    """
    在指定目录下查找匹配模式的文件

    Args:
        root_dir: 根目录
        pattern: 文件名模式（如 "package.json"）

    Yields:
        匹配的文件路径
    """
    try:
        for file_path in root_dir.rglob(pattern):
            if file_path.is_file():
                yield file_path
    except (OSError, IOError) as e:
        logger.error(f"搜索文件时出错: {root_dir}, 模式: {pattern}, 错误: {e}")


def is_hidden_directory(path: Path) -> bool:
    """
    判断是否为隐藏目录或应该跳过的目录

    Args:
        path: 目录路径

    Returns:
        是否应该跳过该目录
    """
    skip_dirs = {
        ".git",
        ".svn",
        ".hg",  # 版本控制
        ".vscode",
        ".idea",  # IDE
        "__pycache__",
        ".pytest_cache",  # Python
        "node_modules/.cache",  # Node.js 缓存
        ".DS_Store",  # macOS
        "Thumbs.db",  # Windows
    }

    return (
        path.name.startswith(".")
        or path.name in skip_dirs
        or any(skip_dir in str(path) for skip_dir in skip_dirs)
    )


def safe_read_json(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    安全地读取 JSON 文件

    Args:
        file_path: JSON 文件路径

    Returns:
        解析后的 JSON 数据，失败时返回 None
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, IOError, json.JSONDecodeError) as e:
        logger.warning(f"无法读取 JSON 文件: {file_path}, 错误: {e}")
        return None


def format_size(size_bytes: int) -> str:
    """
    格式化文件大小为人类可读的格式

    Args:
        size_bytes: 字节数

    Returns:
        格式化后的大小字符串
    """
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)

    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1

    return f"{size:.1f} {size_names[i]}"
