"""
显示和用户界面工具模块

提供美化的输出、进度显示和用户交互功能
"""

import logging
import sys
from typing import Any, Dict, List, Optional

from ..parsers.base import ProjectInfo, ProjectType

logger = logging.getLogger(__name__)

# 尝试导入 rich 库，如果不可用则使用简单输出
try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.table import Table
    from rich.tree import Tree
    from rich.panel import Panel
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    logger.debug("Rich 库不可用，使用简单输出格式")


class DisplayManager:
    """显示管理器"""
    
    def __init__(self, use_rich: bool = True):
        """
        初始化显示管理器
        
        Args:
            use_rich: 是否使用 Rich 库美化输出
        """
        self.use_rich = use_rich and RICH_AVAILABLE
        if self.use_rich:
            self.console = Console()
    
    def print(self, *args, **kwargs):
        """打印输出"""
        if self.use_rich:
            self.console.print(*args, **kwargs)
        else:
            print(*args, **kwargs)
    
    def print_header(self, title: str, subtitle: Optional[str] = None):
        """打印标题"""
        if self.use_rich:
            if subtitle:
                panel_content = f"[bold]{title}[/bold]\n{subtitle}"
            else:
                panel_content = f"[bold]{title}[/bold]"
            
            panel = Panel(panel_content, style="blue")
            self.console.print(panel)
        else:
            print(f"\n{'=' * 60}")
            print(f" {title}")
            if subtitle:
                print(f" {subtitle}")
            print(f"{'=' * 60}")
    
    def print_projects_table(self, projects: List[ProjectInfo]):
        """打印项目表格"""
        if not projects:
            self.print("[yellow]未找到任何项目[/yellow]" if self.use_rich else "未找到任何项目")
            return
        
        if self.use_rich:
            table = Table(title="项目扫描结果")
            table.add_column("项目名称", style="cyan", no_wrap=True)
            table.add_column("类型", style="magenta")
            table.add_column("依赖数量", justify="right", style="green")
            table.add_column("大小", justify="right", style="yellow")
            table.add_column("路径", style="dim")
            
            for project in projects:
                table.add_row(
                    project.name,
                    project.project_type.value,
                    str(len(project.dependencies)),
                    self._format_size(project.total_size_bytes),
                    str(project.path)
                )
            
            self.console.print(table)
        else:
            # 简单表格输出
            print(f"\n{'项目名称':<20} {'类型':<10} {'依赖数':<8} {'大小':<12} {'路径'}")
            print("-" * 80)
            for project in projects:
                print(f"{project.name:<20} {project.project_type.value:<10} "
                      f"{len(project.dependencies):<8} {self._format_size(project.total_size_bytes):<12} "
                      f"{project.path}")
    
    def print_project_summary(self, projects: List[ProjectInfo]):
        """打印项目摘要"""
        if not projects:
            return
        
        # 统计信息
        total_projects = len(projects)
        total_dependencies = sum(len(p.dependencies) for p in projects)
        total_size = sum(p.total_size_bytes for p in projects)
        
        # 按类型分组
        type_stats = {}
        for project in projects:
            project_type = project.project_type.value
            if project_type not in type_stats:
                type_stats[project_type] = {"count": 0, "dependencies": 0, "size": 0}
            
            type_stats[project_type]["count"] += 1
            type_stats[project_type]["dependencies"] += len(project.dependencies)
            type_stats[project_type]["size"] += project.total_size_bytes
        
        if self.use_rich:
            # 创建摘要面板
            summary_text = f"""
[bold]总计[/bold]: {total_projects} 个项目
[bold]依赖总数[/bold]: {total_dependencies}
[bold]总大小[/bold]: {self._format_size(total_size)}

[bold]按类型分布[/bold]:
"""
            for ptype, stats in type_stats.items():
                summary_text += f"  • {ptype}: {stats['count']} 项目, {stats['dependencies']} 依赖, {self._format_size(stats['size'])}\n"
            
            panel = Panel(summary_text.strip(), title="扫描摘要", style="green")
            self.console.print(panel)
        else:
            print(f"\n扫描摘要:")
            print(f"  总计: {total_projects} 个项目")
            print(f"  依赖总数: {total_dependencies}")
            print(f"  总大小: {self._format_size(total_size)}")
            print(f"\n按类型分布:")
            for ptype, stats in type_stats.items():
                print(f"  • {ptype}: {stats['count']} 项目, {stats['dependencies']} 依赖, {self._format_size(stats['size'])}")
    
    def print_dependencies_tree(self, project: ProjectInfo):
        """打印依赖树"""
        if self.use_rich:
            tree = Tree(f"[bold]{project.name}[/bold] ({project.project_type.value})")
            
            # 按类型分组依赖
            dep_groups = {}
            for dep in project.dependencies:
                dep_type = dep.dependency_type.value
                if dep_type not in dep_groups:
                    dep_groups[dep_type] = []
                dep_groups[dep_type].append(dep)
            
            for dep_type, deps in dep_groups.items():
                type_branch = tree.add(f"[magenta]{dep_type}[/magenta] ({len(deps)})")
                for dep in deps:
                    dep_text = f"{dep.name}"
                    if dep.version:
                        dep_text += f" [dim]({dep.version})[/dim]"
                    if dep.size_bytes > 0:
                        dep_text += f" [yellow]{self._format_size(dep.size_bytes)}[/yellow]"
                    type_branch.add(dep_text)
            
            self.console.print(tree)
        else:
            print(f"\n{project.name} ({project.project_type.value}):")
            for dep in project.dependencies:
                size_info = f" ({self._format_size(dep.size_bytes)})" if dep.size_bytes > 0 else ""
                print(f"  • {dep.name} {dep.version}{size_info} [{dep.dependency_type.value}]")
    
    def create_progress_bar(self, description: str = "处理中..."):
        """创建进度条"""
        if self.use_rich:
            return Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=self.console
            )
        else:
            return SimpleProgressBar(description)
    
    def print_error(self, message: str, exception: Optional[Exception] = None):
        """打印错误信息"""
        if self.use_rich:
            error_text = f"[bold red]错误[/bold red]: {message}"
            if exception:
                error_text += f"\n[dim]{str(exception)}[/dim]"
            self.console.print(error_text)
        else:
            print(f"错误: {message}")
            if exception:
                print(f"  详情: {exception}")
    
    def print_warning(self, message: str):
        """打印警告信息"""
        if self.use_rich:
            self.console.print(f"[bold yellow]警告[/bold yellow]: {message}")
        else:
            print(f"警告: {message}")
    
    def print_success(self, message: str):
        """打印成功信息"""
        if self.use_rich:
            self.console.print(f"[bold green]✓[/bold green] {message}")
        else:
            print(f"✓ {message}")
    
    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        
        return f"{size:.1f} {size_names[i]}"


class SimpleProgressBar:
    """简单进度条（当 Rich 不可用时使用）"""
    
    def __init__(self, description: str):
        self.description = description
        self.task_id = 0
    
    def add_task(self, description: str, total: int = 100):
        """添加任务"""
        print(f"{description}...")
        return self.task_id
    
    def update(self, task_id: int, advance: int = 1, description: Optional[str] = None):
        """更新进度"""
        # 简单的点进度显示
        print(".", end="", flush=True)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        print()  # 换行


# 全局显示管理器实例
display = DisplayManager()


def set_display_mode(use_rich: bool = True):
    """设置显示模式"""
    global display
    display = DisplayManager(use_rich=use_rich)


def print_project_info(project: ProjectInfo):
    """打印项目详细信息"""
    display.print_header(f"项目信息: {project.name}")
    
    info_data = [
        ("项目名称", project.name),
        ("项目类型", project.project_type.value),
        ("项目路径", str(project.path)),
        ("配置文件", str(project.config_file)),
        ("依赖数量", len(project.dependencies)),
        ("总大小", display._format_size(project.total_size_bytes)),
    ]
    
    # 添加元数据
    if project.metadata:
        for key, value in project.metadata.items():
            info_data.append((key.replace("_", " ").title(), str(value)))
    
    if display.use_rich:
        table = Table(show_header=False, box=None)
        table.add_column("属性", style="cyan", width=15)
        table.add_column("值", style="white")
        
        for key, value in info_data:
            table.add_row(key, value)
        
        display.console.print(table)
    else:
        for key, value in info_data:
            print(f"  {key}: {value}")
    
    # 打印依赖树
    if project.dependencies:
        display.print_dependencies_tree(project)
