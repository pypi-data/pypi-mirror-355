#!/usr/bin/env python3
"""
DepMan - A universal dependency manager CLI.
"""
import sys
from pathlib import Path
import time

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
        console.print("- yarn: https://classic.yarnpkg.com/en/docs/install")
        console.print("- golang: https://golang.org/doc/install")
        console.print("- maven: https://maven.apache.org/install.html")
        console.print("- gradle: https://gradle.org/install/")
        
        # 如果是Windows系统，提供更具体的PATH建议
        if platform.system() == "Windows":
            console.print("\n[yellow]Windows用户提示: 请确保安装后重启命令提示符或PowerShell，或手动将工具路径添加到系统PATH中。[/yellow]")
            console.print("添加到PATH的方法: 控制面板 -> 系统 -> 高级系统设置 -> 环境变量 -> 选择Path -> 编辑 -> 添加工具路径")
        elif platform.system() == "Darwin":  # macOS
            console.print("\n[yellow]macOS用户提示: 使用Homebrew安装工具通常会自动添加到PATH中。如果使用其他方式安装，可能需要手动添加。[/yellow]")
            console.print("添加到PATH的方法: 编辑~/.bash_profile或~/.zshrc文件，添加'export PATH=/path/to/tool:$PATH'，然后运行'source ~/.bash_profile'或'source ~/.zshrc'")
        else:  # Linux
            console.print("\n[yellow]Linux用户提示: 使用包管理器安装工具通常会自动添加到PATH中。如果使用其他方式安装，可能需要手动添加。[/yellow]")
            console.print("添加到PATH的方法: 编辑~/.bashrc文件，添加'export PATH=/path/to/tool:$PATH'，然后运行'source ~/.bashrc'")
        
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
        console.print("- Go: go.mod")
        console.print("- PHP: composer.json")
        console.print("- .NET: .csproj, .vbproj, packages.config")
        
        # 提供创建新项目的建议
        console.print("\n如果这是一个新项目，您可能需要先初始化项目配置文件。常见初始化命令:")
        console.print("- JavaScript: npm init")
        console.print("- Python: pip freeze > requirements.txt 或 poetry init")
        console.print("- Go: go mod init <module_name>")
        console.print("- Rust: cargo init")
    
    # 检查是否为权限错误
    elif any(x in error_msg.lower() for x in ["permission denied", "access is denied", "需要权限"]):
        console.print("\n[yellow]提示: 操作失败，可能是因为权限不足。尝试使用管理员权限运行命令。[/yellow]")
        system = platform.system()
        if system == "Linux" or system == "Darwin":  # Linux 或 macOS
            console.print("在 Linux/macOS 上尝试使用 sudo:")
            console.print("  sudo depman <命令>")
            console.print("\n或者考虑为用户目录设置正确的权限:")
            console.print("  sudo chown -R $(whoami) ~/.npm ~/.pip ~/.local")
        elif system == "Windows":  # Windows
            console.print("在 Windows 上尝试右键点击命令提示符或 PowerShell，选择'以管理员身份运行'，然后再执行命令。")
            console.print("\n如果使用的是VSCode或其他IDE，请尝试以管理员身份运行IDE。")
    
    # 网络错误
    elif any(x in error_msg.lower() for x in ["connection", "network", "timeout", "连接", "网络", "超时", "proxy", "代理"]):
        console.print("\n[yellow]提示: 操作失败，可能是因为网络问题。请检查您的网络连接，然后重试。[/yellow]")
        console.print("可能的解决方案:")
        console.print("1. 检查您的网络连接是否正常")
        console.print("2. 确认是否需要配置代理")
        console.print("3. 尝试切换到其他网络环境")
        console.print("4. 检查防火墙或杀毒软件是否阻止了网络连接")
        console.print("5. 如果使用公司网络，可能需要联系IT部门获取帮助")
        
        if command_name and command_name in ["install", "upgrade", "search"]:
            console.print("\n对于网络问题，您可以尝试使用国内镜像源:")
            console.print("- npm: npm config set registry https://registry.npmmirror.com")
            console.print("- pip: pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple")
    
    # 版本冲突
    elif any(x in error_msg.lower() for x in ["version conflict", "incompatible", "不兼容", "版本冲突", "dependency conflict", "依赖冲突"]):
        console.print("\n[yellow]提示: 操作失败，可能是因为版本冲突或依赖冲突。[/yellow]")
        console.print("可能的解决方案:")
        console.print("1. 尝试指定兼容的版本: depman install <包名>@<特定版本>")
        console.print("2. 更新所有相关依赖: depman upgrade --all")
        console.print("3. 检查项目的依赖树，识别冲突: depman tree")
        console.print("4. 考虑使用虚拟环境或隔离环境管理依赖")
        
    # 磁盘空间不足
    elif any(x in error_msg.lower() for x in ["disk space", "空间不足", "no space left", "磁盘已满"]):
        console.print("\n[yellow]提示: 操作失败，可能是因为磁盘空间不足。[/yellow]")
        console.print("可能的解决方案:")
        console.print("1. 清理磁盘空间")
        console.print("2. 清理包管理器缓存:")
        console.print("   - npm: npm cache clean --force")
        console.print("   - pip: pip cache purge")
        console.print("3. 删除未使用的依赖")
        
    # 包不存在
    elif any(x in error_msg.lower() for x in ["not found", "no matching", "找不到包", "不存在", "未找到"]):
        console.print("\n[yellow]提示: 操作失败，可能是因为指定的包不存在或名称错误。[/yellow]")
        console.print("可能的解决方案:")
        console.print("1. 检查包名是否正确，注意大小写")
        console.print("2. 搜索类似的包: depman search <关键词>")
        console.print("3. 检查是否需要指定特定的包管理器: depman install <包名> --manager <包管理器>")
        console.print("4. 确认包在指定的仓库中可用")
        
    # 其他未知错误
    else:
        console.print("\n[yellow]提示: 发生了未知错误。如果问题持续存在，请尝试以下方法:[/yellow]")
        console.print("1. 检查命令语法是否正确")
        console.print("2. 更新 depman 到最新版本")
        console.print("3. 查看详细日志文件 (~/.depman/logs/depman.log)")
        console.print("4. 搜索在线文档或社区获取帮助")
        console.print("5. 报告问题: https://github.com/yourusername/depman/issues")
        
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
    start_time = time.time()
    
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
        
        installed_items = []
        
        if package:
            scope = "[cyan](项目)[/cyan]" if project else "[cyan](全局)[/cyan]"
            console.print(f"正在安装包: [green]{package}[/green] {scope}")
            
            # Use specified package manager if provided
            if manager:
                console.print(f"使用包管理器: [blue]{manager}[/blue]")
                result = manager_obj.install(package, project=project, pkg_manager=manager)
                if isinstance(result, dict):
                    installed_items.append(result)
                elif isinstance(result, bool) and result:
                    installed_items.append({"name": package, "package_manager": manager})
            else:
                result = manager_obj.install(package, project=project)
                if isinstance(result, dict):
                    installed_items.append(result)
                elif isinstance(result, bool) and result:
                    installed_items.append({"name": package})
                
        elif file:
            console.print(f"从文件安装依赖: [blue]{file}[/blue]")
            results = manager_obj.install_from_file(file)
            if isinstance(results, list):
                installed_items.extend(results)
        elif project:
            console.print("安装所有项目依赖")
            results = manager_obj.install_all_project_dependencies()
            if isinstance(results, list):
                installed_items.extend(results)
        else:
            console.print("[red]错误: 请指定包名或使用 --project 安装所有项目依赖[/red]")
            sys.exit(1)
        
        # 计算执行时间
        execution_time = time.time() - start_time
        
        # 格式化执行时间
        if execution_time < 1:
            time_str = f"{execution_time * 1000:.0f}毫秒"
        elif execution_time < 60:
            time_str = f"{execution_time:.2f}秒"
        else:
            minutes = int(execution_time // 60)
            seconds = execution_time % 60
            time_str = f"{minutes}分{seconds:.2f}秒"
        
        # 显示安装结果摘要
        if installed_items:
            # 检查是否为单个包安装
            if package and len(installed_items) == 1:
                item = installed_items[0]
                version = item.get("version", "未知版本")
                pm = item.get("package_manager", "未知包管理器")
                path = item.get("path", "")
                
                console.print(f"[bold green]安装成功:[/bold green] {package} ({version}) 使用 {pm}")
                
                # 如果有安装路径，显示它
                if path:
                    console.print(f"安装路径: [blue]{path}[/blue]")
                
                # 如果有安装大小，显示它
                if "installed_size" in item and item["installed_size"]:
                    size = format_size(item["installed_size"])
                    console.print(f"安装大小: {size}")
                
                # 显示执行时间
                console.print(f"安装耗时: {time_str}")
                
                # 提供使用建议（如果适用）
                if pm == "npm" or pm == "yarn":
                    console.print("\n[cyan]提示: 您可以使用以下方式在JavaScript中导入此包:[/cyan]")
                    console.print(f"  import * as {package.replace('-', '_')} from '{package}';")
                elif pm == "pip":
                    console.print("\n[cyan]提示: 您可以使用以下方式在Python中导入此包:[/cyan]")
                    console.print(f"  import {package.replace('-', '_')}")
            else:
                # 多个包安装结果摘要
                total_count = len(installed_items)
                pm_counts = {}
                
                for item in installed_items:
                    pm = item.get("package_manager", "未知")
                    if pm in pm_counts:
                        pm_counts[pm] += 1
                    else:
                        pm_counts[pm] = 1
                
                # 显示总结信息
                console.print(f"[bold green]安装成功完成！[/bold green] 共安装了 {total_count} 个包")
                
                # 按包管理器显示统计
                for pm, count in pm_counts.items():
                    console.print(f"- {pm}: {count} 个包")
                
                # 显示执行时间
                console.print(f"安装耗时: {time_str}")
        else:
            console.print(f"[green]安装成功完成。耗时: {time_str}[/green]")
            
        # 提供下一步建议
        if project and installed_items:
            console.print("\n[cyan]下一步操作建议:[/cyan]")
            console.print("1. 使用 'depman list --project' 查看已安装的依赖")
            console.print("2. 使用 'depman tree --project' 查看依赖树")
            
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


@cli.command()
@click.argument('command_name', required=False)
@click.pass_context
def help(ctx, command_name):
    """
    显示命令的详细帮助信息。
    如果没有指定命令名称，则显示所有可用命令的概览。
    """
    # 命令的详细帮助信息
    help_info = {
        "install": {
            "description": "安装包或项目依赖",
            "usage": "depman install [PACKAGE] [OPTIONS]",
            "arguments": [
                {"name": "PACKAGE", "description": "要安装的包名称（可选）"}
            ],
            "options": [
                {"name": "--project", "description": "在当前项目中安装而不是全局安装"},
                {"name": "--file PATH", "description": "从指定的依赖文件安装"},
                {"name": "--manager NAME", "description": "指定要使用的包管理器（pip, npm, brew等）"}
            ],
            "examples": [
                {"cmd": "depman install requests", "desc": "全局安装requests包"},
                {"cmd": "depman install react --project", "desc": "在当前项目中安装react包"},
                {"cmd": "depman install --file requirements.txt", "desc": "从requirements.txt文件安装所有依赖"},
                {"cmd": "depman install --project", "desc": "安装当前项目的所有依赖"},
                {"cmd": "depman install pandas --manager pip", "desc": "使用pip安装pandas包"}
            ]
        },
        "uninstall": {
            "description": "卸载包",
            "usage": "depman uninstall PACKAGE [OPTIONS]",
            "arguments": [
                {"name": "PACKAGE", "description": "要卸载的包名称"}
            ],
            "options": [
                {"name": "--project", "description": "从当前项目中卸载而不是全局卸载"}
            ],
            "examples": [
                {"cmd": "depman uninstall requests", "desc": "全局卸载requests包"},
                {"cmd": "depman uninstall react --project", "desc": "从当前项目中卸载react包"}
            ]
        },
        "upgrade": {
            "description": "升级包或所有包",
            "usage": "depman upgrade [PACKAGE] [OPTIONS]",
            "arguments": [
                {"name": "PACKAGE", "description": "要升级的包名称（可选）"}
            ],
            "options": [
                {"name": "--project", "description": "在当前项目中升级而不是全局升级"},
                {"name": "--all", "description": "升级所有包"}
            ],
            "examples": [
                {"cmd": "depman upgrade requests", "desc": "全局升级requests包"},
                {"cmd": "depman upgrade react --project", "desc": "在当前项目中升级react包"},
                {"cmd": "depman upgrade --all", "desc": "升级所有全局包"},
                {"cmd": "depman upgrade --all --project", "desc": "升级当前项目的所有包"}
            ]
        },
        "scan": {
            "description": "扫描当前项目或全局的依赖",
            "usage": "depman scan [OPTIONS]",
            "options": [
                {"name": "--global", "description": "扫描全局依赖而不是项目依赖"},
                {"name": "--security", "description": "执行安全漏洞扫描"},
                {"name": "--no-table", "description": "以简单列表格式显示而不是表格"}
            ],
            "examples": [
                {"cmd": "depman scan", "desc": "扫描当前项目的依赖"},
                {"cmd": "depman scan --global", "desc": "扫描全局依赖"},
                {"cmd": "depman scan --security", "desc": "扫描当前项目依赖的安全漏洞"},
                {"cmd": "depman scan --no-table", "desc": "以简单列表格式显示扫描结果"}
            ]
        },
        "path": {
            "description": "显示包的安装路径",
            "usage": "depman path PACKAGE",
            "arguments": [
                {"name": "PACKAGE", "description": "要查找的包名称"}
            ],
            "examples": [
                {"cmd": "depman path requests", "desc": "显示requests包的安装路径"}
            ]
        },
        "list": {
            "description": "列出已安装的依赖",
            "usage": "depman list [OPTIONS]",
            "options": [
                {"name": "--project", "description": "列出项目依赖而不是全局依赖"},
                {"name": "--global", "description": "列出全局依赖（默认为项目依赖）"},
                {"name": "--no-table", "description": "以简单列表格式显示而不是表格"}
            ],
            "examples": [
                {"cmd": "depman list", "desc": "列出当前项目的依赖"},
                {"cmd": "depman list --global", "desc": "列出全局依赖"},
                {"cmd": "depman list --no-table", "desc": "以简单列表格式显示依赖"}
            ]
        },
        "tree": {
            "description": "显示依赖树",
            "usage": "depman tree [OPTIONS]",
            "options": [
                {"name": "--project", "description": "显示项目依赖树"},
                {"name": "--no-color", "description": "禁用彩色输出"}
            ],
            "examples": [
                {"cmd": "depman tree --project", "desc": "显示当前项目的依赖树"},
                {"cmd": "depman tree --project --no-color", "desc": "显示不带彩色的项目依赖树"}
            ]
        },
        "search": {
            "description": "搜索包",
            "usage": "depman search KEYWORD [OPTIONS]",
            "arguments": [
                {"name": "KEYWORD", "description": "搜索关键词"}
            ],
            "options": [
                {"name": "--no-table", "description": "以简单列表格式显示而不是表格"}
            ],
            "examples": [
                {"cmd": "depman search react", "desc": "搜索包含'react'的包"},
                {"cmd": "depman search python --no-table", "desc": "以简单列表格式搜索包含'python'的包"}
            ]
        },
        "doctor": {
            "description": "诊断系统环境和依赖管理工具，提供修复建议",
            "usage": "depman doctor [OPTIONS]",
            "options": [
                {"name": "--verbose", "description": "显示详细诊断信息"}
            ],
            "examples": [
                {"cmd": "depman doctor", "desc": "诊断系统环境并显示摘要结果"},
                {"cmd": "depman doctor --verbose", "desc": "显示详细的诊断信息，包括所有工具的完整状态"}
            ]
        },
        "info": {
            "description": "获取包的详细信息，包括版本、描述、许可证、依赖等",
            "usage": "depman info PACKAGE [OPTIONS]",
            "arguments": [
                {"name": "PACKAGE", "description": "要查询的包名称"}
            ],
            "options": [
                {"name": "--manager NAME", "description": "指定包管理器 (pip, npm, brew等)"},
                {"name": "--verbose", "description": "显示更详细的包信息"}
            ],
            "examples": [
                {"cmd": "depman info requests", "desc": "获取requests包的详细信息"},
                {"cmd": "depman info react --manager npm", "desc": "使用npm获取react包的详细信息"},
                {"cmd": "depman info pandas --verbose", "desc": "获取pandas包的详尽信息，包括元数据"}
            ]
        },
        "clean": {
            "description": "清理未使用的依赖和包管理器缓存",
            "usage": "depman clean [OPTIONS]",
            "options": [
                {"name": "--cache", "description": "仅清理包管理器缓存"},
                {"name": "--unused", "description": "仅清理未使用的依赖"},
                {"name": "--all", "description": "清理所有缓存和未使用的依赖"},
                {"name": "--dry-run", "description": "模拟运行，不实际删除任何内容"},
                {"name": "--manager NAME", "description": "指定要清理的包管理器 (pip, npm, yarn等)"}
            ],
            "examples": [
                {"cmd": "depman clean", "desc": "清理缓存和未使用的依赖"},
                {"cmd": "depman clean --cache", "desc": "仅清理包管理器缓存"},
                {"cmd": "depman clean --unused", "desc": "仅清理未使用的依赖"},
                {"cmd": "depman clean --dry-run", "desc": "模拟清理，显示将要清理的内容但不实际删除"},
                {"cmd": "depman clean --manager npm", "desc": "仅清理npm的缓存和未使用依赖"}
            ]
        },
        "help": {
            "description": "显示命令的详细帮助信息",
            "usage": "depman help [COMMAND]",
            "arguments": [
                {"name": "COMMAND", "description": "要查看帮助的命令名称（可选）"}
            ],
            "examples": [
                {"cmd": "depman help", "desc": "显示所有可用命令的概览"},
                {"cmd": "depman help install", "desc": "显示install命令的详细帮助"}
            ]
        }
    }

    if command_name:
        # 显示特定命令的详细帮助
        if command_name in help_info:
            cmd_help = help_info[command_name]
            
            # 显示命令信息
            console.print(f"\n[bold]命令: [green]{command_name}[/green][/bold]")
            console.print(f"\n[bold cyan]描述:[/bold cyan]")
            console.print(f"  {cmd_help['description']}")
            console.print(f"\n[bold cyan]用法:[/bold cyan]")
            console.print(f"  {cmd_help['usage']}")
            
            # 显示参数
            if "arguments" in cmd_help and cmd_help["arguments"]:
                console.print(f"\n[bold cyan]参数:[/bold cyan]")
                for arg in cmd_help["arguments"]:
                    console.print(f"  [bold]{arg['name']}[/bold]: {arg['description']}")
            
            # 显示选项
            if "options" in cmd_help and cmd_help["options"]:
                console.print(f"\n[bold cyan]选项:[/bold cyan]")
                for opt in cmd_help["options"]:
                    console.print(f"  [bold]{opt['name']}[/bold]: {opt['description']}")
            
            # 显示示例
            if "examples" in cmd_help and cmd_help["examples"]:
                console.print(f"\n[bold cyan]示例:[/bold cyan]")
                for example in cmd_help["examples"]:
                    console.print(f"  [bold green]{example['cmd']}[/bold green]")
                    console.print(f"    {example['desc']}")
        else:
            console.print(f"[red]错误: 未知命令 '{command_name}'[/red]")
            console.print("使用 'depman help' 查看所有可用命令")
    else:
        # 显示所有命令的概览
        console.print("\n[bold]DepMan - 通用依赖管理工具[/bold]")
        console.print("\n一个管理不同包管理器和语言依赖的工具。")
        
        console.print("\n[bold cyan]可用命令:[/bold cyan]")
        # 按照字母顺序排序命令
        for cmd_name in sorted(help_info.keys()):
            cmd = help_info[cmd_name]
            console.print(f"  [bold green]{cmd_name}[/bold green]: {cmd['description']}")
        
        console.print("\n使用 'depman help COMMAND' 查看特定命令的详细帮助")
        console.print("例如: depman help install")


@cli.command()
@click.option('--verbose', is_flag=True, help='显示详细诊断信息')
@click.pass_context
def doctor(ctx, verbose):
    """
    诊断系统环境和依赖管理工具，提供修复建议。
    """
    manager = ctx.obj['manager']
    console.print("[bold]DepMan 系统诊断 (System Diagnosis)[/bold]")
    console.print("正在检查系统环境和依赖管理工具...\n")
    
    # 收集结果
    diagnosis_results = {
        "errors": [],
        "warnings": [],
        "passed": []
    }
    
    # 检查操作系统信息
    try:
        os_info = manager.os_utils.get_os_info()
        os_name = os_info.get("system", "unknown").capitalize()
        
        if os_info["system"] == "linux":
            os_display = f"{os_name} ({os_info.get('distribution', '').capitalize()} {os_info.get('distribution_version', '')})"
        elif os_info["system"] == "darwin":
            os_display = f"macOS {os_info.get('macos_version', '')}"
        elif os_info["system"] == "windows":
            os_display = f"Windows {os_info.get('windows_version', '')}"
        else:
            os_display = os_name
        
        diagnosis_results["passed"].append({
            "name": "操作系统",
            "value": os_display,
            "details": os_info if verbose else None
        })
    except Exception as e:
        diagnosis_results["warnings"].append({
            "name": "操作系统检测",
            "message": f"无法获取操作系统信息: {str(e)}",
            "fix": "这不会影响基本功能，但某些特定于操作系统的功能可能不可用。"
        })
    
    # 检查Python环境
    try:
        python_version = platform.python_version()
        diagnosis_results["passed"].append({
            "name": "Python版本",
            "value": python_version,
            "details": f"位置: {sys.executable}" if verbose else None
        })
        
        if float(python_version.split('.')[0] + '.' + python_version.split('.')[1]) < 3.6:
            diagnosis_results["warnings"].append({
                "name": "Python版本",
                "message": f"Python {python_version} 是旧版本，建议升级到Python 3.6+",
                "fix": "访问 https://www.python.org/downloads/ 下载并安装较新的Python版本。"
            })
    except Exception as e:
        diagnosis_results["errors"].append({
            "name": "Python环境",
            "message": f"无法获取Python版本信息: {str(e)}",
            "fix": "请确保Python正确安装并添加到PATH中。"
        })
    
    # 检查必要工具
    essential_tools = ["pip", "npm", "yarn", "pip3", "python", "python3"]
    optional_tools = ["go", "cargo", "gem", "composer", "mvn", "gradle", "dotnet", "brew", "apt", "choco"]
    
    # 检查必要工具
    missing_essential = []
    for tool in essential_tools:
        if not manager.tool_checker.check_tool(tool):
            missing_essential.append(tool)
        else:
            # 尝试获取工具版本
            try:
                version_cmd = {
                    "pip": ["pip", "--version"],
                    "pip3": ["pip3", "--version"],
                    "npm": ["npm", "--version"],
                    "yarn": ["yarn", "--version"],
                    "python": ["python", "--version"],
                    "python3": ["python3", "--version"]
                }
                
                if tool in version_cmd:
                    result = manager.cmd_executor.run_command(version_cmd[tool])
                    version = result.stdout.strip() if result.success else "未知"
                else:
                    version = "已安装"
                
                diagnosis_results["passed"].append({
                    "name": f"{tool}",
                    "value": version,
                    "details": None
                })
            except Exception:
                diagnosis_results["passed"].append({
                    "name": f"{tool}",
                    "value": "已安装",
                    "details": None
                })
    
    # 如果缺少必要工具，添加警告
    if missing_essential:
        missing_tools_msg = manager.tool_checker.get_formatted_missing_tools_message(missing_essential)
        diagnosis_results["warnings"].append({
            "name": "必要工具缺失",
            "message": f"以下工具不可用: {', '.join(missing_essential)}",
            "fix": missing_tools_msg
        })
    
    # 检查可选工具
    missing_optional = []
    for tool in optional_tools:
        if not manager.tool_checker.check_tool(tool):
            missing_optional.append(tool)
        else:
            # 尝试获取工具版本
            try:
                version_cmd = {
                    "go": ["go", "version"],
                    "cargo": ["cargo", "--version"],
                    "gem": ["gem", "--version"],
                    "composer": ["composer", "--version"],
                    "mvn": ["mvn", "--version"],
                    "gradle": ["gradle", "--version"],
                    "dotnet": ["dotnet", "--version"],
                    "brew": ["brew", "--version"],
                    "apt": ["apt", "--version"],
                    "choco": ["choco", "--version"]
                }
                
                if tool in version_cmd:
                    result = manager.cmd_executor.run_command(version_cmd[tool])
                    version = result.stdout.strip() if result.success else "已安装"
                else:
                    version = "已安装"
                
                diagnosis_results["passed"].append({
                    "name": f"{tool}",
                    "value": version,
                    "details": None
                })
            except Exception:
                diagnosis_results["passed"].append({
                    "name": f"{tool}",
                    "value": "已安装",
                    "details": None
                })
    
    # 如果缺少可选工具，添加信息
    if missing_optional and verbose:
        diagnosis_results["warnings"].append({
            "name": "可选工具缺失",
            "message": f"以下可选工具不可用: {', '.join(missing_optional)}",
            "fix": "这些工具不是必需的，但安装它们可以扩展DepMan的功能。"
        })
    
    # 检查网络连接
    try:
        # 尝试连接到常用包仓库
        repos = [
            {"name": "PyPI", "url": "https://pypi.org"},
            {"name": "npm", "url": "https://registry.npmjs.org"}
        ]
        
        for repo in repos:
            try:
                import urllib.request
                with urllib.request.urlopen(repo["url"], timeout=5) as response:
                    if response.status == 200:
                        diagnosis_results["passed"].append({
                            "name": f"{repo['name']}连接",
                            "value": "正常",
                            "details": None
                        })
                    else:
                        diagnosis_results["warnings"].append({
                            "name": f"{repo['name']}连接",
                            "message": f"连接到{repo['name']}返回状态码{response.status}",
                            "fix": "检查您的网络连接或代理设置，或者网站可能暂时不可用。"
                        })
            except Exception as e:
                diagnosis_results["warnings"].append({
                    "name": f"{repo['name']}连接",
                    "message": f"无法连接到{repo['name']}: {str(e)}",
                    "fix": "检查您的网络连接或代理设置。"
                })
    except Exception as e:
        diagnosis_results["warnings"].append({
            "name": "网络连接",
            "message": f"无法执行网络检查: {str(e)}",
            "fix": "检查您的网络连接。"
        })
    
    # 检查权限
    try:
        is_admin = manager.os_utils.is_admin()
        needs_sudo = manager.os_utils.needs_sudo()
        
        if is_admin:
            diagnosis_results["passed"].append({
                "name": "权限检查",
                "value": "管理员权限",
                "details": None
            })
        elif needs_sudo:
            diagnosis_results["warnings"].append({
                "name": "权限检查",
                "message": "当前用户没有管理员权限，可能需要sudo/管理员权限进行全局操作",
                "fix": "使用sudo运行全局命令或以管理员身份运行终端。"
            })
        else:
            diagnosis_results["passed"].append({
                "name": "权限检查",
                "value": "普通用户权限（足够）",
                "details": None
            })
    except Exception as e:
        diagnosis_results["warnings"].append({
            "name": "权限检查",
            "message": f"无法检查权限: {str(e)}",
            "fix": "如果安装包时遇到权限问题，尝试使用sudo或管理员权限。"
        })
    
    # 输出诊断结果
    # 首先显示通过的检查
    if diagnosis_results["passed"]:
        console.print("\n[bold green]通过的检查:[/bold green]")
        for check in diagnosis_results["passed"]:
            console.print(f"  ✓ [green]{check['name']}:[/green] {check['value']}")
            if verbose and check['details']:
                if isinstance(check['details'], dict):
                    for k, v in check['details'].items():
                        console.print(f"    - {k}: {v}")
                else:
                    console.print(f"    {check['details']}")
    
    # 显示警告
    if diagnosis_results["warnings"]:
        console.print("\n[bold yellow]警告:[/bold yellow]")
        for warning in diagnosis_results["warnings"]:
            console.print(f"  ⚠ [yellow]{warning['name']}:[/yellow] {warning['message']}")
            console.print(f"    [cyan]修复建议:[/cyan] {warning['fix']}")
    
    # 显示错误
    if diagnosis_results["errors"]:
        console.print("\n[bold red]错误:[/bold red]")
        for error in diagnosis_results["errors"]:
            console.print(f"  ✗ [red]{error['name']}:[/red] {error['message']}")
            console.print(f"    [cyan]修复建议:[/cyan] {error['fix']}")
    
    # 总结
    console.print("\n[bold]诊断总结:[/bold]")
    error_count = len(diagnosis_results["errors"])
    warning_count = len(diagnosis_results["warnings"])
    pass_count = len(diagnosis_results["passed"])
    
    if error_count == 0 and warning_count == 0:
        console.print("[bold green]✓ 所有检查都已通过！系统环境看起来很健康。[/bold green]")
    elif error_count == 0:
        console.print(f"[bold yellow]⚠ 发现 {warning_count} 个警告，但没有严重错误。大多数功能应该可以正常工作。[/bold yellow]")
    else:
        console.print(f"[bold red]✗ 发现 {error_count} 个错误和 {warning_count} 个警告。请解决这些问题以确保功能正常。[/bold red]")
    
    console.print(f"\n总共执行了 {pass_count + warning_count + error_count} 项检查：[green]{pass_count} 通过[/green]，[yellow]{warning_count} 警告[/yellow]，[red]{error_count} 错误[/red]")
    
    # 提供最终建议
    if error_count > 0 or warning_count > 0:
        console.print("\n[bold cyan]建议:[/bold cyan]")
        console.print("1. 解决上述错误和警告")
        console.print("2. 安装所有必要的工具和依赖")
        console.print("3. 再次运行 'depman doctor' 检查问题是否已解决")
        console.print("\n如需更详细的诊断信息，请使用 '--verbose' 选项：")
        console.print("  depman doctor --verbose")


@cli.command()
@click.argument('package')
@click.option('--manager', help='指定包管理器 (pip, npm, brew等)')
@click.option('--verbose', is_flag=True, help='显示更详细的包信息')
@click.pass_context
def info(ctx, package, manager, verbose):
    """
    获取包的详细信息，包括版本、描述、许可证、依赖等。
    """
    manager_obj = ctx.obj['manager']
    
    try:
        console.print(f"正在获取包 [bold green]{package}[/bold green] 的详细信息...")
        
        # 如果指定了包管理器，使用它
        if manager:
            console.print(f"使用包管理器: [blue]{manager}[/blue]")
            
        # 获取包信息
        package_info = manager_obj.get_package_info(package, pkg_manager=manager)
        
        if not package_info:
            console.print(f"[red]错误: 未找到包 '{package}'。请检查包名或尝试指定包管理器。[/red]")
            sys.exit(1)
            
        # 显示基本信息
        console.print("\n[bold]包信息:[/bold]")
        console.print(f"[bold cyan]名称:[/bold cyan] {package_info.get('name', package)}")
        console.print(f"[bold cyan]版本:[/bold cyan] {package_info.get('version', '未知')}")
        console.print(f"[bold cyan]包管理器:[/bold cyan] {package_info.get('package_manager', '未知')}")
        
        if 'description' in package_info and package_info['description']:
            console.print(f"[bold cyan]描述:[/bold cyan] {package_info.get('description', '')}")
            
        if 'homepage' in package_info and package_info['homepage']:
            console.print(f"[bold cyan]主页:[/bold cyan] {package_info.get('homepage', '')}")
            
        if 'license' in package_info and package_info['license']:
            console.print(f"[bold cyan]许可证:[/bold cyan] {package_info.get('license', '')}")
            
        if 'author' in package_info and package_info['author']:
            console.print(f"[bold cyan]作者:[/bold cyan] {package_info.get('author', '')}")
            
        if 'installed_size' in package_info and package_info['installed_size']:
            size = format_size(package_info['installed_size'])
            console.print(f"[bold cyan]安装大小:[/bold cyan] {size}")
            
        if 'install_date' in package_info and package_info['install_date']:
            console.print(f"[bold cyan]安装日期:[/bold cyan] {package_info.get('install_date', '')}")
            
        if 'path' in package_info and package_info['path']:
            console.print(f"[bold cyan]安装路径:[/bold cyan] {package_info.get('path', '')}")
        
        # 显示依赖
        if 'dependencies' in package_info and package_info['dependencies']:
            deps = package_info['dependencies']
            if isinstance(deps, list) and deps:
                console.print("\n[bold]依赖:[/bold]")
                for dep in sorted(deps):
                    console.print(f"  • {dep}")
            elif isinstance(deps, dict) and deps:
                console.print("\n[bold]依赖:[/bold]")
                for dep_name, dep_version in sorted(deps.items()):
                    console.print(f"  • {dep_name}: {dep_version}")
                    
        # 显示被依赖情况
        if 'dependents' in package_info and package_info['dependents']:
            deps = package_info['dependents']
            console.print("\n[bold]被以下包依赖:[/bold]")
            for dep in sorted(deps):
                console.print(f"  • {dep}")
                
        # 显示详细元数据
        if verbose and 'metadata' in package_info and package_info['metadata']:
            console.print("\n[bold]详细元数据:[/bold]")
            metadata = package_info['metadata']
            if isinstance(metadata, dict):
                for key, value in sorted(metadata.items()):
                    # 跳过已经显示的或过于复杂的字段
                    if key.lower() in ['name', 'version', 'description', 'homepage', 'license', 'author', 'dependencies']:
                        continue
                        
                    # 格式化复杂值
                    if isinstance(value, dict):
                        console.print(f"  [cyan]{key}:[/cyan]")
                        for subkey, subvalue in value.items():
                            if isinstance(subvalue, (list, dict)):
                                continue
                            console.print(f"    - {subkey}: {subvalue}")
                    elif isinstance(value, list):
                        if not value or not isinstance(value[0], (dict, list)):
                            console.print(f"  [cyan]{key}:[/cyan] {', '.join(str(v) for v in value)}")
                    else:
                        console.print(f"  [cyan]{key}:[/cyan] {value}")
        
        # 显示安全信息
        if 'security' in package_info and package_info['security']:
            security_info = package_info['security']
            if 'vulnerabilities' in security_info and security_info['vulnerabilities']:
                vulns = security_info['vulnerabilities']
                console.print("\n[bold red]安全漏洞:[/bold red]")
                for vuln in vulns:
                    console.print(f"  [red]• {vuln.get('id')}: {vuln.get('title', '未知漏洞')}[/red]")
                    console.print(f"    严重程度: {vuln.get('severity', '未知')}")
                    console.print(f"    描述: {vuln.get('description', '无描述')}")
                    if 'affected_versions' in vuln:
                        console.print(f"    影响版本: {', '.join(vuln['affected_versions'])}")
                    if 'fixed_versions' in vuln:
                        console.print(f"    修复版本: {', '.join(vuln['fixed_versions'])}")
                    if 'references' in vuln and vuln['references']:
                        console.print(f"    参考链接: {vuln['references'][0]}")
            else:
                console.print("\n[bold green]安全状态: 未发现已知漏洞[/bold green]")
                
        # 显示使用提示
        if 'usage' in package_info and package_info['usage']:
            console.print("\n[bold]使用示例:[/bold]")
            console.print(package_info['usage'])
            
    except Exception as e:
        handle_command_error(e, "info")


@cli.command()
@click.option('--cache', is_flag=True, help='仅清理包管理器缓存')
@click.option('--unused', is_flag=True, help='仅清理未使用的依赖')
@click.option('--all', 'clean_all', is_flag=True, help='清理所有缓存和未使用的依赖')
@click.option('--dry-run', is_flag=True, help='模拟运行，不实际删除任何内容')
@click.option('--manager', help='指定要清理的包管理器 (pip, npm, yarn等)')
@click.pass_context
def clean(ctx, cache, unused, clean_all, dry_run, manager):
    """
    清理未使用的依赖和包管理器缓存。
    
    如果不指定选项，将同时清理缓存和未使用的依赖。
    """
    manager_obj = ctx.obj['manager']
    
    # 如果没有指定具体操作，则默认全部清理
    if not cache and not unused and not clean_all:
        clean_all = True
    
    # 提取缓存状态
    run_cache_clean = cache or clean_all
    run_unused_clean = unused or clean_all
    
    try:
        # 检查工具可用性
        tool_checker = manager_obj.tool_checker
        required_tools = ["npm", "pip", "python", "python3"]
        if manager:
            required_tools.append(manager)
        
        missing_tools = tool_checker.get_missing_tools(required_tools)
        
        if missing_tools:
            missing_tools_msg = tool_checker.get_formatted_missing_tools_message(missing_tools)
            console.print(f"[yellow]警告: 某些包管理器工具不可用，可能会影响清理操作[/yellow]")
            console.print(f"[yellow]{missing_tools_msg}[/yellow]")
            
            # 如果指定的包管理器不可用，直接报错
            if manager and manager in missing_tools:
                console.print(f"[red]错误: 指定的包管理器 '{manager}' 不可用[/red]")
                sys.exit(1)
        
        # 显示操作模式
        mode_desc = []
        if run_cache_clean:
            mode_desc.append("缓存")
        if run_unused_clean:
            mode_desc.append("未使用的依赖")
        
        if dry_run:
            console.print(f"[bold]模拟清理 {', '.join(mode_desc)}...[/bold]")
            console.print("[yellow]注意: 这是模拟运行，不会实际删除任何内容[/yellow]")
        else:
            console.print(f"[bold]正在清理 {', '.join(mode_desc)}...[/bold]")
        
        # 如果指定了包管理器，显示它
        if manager:
            console.print(f"使用包管理器: [blue]{manager}[/blue]")
        
        # 清理包管理器缓存
        if run_cache_clean:
            console.print("\n[bold]清理包管理器缓存:[/bold]")
            results = manager_obj.clean_caches(dry_run=dry_run, pkg_manager=manager)
            
            if not results:
                console.print("[yellow]没有找到可清理的缓存。[/yellow]")
            else:
                total_size_saved = 0
                
                for result in results:
                    pm_name = result.get("package_manager", "未知")
                    status = result.get("status", "未知")
                    message = result.get("message", "")
                    size_saved = result.get("size_saved", 0)
                    total_size_saved += size_saved
                    
                    # 根据状态显示不同颜色
                    if status == "success":
                        size_str = f" (已释放 {format_size(size_saved)})" if size_saved else ""
                        console.print(f"[green]✓ {pm_name}: 缓存清理成功{size_str}[/green]")
                    elif status == "error":
                        console.print(f"[red]✗ {pm_name}: 清理失败 - {message}[/red]")
                    elif status == "warning":
                        console.print(f"[yellow]⚠ {pm_name}: {message}[/yellow]")
                    elif status == "skipped":
                        console.print(f"[cyan]○ {pm_name}: 已跳过 - {message}[/cyan]")
                
                # 显示总节省空间
                if total_size_saved > 0:
                    console.print(f"\n总共释放了 [bold green]{format_size(total_size_saved)}[/bold green] 的磁盘空间")
        
        # 清理未使用的依赖
        if run_unused_clean:
            console.print("\n[bold]清理未使用的依赖:[/bold]")
            results = manager_obj.clean_unused_dependencies(dry_run=dry_run, pkg_manager=manager)
            
            if not results:
                console.print("[yellow]没有找到未使用的依赖。[/yellow]")
            else:
                total_removed = 0
                total_size_saved = 0
                
                for result in results:
                    pm_name = result.get("package_manager", "未知")
                    status = result.get("status", "未知")
                    message = result.get("message", "")
                    removed_packages = result.get("removed_packages", [])
                    size_saved = result.get("size_saved", 0)
                    
                    total_removed += len(removed_packages)
                    total_size_saved += size_saved
                    
                    # 根据状态显示不同颜色
                    if status == "success":
                        if removed_packages:
                            package_list = ", ".join(removed_packages)
                            size_str = f" (已释放 {format_size(size_saved)})" if size_saved else ""
                            console.print(f"[green]✓ {pm_name}: 已移除 {len(removed_packages)} 个未使用的依赖{size_str}[/green]")
                            if len(removed_packages) <= 10:  # 仅显示少量包以避免输出过多
                                console.print(f"  移除的包: {package_list}")
                            else:
                                console.print(f"  移除的包: {', '.join(removed_packages[:5])}... 等 {len(removed_packages)} 个包")
                        else:
                            console.print(f"[green]✓ {pm_name}: 没有发现未使用的依赖[/green]")
                    elif status == "error":
                        console.print(f"[red]✗ {pm_name}: 清理失败 - {message}[/red]")
                    elif status == "warning":
                        console.print(f"[yellow]⚠ {pm_name}: {message}[/yellow]")
                    elif status == "skipped":
                        console.print(f"[cyan]○ {pm_name}: 已跳过 - {message}[/cyan]")
                
                # 显示总结
                if total_removed > 0:
                    size_str = f" (已释放 {format_size(total_size_saved)})" if total_size_saved > 0 else ""
                    console.print(f"\n总共移除了 [bold green]{total_removed}[/bold green] 个未使用的依赖{size_str}")
        
        # 操作完成
        if dry_run:
            console.print("\n[bold yellow]模拟清理完成。要执行实际清理，请移除 --dry-run 选项。[/bold yellow]")
        else:
            console.print("\n[bold green]清理操作成功完成！[/bold green]")
    
    except Exception as e:
        handle_command_error(e, "clean")

if __name__ == '__main__':
    cli() 