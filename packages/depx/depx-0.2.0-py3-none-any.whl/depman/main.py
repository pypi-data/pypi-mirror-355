#!/usr/bin/env python3
"""
DepMan - A universal dependency manager CLI.
"""
import sys
from pathlib import Path

import click
import colorama
import platform

# 尝试导入 rich 库，如果不可用则进入兼容模式
try:
    from rich.console import Console
    from rich.table import Table
    from rich import box
    
    # Initialize rich console
    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    
    # 创建兼容函数，当 rich 不可用时使用
    class FallbackConsole:
        def print(self, text, err=False):
            # 简单移除 rich 标记
            text = text.replace("[bold]", "").replace("[/bold]", "")
            text = text.replace("[green]", "").replace("[/green]", "")
            text = text.replace("[red]", "").replace("[/red]", "")
            text = text.replace("[blue]", "").replace("[/blue]", "")
            text = text.replace("[yellow]", "").replace("[/yellow]", "")
            text = text.replace("[cyan]", "").replace("[/cyan]", "")
            text = text.replace("[bold red]", "").replace("[/bold red]", "")
            text = text.replace("[bold green]", "").replace("[/bold green]", "")
            text = text.replace("[bold blue]", "").replace("[/bold blue]", "")
            text = text.replace("[magenta]", "").replace("[/magenta]", "")
            
            if err:
                click.echo(text, err=True)
            else:
                click.echo(text)
    
    console = FallbackConsole()
    
    # 创建表格兼容类
    class FallbackTable:
        def __init__(self, title=None, box=None):
            self.title = title
            self.columns = []
            self.rows = []
            
        def add_column(self, header_name, style=None, justify=None, max_width=None, no_wrap=False):
            self.columns.append(header_name)
            
        def add_row(self, *args):
            self.rows.append(args)
    
    # 全局定义 Table 为 FallbackTable，确保兼容模式下可用
    Table = FallbackTable
    
    # 创建假 box 对象
    class FallbackBox:
        ROUNDED = None
    
    box = FallbackBox

def format_size(size_in_bytes):
    """
    将字节大小格式化为人类可读的格式。
    
    Args:
        size_in_bytes: 以字节为单位的大小
        
    Returns:
        str: 格式化后的大小字符串
    """
    if size_in_bytes is None:
        return "未知 (Unknown)"
        
    # 转换为数字
    try:
        size = float(size_in_bytes)
    except (ValueError, TypeError):
        return str(size_in_bytes)
    
    # 格式化大小
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            if size < 0.1:
                return f"{size:.1f} {unit}"
            return f"{size:.2f} {unit}"
        size /= 1024.0
    
    return f"{size:.2f} PB"

from depman.core.manager import DependencyManager
from depman.core.config import Config

# Initialize colorama for cross-platform colored terminal output
colorama.init()


@click.group()
@click.version_option()
@click.pass_context
def cli(ctx):
    """
    DepMan - Universal Dependency Manager.

    A tool to manage dependencies across different package managers and languages.
    """
    # Initialize the config
    ctx.obj = {'config': Config()}
    ctx.obj['manager'] = DependencyManager(ctx.obj['config'])


def handle_command_error(e, command_name=None):
    """
    通用错误处理函数，提供友好的错误消息。
    
    Args:
        e (Exception): 异常对象
        command_name (str, optional): 命令名称，用于更具体的错误消息。默认为 None。
    """
    error_msg = str(e)
    console.print(f"[bold red]错误 (Error):[/bold red] {error_msg}", err=True)
    
    # 检查是否为命令不存在错误
    if any(x in error_msg.lower() for x in ["command not found", "not recognized", "系统找不到指定的文件", "不是内部或外部命令", "找不到命令", "无法找到"]):
        console.print("\n[yellow]提示: 这可能是因为某些必要的命令行工具未安装或不在系统PATH中。请安装相应的工具后重试。[/yellow]")
        console.print("常见工具安装指南:")
        console.print("- npm: https://docs.npmjs.com/downloading-and-installing-node-js-and-npm")
        console.print("- pip/python: https://www.python.org/downloads/")
        
        # 如果是Windows系统，提供更具体的PATH建议
        if platform.system() == "Windows":
            console.print("\n[yellow]Windows用户提示: 请确保安装后重启命令提示符或PowerShell，或手动将工具路径添加到系统PATH中。[/yellow]")
        
        # 根据命令名称提供更具体的建议
        if command_name:
            if command_name == "install":
                console.print("\n[yellow]安装依赖需要相应的包管理器，如 npm、pip 等。[/yellow]")
            elif command_name == "uninstall":
                console.print("\n[yellow]卸载依赖需要相应的包管理器，如 npm、pip 等。[/yellow]")
            elif command_name == "upgrade":
                console.print("\n[yellow]升级依赖需要相应的包管理器，如 npm、pip 等。[/yellow]")
            elif command_name == "path":
                console.print("\n[yellow]查找包路径需要相应的包管理器已安装。[/yellow]")
            elif command_name == "list":
                console.print("\n[yellow]列出依赖需要相应的包管理器已安装。[/yellow]")
            elif command_name == "tree":
                console.print("\n[yellow]显示依赖树需要相应的包管理器已安装。[/yellow]")
            elif command_name == "search":
                console.print("\n[yellow]搜索包需要相应的包管理器已安装。[/yellow]")
    
    # 检查是否为找不到包管理器错误
    elif "no package manager" in error_msg.lower():
        console.print("\n[yellow]提示: 无法找到适合当前项目的包管理器。请确保您在正确的项目目录下，且项目有相应的配置文件。[/yellow]")
        console.print("常见项目配置文件:")
        console.print("- Python: requirements.txt, setup.py, pyproject.toml")
        console.print("- JavaScript: package.json")
        console.print("- Java: pom.xml, build.gradle")
        console.print("- Ruby: Gemfile")
        console.print("- Rust: Cargo.toml")
    
    # 检查是否为权限错误
    elif any(x in error_msg.lower() for x in ["permission denied", "access is denied", "需要权限"]):
        console.print("\n[yellow]提示: 操作失败，可能是因为权限不足。尝试使用管理员权限运行命令。[/yellow]")
        system = platform.system()
        if system == "Linux" or system == "Darwin":  # Linux 或 macOS
            console.print("在 Linux/macOS 上尝试使用 sudo:")
            console.print("  sudo depx <命令>")
        elif system == "Windows":  # Windows
            console.print("在 Windows 上尝试右键点击命令提示符或 PowerShell，选择'以管理员身份运行'，然后再执行命令。")
    
    # 网络错误
    elif any(x in error_msg.lower() for x in ["connection", "network", "timeout", "连接", "网络", "超时"]):
        console.print("\n[yellow]提示: 操作失败，可能是因为网络问题。请检查您的网络连接，然后重试。[/yellow]")
        
    sys.exit(1)


@cli.command()
@click.argument('package', required=False)
@click.option('--project', is_flag=True, help='Install to the current project instead of globally.')
@click.option('--file', type=click.Path(exists=True), help='Install from specific dependency file.')
@click.option('--manager', help='Specify the package manager to use (pip, npm, brew, etc.)')
@click.pass_context
def install(ctx, package, project, file, manager):
    """Install a package or all project dependencies."""
    manager_obj = ctx.obj['manager']
    
    try:
        # 检查所需工具是否可用
        tool_checker = manager_obj.tool_checker
        required_tools = ["npm", "pip", "python", "python3"]
        if manager:
            # 如果指定了包管理器，特别检查它
            required_tools.append(manager)
        
        missing_tools = tool_checker.get_missing_tools(required_tools)
        
        if missing_tools:
            missing_tools_msg = tool_checker.get_formatted_missing_tools_message(missing_tools)
            console.print(f"[yellow]警告: 某些包管理器工具不可用，可能会影响安装操作[/yellow]")
            console.print(f"[yellow]{missing_tools_msg}[/yellow]")
            
            # 如果指定的包管理器不可用，直接报错
            if manager and manager in missing_tools:
                console.print(f"[red]错误: 指定的包管理器 '{manager}' 不可用[/red]")
                sys.exit(1)
        
        if package:
            scope = "[cyan](项目)[/cyan]" if project else "[cyan](全局)[/cyan]"
            console.print(f"正在安装包: [green]{package}[/green] {scope}")
            
            # Use specified package manager if provided
            if manager:
                console.print(f"使用包管理器: [blue]{manager}[/blue]")
                manager_obj.install(package, project=project, pkg_manager=manager)
            else:
                manager_obj.install(package, project=project)
                
        elif file:
            console.print(f"从文件安装依赖: [blue]{file}[/blue]")
            manager_obj.install_from_file(file)
        elif project:
            console.print("安装所有项目依赖")
            manager_obj.install_all_project_dependencies()
        else:
            console.print("[red]错误: 请指定包名或使用 --project 安装所有项目依赖[/red]")
            sys.exit(1)
            
        console.print("[green]安装成功完成。[/green]")
    except Exception as e:
        handle_command_error(e, "install")


@cli.command()
@click.argument('package')
@click.option('--project', is_flag=True, help='Uninstall from the current project instead of globally.')
@click.pass_context
def uninstall(ctx, package, project):
    """Uninstall a package."""
    manager = ctx.obj['manager']
    
    try:
        # 检查所需工具是否可用
        tool_checker = manager.tool_checker
        required_tools = ["npm", "pip", "python", "python3"]
        missing_tools = tool_checker.get_missing_tools(required_tools)
        
        if missing_tools:
            missing_tools_msg = tool_checker.get_formatted_missing_tools_message(missing_tools)
            console.print(f"[yellow]警告: 某些包管理器工具不可用，可能会影响卸载操作[/yellow]")
            console.print(f"[yellow]{missing_tools_msg}[/yellow]")
        
        scope = "[cyan](项目)[/cyan]" if project else "[cyan](全局)[/cyan]"
        console.print(f"正在卸载包: [green]{package}[/green] {scope}")
        manager.uninstall(package, project=project)
        console.print("[green]卸载成功完成。[/green]")
    except Exception as e:
        handle_command_error(e, "uninstall")


@cli.command()
@click.argument('package', required=False)
@click.option('--project', is_flag=True, help='Upgrade in the current project instead of globally.')
@click.option('--all', 'upgrade_all', is_flag=True, help='Upgrade all packages.')
@click.pass_context
def upgrade(ctx, package, project, upgrade_all):
    """Upgrade a package or all packages."""
    manager = ctx.obj['manager']
    
    try:
        # 检查所需工具是否可用
        tool_checker = manager.tool_checker
        required_tools = ["npm", "pip", "python", "python3"]
        missing_tools = tool_checker.get_missing_tools(required_tools)
        
        if missing_tools:
            missing_tools_msg = tool_checker.get_formatted_missing_tools_message(missing_tools)
            console.print(f"[yellow]警告: 某些包管理器工具不可用，可能会影响升级操作[/yellow]")
            console.print(f"[yellow]{missing_tools_msg}[/yellow]")
        
        scope = "[cyan](项目)[/cyan]" if project else "[cyan](全局)[/cyan]"
        if upgrade_all:
            console.print(f"正在升级所有包 {scope}")
            manager.upgrade_all(project=project)
        elif package:
            console.print(f"正在升级包: [green]{package}[/green] {scope}")
            manager.upgrade(package, project=project)
        else:
            console.print("[red]错误: 请指定包名或使用 --all 升级所有包[/red]")
            sys.exit(1)
            
        console.print("[green]升级成功完成。[/green]")
    except Exception as e:
        handle_command_error(e, "upgrade")


@cli.command()
@click.option('--global', 'global_scan', is_flag=True, help='Scan global dependencies.')
@click.option('--security', is_flag=True, help='Perform security vulnerability scan.')
@click.option('--no-table', is_flag=True, help='Display in simple list format instead of table.')
@click.pass_context
def scan(ctx, global_scan, security, no_table):
    """Scan for dependencies in the current project or globally."""
    manager = ctx.obj['manager']
    
    try:
        if global_scan:
            console.print("[bold]扫描全局依赖 (Scanning global dependencies)[/bold]")
            results = manager.scan_global(security=security)
        else:
            console.print("[bold]扫描项目依赖 (Scanning project dependencies)[/bold]")
            results = manager.scan_project(Path.cwd(), security=security)
            
        # Process and display results
        if results:
            # Separate warnings, errors and regular results
            warnings = [r for r in results if "warning" in r]
            errors = [r for r in results if "error" in r]
            dependencies = [r for r in results if "name" in r and "package_manager" in r]
            package_manager_infos = [r for r in results if "package_manager_info" in r]
            
            # Display warnings first
            if warnings:
                console.print("\n[yellow]警告 (Warnings):[/yellow]")
                for warning in warnings:
                    if warning.get("warning") == "missing_tools":
                        console.print(f"[yellow]- {warning.get('message')}[/yellow]")
                        missing_tools = warning.get("missing_tools", [])
                        for tool in missing_tools:
                            instructions = warning.get("install_instructions", "")
                            console.print(f"  [yellow]- {tool}:[/yellow] {instructions}")
                    else:
                        console.print(f"[yellow]- {warning}[/yellow]")
            
            # Display errors
            if errors:
                console.print("\n[red]错误 (Errors):[/red]")
                for error in errors:
                    if error.get("error") == "command_not_found":
                        pm = error.get("package_manager", "")
                        msg = error.get("message", "")
                        instructions = error.get("install_instructions", "")
                        console.print(f"[red]- {pm}: {msg}[/red]")
                        if instructions:
                            console.print(f"  提示: {instructions}")
                    else:
                        console.print(f"[red]- {error.get('message', str(error))}[/red]")
            
            # Display dependencies in table format if available
            if dependencies:
                if not no_table:
                    # Group dependencies by package manager
                    pm_groups = {}
                    for dep in dependencies:
                        pm = dep.get("package_manager", "unknown")
                        if pm not in pm_groups:
                            pm_groups[pm] = []
                        pm_groups[pm].append(dep)
                    
                    # For each package manager, create a table
                    for pm, deps in pm_groups.items():
                        # Create and display table
                        table = Table(title=f"{pm.capitalize()} 依赖", box=box.ROUNDED)
                        table.add_column("名称 (Name)", style="green bold")
                        table.add_column("版本 (Version)", style="blue")
                        table.add_column("描述 (Description)", style="white", max_width=50, no_wrap=True)
                        
                        for dep in sorted(deps, key=lambda x: x.get('name', '').lower()):
                            name = dep.get('name', 'Unknown')
                            version = dep.get('version', 'Unknown')
                            desc = dep.get('description', '')
                            if len(desc) > 50:
                                desc = desc[:47] + "..."
                            
                            table.add_row(name, version, desc)
                        
                        console.print("\n")
                        if RICH_AVAILABLE:
                            console.print(table)
                        else:
                            # 兼容模式下的表格显示
                            console.print(f"{pm.capitalize()} 依赖:")
                            console.print("-" * 80)
                            console.print(f"{'名称 (Name)':<30} {'版本 (Version)':<15} {'描述 (Description)':<35}")
                            console.print("-" * 80)
                            for dep in sorted(deps, key=lambda x: x.get('name', '').lower()):
                                name = dep.get('name', 'Unknown')
                                version = dep.get('version', 'Unknown')
                                desc = dep.get('description', '')
                                if len(desc) > 35:
                                    desc = desc[:32] + "..."
                                console.print(f"{name:<30} {version:<15} {desc:<35}")
                            
                        console.print(f"{pm} 依赖总数: {len(deps)}")
                else:
                    # Simple list format
                    console.print("\n[bold]依赖列表 (Dependencies):[/bold]")
                    for dep in sorted(dependencies, key=lambda x: x.get('name', '').lower()):
                        name = dep.get('name', 'Unknown')
                        version = dep.get('version', 'Unknown')
                        pm = dep.get('package_manager', 'unknown')
                        console.print(f"- {name} ({version}) [{pm}]")
            
            # If no dependencies but we have errors or warnings, show a message
            if not dependencies and (errors or warnings):
                console.print("\n[yellow]没有找到依赖，请查看上述警告和错误。[/yellow]")
            elif not dependencies:
                console.print("\n无依赖 (No dependencies found).")
                
        else:
            console.print("\n[yellow]没有找到依赖 (No dependencies found).[/yellow]")
            
    except Exception as e:
        handle_command_error(e, "scan")


@cli.command()
@click.argument('package')
@click.pass_context
def path(ctx, package):
    """Show the installation path of a package."""
    manager = ctx.obj['manager']
    
    try:
        # 检查所需工具是否可用
        tool_checker = manager.tool_checker
        required_tools = ["npm", "pip", "python", "python3"]
        missing_tools = tool_checker.get_missing_tools(required_tools)
        
        if missing_tools:
            missing_tools_msg = tool_checker.get_formatted_missing_tools_message(missing_tools)
            console.print(f"[yellow]警告: 某些包管理器工具不可用，可能会影响查找结果[/yellow]")
            console.print(f"[yellow]{missing_tools_msg}[/yellow]")
        
        path = manager.get_package_path(package)
        if path:
            console.print(f"包 [green]'{package}'[/green] 安装路径: [blue]{path}[/blue]")
        else:
            console.print(f"[yellow]未找到包 '{package}'。[/yellow]")
            sys.exit(1)
    except Exception as e:
        handle_command_error(e, "path")


@cli.command()
@click.option('--project', is_flag=True, help='List project dependencies.')
@click.option('--global', 'global_deps', is_flag=True, help='List global dependencies.')
@click.option('--no-table', is_flag=True, help='Display in simple list format instead of table.')
@click.pass_context
def list(ctx, project, global_deps, no_table):
    """List installed dependencies."""
    manager = ctx.obj['manager']
    
    try:
        # 检查所需工具是否可用
        tool_checker = manager.tool_checker
        required_tools = ["npm", "pip", "python", "python3"]
        missing_tools = tool_checker.get_missing_tools(required_tools)
        
        if missing_tools:
            missing_tools_msg = tool_checker.get_formatted_missing_tools_message(missing_tools)
            console.print(f"[yellow]警告: 某些包管理器工具不可用，可能会影响依赖列表[/yellow]")
            console.print(f"[yellow]{missing_tools_msg}[/yellow]")
        
        if not project and not global_deps:
            # Default to project dependencies if no flag is specified
            project = True
            
        if project:
            title = "项目依赖 (Project Dependencies)"
            deps = manager.list_project_dependencies()
        else:
            title = "全局依赖 (Global Dependencies)"
            deps = manager.list_global_dependencies()
            
        if not deps:
            console.print("[yellow]没有找到依赖。(No dependencies found.)[/yellow]")
            return
            
        if no_table:
            # Simple list format
            console.print(f"[bold]{title}:[/bold]")
            for dep in sorted(deps, key=lambda x: x['name'].lower()):
                version_str = f" ([blue]{dep.get('version', '未知')}[/blue])" if dep.get('version') else ""
                console.print(f" - [green]{dep['name']}[/green]{version_str}")
        else:
            # Table format
            table = Table(title=title, box=box.ROUNDED)
            table.add_column("名称 (Name)", style="green bold")
            table.add_column("版本 (Version)", style="blue")
            table.add_column("包管理器 (Package Manager)", style="cyan")
            
            # Add rows
            for dep in sorted(deps, key=lambda x: x['name'].lower()):
                name = dep.get('name', '未知')
                version = dep.get('version', '未知')
                pm = dep.get('package_manager', '未知')
                table.add_row(name, version, pm)
            
            # Display the table
            if RICH_AVAILABLE:
                console.print(table)
            else:
                # 兼容模式下的表格显示
                console.print(f"\n{title}:")
                console.print("-" * 80)
                console.print(f"{'名称 (Name)':<30} {'版本 (Version)':<15} {'包管理器 (Package Manager)':<20}")
                console.print("-" * 80)
                for dep in sorted(deps, key=lambda x: x['name'].lower()):
                    name = dep.get('name', '未知')
                    version = dep.get('version', '未知')
                    pm = dep.get('package_manager', '未知')
                    console.print(f"{name:<30} {version:<15} {pm:<20}")
            
            # Show summary
            console.print(f"\n总计: [bold]{len(deps)}[/bold] 个依赖")
            
    except Exception as e:
        handle_command_error(e, "list")


@cli.command()
@click.option('--project', is_flag=True, help='Show project dependency tree.')
@click.option('--no-color', is_flag=True, help='Disable colorized output.')
@click.pass_context
def tree(ctx, project, no_color):
    """Show dependency tree with improved formatting."""
    manager = ctx.obj['manager']
    
    try:
        # 检查所需工具是否可用
        tool_checker = manager.tool_checker
        required_tools = ["npm", "pip", "python", "python3"]
        missing_tools = tool_checker.get_missing_tools(required_tools)
        
        if missing_tools:
            missing_tools_msg = tool_checker.get_formatted_missing_tools_message(missing_tools)
            console.print(f"[yellow]警告: 某些包管理器工具不可用，可能会影响依赖树显示[/yellow]")
            console.print(f"[yellow]{missing_tools_msg}[/yellow]")
        
        if project:
            if no_color:
                console.print("项目依赖树 (Project Dependency Tree):")
            else:
                console.print("[bold]项目依赖树 (Project Dependency Tree):[/bold]")
                
            tree_data = manager.get_project_dependency_tree()
        else:
            console.print("[red]错误: 目前仅支持项目依赖树。(Error: Currently only project dependency trees are supported.)[/red]")
            sys.exit(1)
            
        if tree_data:
            is_windows = platform.system().lower() == 'windows'
            # Windows和Unix的树结构前缀
            win_prefixes = ['`-- ', '+-- ', '|   ']
            unix_prefixes = ['└── ', '├── ', '│   ']
            
            if no_color:
                for line in tree_data:
                    console.print(line)
            else:
                # Enhanced colorized tree display
                for line in tree_data:
                    # 检查是否有Windows或Unix风格的前缀
                    is_dep_line = False
                    for prefix in (win_prefixes if is_windows else unix_prefixes):
                        if prefix in line:
                            is_dep_line = True
                            break
                            
                    if is_dep_line:
                        # This is a dependency line - 处理Windows和Unix风格
                        # 拆分前缀和内容部分
                        prefix_end = line.find(' ', line.find('--') + 2) if '--' in line else -1
                        if prefix_end > 0:
                            tree_part = line[:prefix_end]
                            dep_part = line[prefix_end:].strip()
                            
                            # Format name and version if available
                            if "@" in dep_part:
                                name, version = dep_part.split("@", 1)
                                formatted_line = f"{tree_part} [green]{name}[/green]@[blue]{version}[/blue]"
                            else:
                                formatted_line = f"{tree_part} [green]{dep_part}[/green]"
                                
                            console.print(formatted_line)
                        else:
                            console.print(line)
                    else:
                        # Root package or header
                        if "@" in line:
                            name, version = line.split("@", 1)
                            console.print(f"[bold green]{name}[/bold green]@[bold blue]{version}[/bold blue]")
                        else:
                            console.print(f"[bold]{line}[/bold]")
        else:
            console.print("[yellow]没有找到依赖。(No dependencies found.)[/yellow]")
            
    except Exception as e:
        handle_command_error(e, "tree")


@cli.command()
@click.argument('keyword')
@click.option('--no-table', is_flag=True, help='Display in simple list format instead of table.')
@click.pass_context
def search(ctx, keyword, no_table):
    """Search for packages."""
    manager = ctx.obj['manager']
    
    try:
        # 检查所需工具是否可用
        tool_checker = manager.tool_checker
        required_tools = ["npm", "pip", "python", "python3"]
        missing_tools = tool_checker.get_missing_tools(required_tools)
        
        if missing_tools:
            missing_tools_msg = tool_checker.get_formatted_missing_tools_message(missing_tools)
            console.print(f"[yellow]警告: 某些包管理器工具不可用，可能会影响搜索结果[/yellow]")
            console.print(f"[yellow]{missing_tools_msg}[/yellow]")
        
        console.print(f"搜索匹配关键词的包: [bold]{keyword}[/bold]")
        results = manager.search_packages(keyword)
        
        if results:
            if no_table:
                # Simple list format
                console.print("\n[bold]搜索结果 (Search Results):[/bold]")
                for result in sorted(results, key=lambda x: x.get('name', '').lower()):
                    name = result.get('name', 'Unknown')
                    pm_name = result.get('package_manager', 'unknown')
                    desc = result.get('description', '')
                    if len(desc) > 70:
                        desc = desc[:67] + "..."
                    console.print(f" - [green]{name}[/green] ([blue]{pm_name}[/blue]): {desc}")
            else:
                # Table format
                table = Table(title="搜索结果 (Search Results)", box=box.ROUNDED)
                table.add_column("名称 (Name)", style="green bold")
                table.add_column("包管理器 (Package Manager)", style="blue")
                table.add_column("描述 (Description)", style="white", max_width=60, no_wrap=True)
                
                # Add rows
                for result in sorted(results, key=lambda x: x.get('name', '').lower()):
                    name = result.get('name', 'Unknown')
                    pm_name = result.get('package_manager', 'unknown')
                    desc = result.get('description', '')
                    if len(desc) > 60:
                        desc = desc[:57] + "..."
                    
                    table.add_row(name, pm_name, desc)
                
                # Display the table
                if RICH_AVAILABLE:
                    console.print(table)
                else:
                    # 兼容模式下的表格显示
                    console.print("\n搜索结果 (Search Results):")
                    console.print("-" * 80)
                    console.print(f"{'名称 (Name)':<30} {'包管理器 (Package Manager)':<20} {'描述 (Description)':<30}")
                    console.print("-" * 80)
                    for result in sorted(results, key=lambda x: x.get('name', '').lower()):
                        name = result.get('name', 'Unknown')
                        pm_name = result.get('package_manager', 'unknown')
                        desc = result.get('description', '')
                        if len(desc) > 30:
                            desc = desc[:27] + "..."
                        console.print(f"{name:<30} {pm_name:<20} {desc:<30}")
                
                # Show summary
                console.print(f"\n总计: [bold]{len(results)}[/bold] 个匹配结果")
        else:
            console.print("[yellow]没有找到匹配的包。(No matching packages found.)[/yellow]")
            
    except Exception as e:
        handle_command_error(e, "search")


if __name__ == '__main__':
    cli() 