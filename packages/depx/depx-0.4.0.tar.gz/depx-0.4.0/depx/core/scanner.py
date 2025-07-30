"""
项目扫描器模块

负责扫描文件系统，发现和识别各种类型的编程项目
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Generator, List, Optional, Type

from ..parsers.base import BaseParser, ProjectInfo, ProjectType
from ..parsers.nodejs import NodeJSParser
from ..parsers.python import PythonParser
from ..utils.file_utils import is_hidden_directory

logger = logging.getLogger(__name__)


class ProjectScanner:
    """项目扫描器"""

    def __init__(self):
        """初始化扫描器，注册所有支持的解析器"""
        self._parsers: Dict[ProjectType, BaseParser] = {}
        self._register_parsers()

    def _register_parsers(self) -> None:
        """注册所有支持的解析器"""
        parsers = [
            NodeJSParser(),
            PythonParser(),
            # 后续添加其他语言的解析器
            # JavaParser(),
            # GoParser(),
            # RustParser(),
        ]

        for parser in parsers:
            self._parsers[parser.project_type] = parser
            logger.debug(f"注册解析器: {parser.project_type.value}")

    def scan_directory(
        self, root_path: Path, max_depth: int = 5, parallel: bool = True
    ) -> List[ProjectInfo]:
        """
        扫描指定目录，发现所有项目

        Args:
            root_path: 根目录路径
            max_depth: 最大扫描深度
            parallel: 是否使用并行处理

        Returns:
            发现的项目信息列表
        """
        if not root_path.exists() or not root_path.is_dir():
            logger.error(f"无效的扫描路径: {root_path}")
            return []

        logger.info(f"开始扫描目录: {root_path}")

        # 发现潜在的项目目录
        project_candidates = list(self._find_project_candidates(root_path, max_depth))
        logger.info(f"发现 {len(project_candidates)} 个潜在项目目录")

        if not project_candidates:
            return []

        # 解析项目信息
        if parallel and len(project_candidates) > 1:
            projects = self._parse_projects_parallel(project_candidates)
        else:
            projects = self._parse_projects_sequential(project_candidates)

        logger.info(f"成功解析 {len(projects)} 个项目")
        return projects

    def _find_project_candidates(
        self, root_path: Path, max_depth: int
    ) -> Generator[Path, None, None]:
        """
        查找潜在的项目目录

        Args:
            root_path: 根目录
            max_depth: 最大深度

        Yields:
            潜在的项目目录路径
        """

        def _scan_recursive(
            current_path: Path, current_depth: int
        ) -> Generator[Path, None, None]:
            if current_depth > max_depth:
                return

            try:
                # 检查当前目录是否为项目
                if self._is_project_directory(current_path):
                    yield current_path
                    # 如果是项目目录，通常不需要继续深入扫描
                    return

                # 扫描子目录
                for item in current_path.iterdir():
                    if item.is_dir() and not is_hidden_directory(item):
                        yield from _scan_recursive(item, current_depth + 1)

            except (OSError, PermissionError) as e:
                logger.warning(f"无法访问目录: {current_path}, 错误: {e}")

        yield from _scan_recursive(root_path, 0)

    def _is_project_directory(self, path: Path) -> bool:
        """
        判断目录是否为项目目录

        Args:
            path: 目录路径

        Returns:
            是否为项目目录
        """
        for parser in self._parsers.values():
            if parser.can_parse(path):
                return True
        return False

    def _parse_projects_sequential(
        self, project_paths: List[Path]
    ) -> List[ProjectInfo]:
        """
        顺序解析项目

        Args:
            project_paths: 项目路径列表

        Returns:
            解析成功的项目信息列表
        """
        projects = []

        for path in project_paths:
            try:
                project_info = self._parse_single_project(path)
                if project_info:
                    projects.append(project_info)
            except Exception as e:
                logger.error(f"解析项目失败: {path}, 错误: {e}")

        return projects

    def _parse_projects_parallel(self, project_paths: List[Path]) -> List[ProjectInfo]:
        """
        并行解析项目

        Args:
            project_paths: 项目路径列表

        Returns:
            解析成功的项目信息列表
        """
        projects = []

        with ThreadPoolExecutor(max_workers=4) as executor:
            # 提交所有解析任务
            future_to_path = {
                executor.submit(self._parse_single_project, path): path
                for path in project_paths
            }

            # 收集结果
            for future in as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    project_info = future.result()
                    if project_info:
                        projects.append(project_info)
                except Exception as e:
                    logger.error(f"解析项目失败: {path}, 错误: {e}")

        return projects

    def _parse_single_project(self, project_path: Path) -> Optional[ProjectInfo]:
        """
        解析单个项目

        Args:
            project_path: 项目路径

        Returns:
            项目信息，解析失败时返回 None
        """
        for parser in self._parsers.values():
            if parser.can_parse(project_path):
                logger.debug(
                    f"使用 {parser.project_type.value} 解析器解析: {project_path}"
                )
                return parser.parse_project(project_path)

        logger.warning(f"没有找到合适的解析器: {project_path}")
        return None

    def get_supported_project_types(self) -> List[ProjectType]:
        """
        获取支持的项目类型列表

        Returns:
            支持的项目类型列表
        """
        return list(self._parsers.keys())

    def scan_single_project(self, project_path: Path) -> Optional[ProjectInfo]:
        """
        扫描单个项目

        Args:
            project_path: 项目路径

        Returns:
            项目信息，解析失败时返回 None
        """
        if not project_path.exists() or not project_path.is_dir():
            logger.error(f"无效的项目路径: {project_path}")
            return None

        return self._parse_single_project(project_path)
