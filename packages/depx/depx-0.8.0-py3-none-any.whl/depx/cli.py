"""
Depx Command Line Interface

Provides user-friendly command line interface with multi-language support
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .config import config_manager, get_config
from .core.analyzer import DependencyAnalyzer
from .core.cleaner import DependencyCleaner
from .core.dependency_manager import DependencyManager
from .core.exporter import AnalysisExporter
from .core.global_scanner import GlobalScanner
from .core.scanner import ProjectScanner
from .core.package_managers import SearchResult, OutdatedPackage
from .i18n import (
    auto_detect_and_set_language,
    get_language_detection_info,
    get_text,
    set_language,
)
from .parsers.base import PackageManagerType, ProjectType
from .utils.file_utils import format_size

# Set UTF-8 encoding for Windows compatibility
if sys.platform.startswith("win"):
    os.environ["PYTHONIOENCODING"] = "utf-8"

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Rich console with Windows compatibility
console = Console(
    force_terminal=True,
    legacy_windows=False,
    width=120,
)

# Auto-detect and set language
auto_detect_and_set_language()


class CustomGroup(click.Group):
    """自定义 Click Group 以支持增强的帮助信息"""

    def format_help(self, ctx, formatter):
        """格式化帮助信息"""
        try:
            # 获取当前语言
            from .i18n import get_current_language

            current_lang = get_current_language()

            # 基本帮助信息
            formatter.write_paragraph()
            formatter.write_usage(ctx.get_usage(), ctx.command_path, ctx.params)
            formatter.write_paragraph()

            # 描述
            try:
                description = get_text("cli.main.description")
                subtitle = get_text("cli.main.subtitle")
                formatter.write_paragraph()
                formatter.write(f"{description}\n\n{subtitle}")
                formatter.write_paragraph()
            except Exception:
                # 如果翻译失败，使用默认描述
                formatter.write_paragraph()
                formatter.write(
                    "Depx - Local Multi-language Dependency Manager\n\n"
                    "Unified discovery, transparent information, "
                    "space optimization, cross-platform support"
                )
                formatter.write_paragraph()

            # 选项
            self.format_options(ctx, formatter)

            # 命令
            self.format_commands(ctx, formatter)

            # 语言支持信息和示例
            try:
                epilog = get_text("cli.main.epilog")
                if epilog and epilog != "cli.main.epilog":  # 确保不是键本身
                    formatter.write_paragraph()
                    formatter.write(epilog)
                else:
                    # 使用默认的语言支持信息
                    from .utils.language_info import (
                        format_language_support_info,
                    )

                    lang_info = format_language_support_info(current_lang)
                    formatter.write_paragraph()
                    formatter.write(lang_info)
            except Exception:
                # 如果出错，显示基本的语言支持信息
                formatter.write_paragraph()
                formatter.write(
                    "🎯 SUPPORTED LANGUAGES: Node.js, Python, Java, "
                    "Go, Rust, PHP, C#"
                )
        except Exception:
            # 如果所有都失败，使用默认的帮助格式
            super().format_help(ctx, formatter)


@click.group(cls=CustomGroup)
@click.version_option(version="0.8.0")
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose output with detailed logging"
)
@click.option(
    "--lang", type=click.Choice(["en", "zh"]), help="Set interface language (en, zh)"
)
def cli(verbose: bool, lang: Optional[str]):
    """
    Depx - Local Multi-language Dependency Manager

    Unified discovery, transparent information, space optimization,
    cross-platform support
    """
    # 设置语言
    if lang:
        set_language(lang)

    # 设置日志级别
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)


@cli.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path), default=".")
@click.option(
    "--depth", "-d", default=5, help="Maximum directory depth to scan (default: 5)"
)
@click.option(
    "--type",
    "-t",
    "project_types",
    multiple=True,
    type=click.Choice([pt.value for pt in ProjectType if pt != ProjectType.UNKNOWN]),
    help="Specify project types to scan",
)
@click.option(
    "--parallel/--no-parallel",
    default=True,
    help="Enable/disable parallel processing for better performance",
)
def scan(path: Path, depth: int, project_types: tuple, parallel: bool):
    """Scan specified directory to discover projects and dependencies"""

    console.print(f"\n{get_text('messages.scanning', path=path.absolute())}")
    console.print(get_text("messages.scan_depth", depth=depth))

    if parallel:
        console.print(get_text("messages.parallel_enabled"))
    else:
        console.print(get_text("messages.parallel_disabled"))

    if project_types:
        console.print(
            get_text("messages.project_types", types=", ".join(project_types))
        )

    scanner = ProjectScanner()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(get_text("status.scanning_projects"), total=None)

        try:
            projects = scanner.scan_directory(path, depth, parallel)
        except Exception as e:
            console.print(f"[red]{get_text('messages.scan_failed', error=e)}[/red]")
            sys.exit(1)

        progress.update(task, description=get_text("success.scan_completed"))

    if not projects:
        console.print(f"\n[yellow]{get_text('messages.no_projects')}[/yellow]")
        return

    # Filter project types
    if project_types:
        filtered_types = [ProjectType(pt) for pt in project_types]
        projects = [p for p in projects if p.project_type in filtered_types]

    console.print(f"\n{get_text('messages.found_projects', count=len(projects))}")

    # Display project list
    _display_projects_table(projects)


@cli.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path), default=".")
@click.option(
    "--depth", "-d", default=5, help="Maximum directory depth to scan (default: 5)"
)
@click.option(
    "--sort-by",
    "-s",
    default="size",
    type=click.Choice(["name", "size", "type"]),
    help="Sort results by specified criteria",
)
@click.option("--limit", "-l", default=20, help="Limit number of results to display")
def analyze(path: Path, depth: int, sort_by: str, limit: int):
    """Analyze project dependencies and generate detailed report"""

    console.print(f"\n{get_text('messages.analyzing', path=path.absolute())}")

    scanner = ProjectScanner()
    analyzer = DependencyAnalyzer()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Scan projects
        scan_task = progress.add_task(get_text("status.scanning_projects"), total=None)
        projects = scanner.scan_directory(path, depth)
        progress.update(scan_task, description=get_text("success.scan_completed"))

        if not projects:
            console.print(f"\n[yellow]{get_text('messages.no_projects')}[/yellow]")
            return

        # Analyze dependencies
        analyze_task = progress.add_task(
            get_text("status.analyzing_dependencies"), total=None
        )
        report = analyzer.analyze_projects(projects)
        progress.update(
            analyze_task, description=get_text("success.analysis_completed")
        )

    # Display analysis report
    _display_analysis_report(report, sort_by, limit)


@cli.command()
@click.argument("project_path", type=click.Path(exists=True, path_type=Path))
def info(project_path: Path):
    """Display detailed information for a single project"""

    scanner = ProjectScanner()

    console.print(
        f"\n📋 Project info: [bold blue]{project_path.absolute()}[/bold blue]"
    )

    project = scanner.scan_single_project(project_path)

    if not project:
        console.print("[red]Unable to recognize project type or parsing failed[/red]")
        return

    _display_project_info(project)


@cli.command()
@click.option(
    "--type",
    "-t",
    "manager_type",
    type=click.Choice(
        [pm.value for pm in PackageManagerType if pm != PackageManagerType.UNKNOWN]
    ),
    help="Specify package manager type",
)
@click.option(
    "--sort-by",
    "-s",
    default="size",
    type=click.Choice(["name", "size", "manager"]),
    help="Sort method",
)
@click.option("--limit", "-l", default=50, help="Display limit")
def global_deps(manager_type: Optional[str], sort_by: str, limit: int):
    """Scan and display globally installed dependencies"""

    console.print("\n🌍 Scanning global dependencies...")

    scanner = GlobalScanner()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning global dependencies...", total=None)

        if manager_type:
            pm_type = PackageManagerType(manager_type)
            dependencies = scanner.scan_by_package_manager(pm_type)
        else:
            dependencies = scanner.scan_all_global_dependencies()

        progress.update(task, description="Scan completed")

    if not dependencies:
        console.print("\n[yellow]No global dependencies found[/yellow]")
        return

    # Sort
    if sort_by == "name":
        dependencies.sort(key=lambda x: x.name.lower())
    elif sort_by == "size":
        dependencies.sort(key=lambda x: x.size_bytes, reverse=True)
    elif sort_by == "manager":
        dependencies.sort(key=lambda x: x.package_manager.value)

    console.print(
        f"\n✅ Found [bold green]{len(dependencies)}[/bold green] global dependencies"
    )

    # Display detected package managers
    detected_managers = scanner.get_detected_package_managers()
    if detected_managers:
        manager_names = [pm.value for pm in detected_managers]
        console.print(f"📦 Detected package managers: {', '.join(manager_names)}")

    # Display global dependencies table
    _display_global_dependencies_table(dependencies[:limit])


def _display_projects_table(projects):
    """Display projects table"""
    table = Table(title=get_text("tables.projects.title"))

    table.add_column(get_text("tables.projects.name"), style="cyan", no_wrap=True)
    table.add_column(get_text("tables.projects.type"), style="magenta")
    table.add_column(get_text("tables.projects.path"), style="blue")
    table.add_column(
        get_text("tables.projects.dependencies"), justify="right", style="green"
    )
    table.add_column(get_text("tables.projects.size"), justify="right", style="yellow")

    for project in projects:
        table.add_row(
            project.name,
            project.project_type.value,
            str(project.path),
            str(len(project.dependencies)),
            format_size(project.total_size_bytes),
        )

    console.print(table)


def _display_analysis_report(report, sort_by: str, limit: int):
    """Display analysis report"""
    summary = report["summary"]

    # Summary panel
    summary_text = f"""
📊 Total projects: {summary['total_projects']}
📦 Total dependencies: {summary['total_dependencies']}
💾 Total space used: {summary['total_size_formatted']}
    """

    console.print(Panel(summary_text.strip(), title="📈 Summary", border_style="green"))

    # Largest dependencies table
    dep_stats = report["dependency_stats"]
    if dep_stats.largest_dependencies:
        dep_table = Table(title="🔥 Largest Dependencies by Size")
        dep_table.add_column("Dependency Name", style="cyan")
        dep_table.add_column("Size", justify="right", style="yellow")

        for name, size in dep_stats.largest_dependencies[:limit]:
            dep_table.add_row(name, format_size(size))

        console.print(dep_table)

    # Duplicate dependencies
    duplicates = report["duplicate_dependencies"]
    if duplicates["count"] > 0:
        dup_table = Table(title="🔄 Duplicate Dependencies")
        dup_table.add_column("Dependency Name", style="cyan")
        dup_table.add_column("Projects", justify="right", style="magenta")
        dup_table.add_column("Versions", justify="right", style="blue")
        dup_table.add_column("Total Size", justify="right", style="yellow")
        dup_table.add_column("Potential Savings", justify="right", style="green")

        for dup in duplicates["dependencies"][:limit]:
            dup_table.add_row(
                dup["name"],
                str(dup["project_count"]),
                str(dup["version_count"]),
                dup["total_size_formatted"],
                format_size(dup["potential_savings"]),
            )

        console.print(dup_table)

    # Cleanup suggestions
    suggestions = report["cleanup_suggestions"]
    if suggestions:
        console.print("\n💡 [bold yellow]Cleanup Suggestions[/bold yellow]")
        for suggestion in suggestions:
            console.print(f"• {suggestion['title']}: {suggestion['description']}")
            console.print(
                f"  Potential savings: {format_size(suggestion['potential_savings'])}"
            )


def _display_global_dependencies_table(dependencies):
    """Display global dependencies table"""
    table = Table(title="🌍 Global Dependencies")

    table.add_column("Dependency Name", style="cyan", no_wrap=True)
    table.add_column("Version", style="magenta")
    table.add_column("Package Manager", style="blue")
    table.add_column("Size", justify="right", style="yellow")
    table.add_column("Install Path", style="dim", max_width=50)

    for dep in dependencies:
        table.add_row(
            dep.name,
            dep.version,
            dep.package_manager.value,
            format_size(dep.size_bytes),
            str(dep.install_path) if dep.install_path != Path("unknown") else "Unknown",
        )

    console.print(table)


def _display_project_info(project):
    """Display detailed project information"""
    # Project basic info
    info_text = f"""
📁 Project name: {project.name}
🏷️  Project type: {project.project_type.value}
📍 Project path: {project.path}
⚙️  Config file: {project.config_file}
📦 Dependencies count: {len(project.dependencies)}
💾 Total size: {format_size(project.total_size_bytes)}
    """

    console.print(
        Panel(info_text.strip(), title="📋 Project Information", border_style="blue")
    )

    # Dependencies list
    if project.dependencies:
        dep_table = Table(title="📦 Dependencies List")
        dep_table.add_column("Name", style="cyan")
        dep_table.add_column("Version", style="magenta")
        dep_table.add_column("Type", style="blue")
        dep_table.add_column("Size", justify="right", style="yellow")

        for dep in project.dependencies:
            dep_table.add_row(
                dep.name,
                dep.installed_version or dep.version,
                dep.dependency_type.value,
                format_size(dep.size_bytes),
            )

        console.print(dep_table)


@cli.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path), default=".")
@click.option(
    "--type",
    "-t",
    "cleanup_types",
    multiple=True,
    type=click.Choice(["dev", "cache", "unused", "large"]),
    default=["dev", "cache"],
    help="Types of cleanup to perform",
)
@click.option(
    "--dry-run/--no-dry-run",
    default=True,
    help="Show what would be cleaned without actually doing it",
)
@click.option(
    "--confirm/--no-confirm", default=True, help="Ask for confirmation before cleaning"
)
def clean(path: Path, cleanup_types: tuple, dry_run: bool, confirm: bool):
    """Clean dependencies and caches to free up space"""

    console.print(
        f"\n🧹 Cleaning dependencies in: [bold blue]{path.absolute()}[/bold blue]"
    )
    console.print(f"🎯 Cleanup types: {', '.join(cleanup_types)}")
    console.print(f"🔍 Mode: {'Dry run' if dry_run else 'Live cleaning'}")

    # Load configuration
    config = get_config()

    # Scan projects first
    scanner = ProjectScanner()
    cleaner = DependencyCleaner(dry_run=dry_run)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        scan_task = progress.add_task("Scanning projects...", total=None)
        projects = scanner.scan_directory(path, config.scan.max_depth)
        progress.update(scan_task, description="Creating cleanup plan...")

        # Create cleanup plan
        plan = cleaner.create_cleanup_plan(projects, list(cleanup_types))
        progress.update(scan_task, description="Plan created")

    if not plan.project_dependencies and not plan.global_caches:
        console.print("\n[yellow]Nothing to clean[/yellow]")
        return

    # Display cleanup plan
    console.print("\n📋 [bold yellow]Cleanup Plan[/bold yellow]")
    console.print(
        f"💾 Total space to free: "
        f"[bold green]{format_size(plan.total_size)}[/bold green]"
    )

    if plan.project_dependencies:
        dep_table = Table(title="Project Dependencies to Clean")
        dep_table.add_column("Project", style="cyan")
        dep_table.add_column("Dependency", style="magenta")
        dep_table.add_column("Type", style="blue")
        dep_table.add_column("Size", justify="right", style="yellow")

        for item in plan.project_dependencies:
            dep_table.add_row(
                item["project"], item["name"], item["type"], format_size(item["size"])
            )

        console.print(dep_table)

    if plan.global_caches:
        cache_table = Table(title="Global Caches to Clean")
        cache_table.add_column("Cache", style="cyan")
        cache_table.add_column("Size", justify="right", style="yellow")

        for item in plan.global_caches:
            cache_table.add_row(item["name"], format_size(item["size"]))

        console.print(cache_table)

    # Confirm before cleaning
    if not dry_run and confirm:
        if not click.confirm("\nProceed with cleanup?"):
            console.print("[yellow]Cleanup cancelled[/yellow]")
            return

    # Execute cleanup
    if not dry_run:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            clean_task = progress.add_task("Cleaning...", total=None)
            result = cleaner.execute_cleanup_plan(plan)
            progress.update(clean_task, description="Cleanup completed")

        # Display results
        if result.success:
            console.print(
                "\n✅ [bold green]Cleanup completed successfully![/bold green]"
            )
            console.print(f"💾 Freed space: {format_size(result.freed_space)}")
            console.print(f"🗑️  Cleaned items: {len(result.cleaned_items)}")
        else:
            console.print(
                "\n⚠️  [bold yellow]Cleanup completed with errors[/bold yellow]"
            )
            console.print(f"💾 Freed space: {format_size(result.freed_space)}")
            console.print(f"🗑️  Cleaned items: {len(result.cleaned_items)}")
            console.print(f"❌ Errors: {len(result.errors)}")
            for error in result.errors:
                console.print(f"  • {error}")


@cli.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path), default=".")
@click.option(
    "--format",
    "-f",
    "export_format",
    type=click.Choice(["json", "csv", "html"]),
    default="json",
    help="Export format",
)
@click.option(
    "--output",
    "-o",
    "output_path",
    type=click.Path(path_type=Path),
    help="Output file path",
)
@click.option(
    "--type",
    "-t",
    "export_type",
    type=click.Choice(["projects", "dependencies", "report"]),
    default="projects",
    help="What to export",
)
def export(
    path: Path, export_format: str, output_path: Optional[Path], export_type: str
):
    """Export analysis results to various formats"""

    console.print(
        f"\n📤 Exporting {export_type} from: [bold blue]{path.absolute()}[/bold blue]"
    )
    console.print(f"📄 Format: {export_format}")

    # Generate default output path if not provided
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"depx_{export_type}_{timestamp}.{export_format}"
        output_path = Path(filename)

    scanner = ProjectScanner()
    exporter = AnalysisExporter()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        if export_type == "projects":
            scan_task = progress.add_task("Scanning projects...", total=None)
            projects = scanner.scan_directory(path, 5)
            progress.update(scan_task, description="Exporting...")

            success = exporter.export_projects(projects, output_path, export_format)

        elif export_type == "dependencies":
            scan_task = progress.add_task("Scanning global dependencies...", total=None)
            global_scanner = GlobalScanner()
            dependencies = global_scanner.scan_all_global_dependencies()
            progress.update(scan_task, description="Exporting...")

            success = exporter.export_dependencies(
                dependencies, output_path, export_format
            )

        elif export_type == "report":
            scan_task = progress.add_task("Generating analysis report...", total=None)
            projects = scanner.scan_directory(path, 5)
            analyzer = DependencyAnalyzer()
            report = analyzer.analyze_projects(projects)
            progress.update(scan_task, description="Exporting...")

            success = exporter.export_analysis_report(
                report, output_path, export_format
            )

        progress.update(scan_task, description="Export completed")

    if success:
        console.print("\n✅ [bold green]Export successful![/bold green]")
        console.print(f"📁 Output file: {output_path.absolute()}")
    else:
        console.print("\n❌ [bold red]Export failed![/bold red]")


@cli.command()
@click.argument("package_name", type=str)
@click.option(
    "--type",
    "-t",
    "project_type",
    type=click.Choice([pt.value for pt in ProjectType if pt != ProjectType.UNKNOWN]),
    help="Specify project type",
)
@click.option(
    "--package-manager",
    "-pm",
    type=click.Choice(["npm", "yarn", "pip", "cargo"]),
    help="Specify package manager to use",
)
@click.option(
    "--dev", "-D", is_flag=True, help="Install as development dependency"
)
@click.option(
    "--global", "-g", "global_install", is_flag=True, help="Install globally"
)
@click.option(
    "--dry-run", is_flag=True, help="Show what would be done without actually doing it"
)
@click.argument("path", type=click.Path(exists=True, path_type=Path), default=".")
def install(
    package_name: str,
    project_type: Optional[str],
    package_manager: Optional[str],
    dev: bool,
    global_install: bool,
    dry_run: bool,
    path: Path,
):
    """Install dependencies for projects"""

    console.print(f"\n{get_text('messages.installing_package').format(package=package_name)}")

    # 自动检测语言并设置
    auto_detect_and_set_language()

    # 创建依赖管理器
    dep_manager = DependencyManager()

    # 转换项目类型
    parsed_project_type = None
    if project_type:
        try:
            parsed_project_type = ProjectType(project_type)
        except ValueError:
            console.print(f"[red]{get_text('errors.invalid_path').format(path=project_type)}[/red]")
            return

    # 如果不是全局安装，使用项目路径
    project_path = None if global_install else path

    # 检测项目类型
    if not parsed_project_type and not global_install:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            detect_task = progress.add_task(get_text("messages.detecting_project_type"), total=None)
            parsed_project_type = dep_manager.detect_project_type(project_path)
            progress.update(detect_task, description=get_text("success.scan_completed"))

        if parsed_project_type:
            console.print(f"{get_text('messages.project_type_detected').format(type=parsed_project_type.value)}")
        else:
            console.print(f"[red]{get_text('errors.project_type_not_detected')}[/red]")
            return

    # 获取包管理器
    manager = None
    if package_manager:
        # 使用指定的包管理器
        try:
            from .parsers.base import PackageManagerType
            manager_type = PackageManagerType(package_manager.lower())
            manager_class = dep_manager.package_managers.get(manager_type)
            if manager_class:
                manager = manager_class(project_path)
        except ValueError:
            console.print(f"[red]不支持的包管理器: {package_manager}[/red]")
            return
    elif parsed_project_type:
        manager = dep_manager.detect_preferred_package_manager(project_path, parsed_project_type)
    elif global_install:
        # 全局安装时，如果没有指定包管理器，默认使用 npm
        from .core.package_managers import NPMManager
        manager = NPMManager(None)

    if manager:
        console.print(f"{get_text('messages.package_manager_detected').format(manager=manager.name)}")

    # 预览命令
    if dry_run:
        if manager and hasattr(manager, 'get_install_preview'):
            preview_cmd = manager.get_install_preview(package_name, dev=dev, global_install=global_install)
            console.print(f"\n{get_text('messages.command_preview').format(command=preview_cmd)}")
        console.print(f"[yellow]{get_text('messages.dry_run_mode')}[/yellow]")
        return

    # 确认操作
    if not click.confirm(get_text("messages.confirm_operation")):
        console.print(f"[yellow]{get_text('errors.operation_cancelled')}[/yellow]")
        return

    # 执行安装
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        install_task = progress.add_task(get_text("status.installing"), total=None)

        result = dep_manager.install_package(
            package_name=package_name,
            project_path=project_path,
            project_type=parsed_project_type,
            package_manager=package_manager,
            dev=dev,
            global_install=global_install
        )

        if result.success:
            progress.update(install_task, description=get_text("status.installing") + " - " + get_text("success.scan_completed"))
        else:
            progress.update(install_task, description="Installation failed")

    # 显示结果
    if result.success:
        console.print(f"\n{get_text('success.package_installed').format(package=package_name)}")
        if result.output:
            console.print(f"[dim]{result.output}[/dim]")
    else:
        console.print(f"\n❌ [red]Installation failed: {result.message}[/red]")
        if result.error:
            console.print(f"[dim red]{result.error}[/dim red]")


@cli.command()
@click.argument("package_name", type=str)
@click.option(
    "--type",
    "-t",
    "project_type",
    type=click.Choice([pt.value for pt in ProjectType if pt != ProjectType.UNKNOWN]),
    help="Specify project type",
)
@click.option(
    "--package-manager",
    "-pm",
    type=click.Choice(["npm", "yarn", "pip", "cargo"]),
    help="Specify package manager to use",
)
@click.option(
    "--global", "-g", "global_uninstall", is_flag=True, help="Uninstall globally"
)
@click.option(
    "--dry-run", is_flag=True, help="Show what would be done without actually doing it"
)
@click.argument("path", type=click.Path(exists=True, path_type=Path), default=".")
def uninstall(
    package_name: str,
    project_type: Optional[str],
    package_manager: Optional[str],
    global_uninstall: bool,
    dry_run: bool,
    path: Path,
):
    """Uninstall dependencies from projects"""

    console.print(f"\n{get_text('messages.uninstalling_package').format(package=package_name)}")

    # 自动检测语言并设置
    auto_detect_and_set_language()

    # 创建依赖管理器
    dep_manager = DependencyManager()

    # 转换项目类型
    parsed_project_type = None
    if project_type:
        try:
            parsed_project_type = ProjectType(project_type)
        except ValueError:
            console.print(f"[red]{get_text('errors.invalid_path').format(path=project_type)}[/red]")
            return

    # 如果不是全局卸载，使用项目路径
    project_path = None if global_uninstall else path

    # 检测项目类型
    if not parsed_project_type and not global_uninstall:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            detect_task = progress.add_task(get_text("messages.detecting_project_type"), total=None)
            parsed_project_type = dep_manager.detect_project_type(project_path)
            progress.update(detect_task, description=get_text("success.scan_completed"))

        if parsed_project_type:
            console.print(f"{get_text('messages.project_type_detected').format(type=parsed_project_type.value)}")
        else:
            console.print(f"[red]{get_text('errors.project_type_not_detected')}[/red]")
            return

    # 获取包管理器
    manager = None
    if package_manager:
        # 使用指定的包管理器
        try:
            from .parsers.base import PackageManagerType
            manager_type = PackageManagerType(package_manager.lower())
            manager_class = dep_manager.package_managers.get(manager_type)
            if manager_class:
                manager = manager_class(project_path)
        except ValueError:
            console.print(f"[red]不支持的包管理器: {package_manager}[/red]")
            return
    elif parsed_project_type:
        manager = dep_manager.detect_preferred_package_manager(project_path, parsed_project_type)
    elif global_uninstall:
        # 全局卸载时，如果没有指定包管理器，默认使用 npm
        from .core.package_managers import NPMManager
        manager = NPMManager(None)

    if manager:
        console.print(f"{get_text('messages.package_manager_detected').format(manager=manager.name)}")

    # 预览命令
    if dry_run:
        if manager and hasattr(manager, 'get_uninstall_preview'):
            preview_cmd = manager.get_uninstall_preview(package_name, global_uninstall=global_uninstall)
            console.print(f"\n{get_text('messages.command_preview').format(command=preview_cmd)}")
        console.print(f"[yellow]{get_text('messages.dry_run_mode')}[/yellow]")
        return

    # 确认操作
    if not click.confirm(get_text("messages.confirm_operation")):
        console.print(f"[yellow]{get_text('errors.operation_cancelled')}[/yellow]")
        return

    # 执行卸载
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        uninstall_task = progress.add_task(get_text("status.uninstalling"), total=None)

        result = dep_manager.uninstall_package(
            package_name=package_name,
            project_path=project_path,
            project_type=parsed_project_type,
            package_manager=package_manager,
            global_uninstall=global_uninstall
        )

        if result.success:
            progress.update(uninstall_task, description=get_text("status.uninstalling") + " - " + get_text("success.scan_completed"))
        else:
            progress.update(uninstall_task, description="Uninstallation failed")

    # 显示结果
    if result.success:
        console.print(f"\n{get_text('success.package_uninstalled').format(package=package_name)}")
        if result.output:
            console.print(f"[dim]{result.output}[/dim]")
    else:
        console.print(f"\n❌ [red]Uninstallation failed: {result.message}[/red]")
        if result.error:
            console.print(f"[dim red]{result.error}[/dim red]")


@cli.command()
@click.argument("package_name", type=str)
@click.option(
    "--type",
    "-t",
    "project_type",
    type=click.Choice([pt.value for pt in ProjectType if pt != ProjectType.UNKNOWN]),
    help="Specify project type",
)
@click.option(
    "--package-manager",
    "-pm",
    type=click.Choice(["npm", "yarn", "pip", "cargo"]),
    help="Specify package manager to use",
)
@click.option(
    "--limit", "-l", default=10, help="Limit number of search results"
)
@click.option(
    "--all", "-a", is_flag=True, help="Search in all available package managers"
)
@click.argument("path", type=click.Path(exists=True, path_type=Path), default=".")
def search(
    package_name: str,
    project_type: Optional[str],
    package_manager: Optional[str],
    limit: int,
    all: bool,
    path: Path,
):
    """Search for packages"""

    console.print(f"\n🔍 Searching for: {package_name}")

    # 自动检测语言并设置
    auto_detect_and_set_language()

    # 创建依赖管理器
    dep_manager = DependencyManager()

    # 转换项目类型
    parsed_project_type = None
    if project_type:
        try:
            parsed_project_type = ProjectType(project_type)
        except ValueError:
            console.print(f"[red]Invalid project type: {project_type}[/red]")
            return

    # 执行搜索
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        search_task = progress.add_task("Searching packages...", total=None)

        results = dep_manager.search_package(
            package_name=package_name,
            project_path=path,
            project_type=parsed_project_type,
            package_manager=package_manager,
            limit=limit,
            search_all=all
        )

        progress.update(search_task, description="Search completed")

    # 显示结果
    if not results:
        console.print(f"[yellow]No packages found for '{package_name}'[/yellow]")
        return

    console.print(f"\n📦 Found {len(results)} package(s):")

    # 创建搜索结果表格
    table = Table(title=f"Search Results for '{package_name}'")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Version", style="green")
    table.add_column("Description", style="white")
    table.add_column("Author", style="yellow")
    table.add_column("Downloads", style="magenta")
    table.add_column("Package Manager", style="blue", no_wrap=True)

    for result in results:
        table.add_row(
            result.name,
            result.version,
            result.description[:50] + "..." if len(result.description) > 50 else result.description,
            result.author,
            result.downloads,
            result.package_manager
        )

    console.print(table)

    # 显示详细信息（如果只有一个结果）
    if len(results) == 1:
        result = results[0]
        console.print(f"\n📋 Package Details:")
        details = [
            f"• Name: {result.name}",
            f"• Version: {result.version}",
            f"• Description: {result.description}",
            f"• Author: {result.author}",
            f"• Package Manager: {result.package_manager}",
            f"• Homepage: {result.homepage}",
            f"• Repository: {result.repository}",
            f"• License: {result.license}",
        ]
        for detail in details:
            if detail.split(": ", 1)[1]:  # 只显示有值的字段
                console.print(detail)


@cli.command()
@click.argument("package_name", type=str, required=False)
@click.option(
    "--type",
    "-t",
    "project_type",
    type=click.Choice([pt.value for pt in ProjectType if pt != ProjectType.UNKNOWN]),
    help="Specify project type",
)
@click.option(
    "--package-manager",
    "-pm",
    type=click.Choice(["npm", "yarn", "pip", "cargo"]),
    help="Specify package manager to use",
)
@click.option(
    "--check", "-c", is_flag=True, help="Only check for outdated packages, don't update"
)
@click.option(
    "--dry-run", is_flag=True, help="Show what would be done without actually doing it"
)
@click.option(
    "--dev", "-D", is_flag=True, help="Include development dependencies"
)
@click.argument("path", type=click.Path(exists=True, path_type=Path), default=".")
def update(
    package_name: Optional[str],
    project_type: Optional[str],
    package_manager: Optional[str],
    check: bool,
    dry_run: bool,
    dev: bool,
    path: Path,
):
    """Update packages"""

    if package_name:
        console.print(f"\n🔄 Updating package: {package_name}")
    else:
        console.print(f"\n🔄 Checking for outdated packages...")

    # 自动检测语言并设置
    auto_detect_and_set_language()

    # 创建依赖管理器
    dep_manager = DependencyManager()

    # 转换项目类型
    parsed_project_type = None
    if project_type:
        try:
            parsed_project_type = ProjectType(project_type)
        except ValueError:
            console.print(f"[red]Invalid project type: {project_type}[/red]")
            return

    # 检测项目类型
    if not parsed_project_type:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            detect_task = progress.add_task("Detecting project type...", total=None)
            parsed_project_type = dep_manager.detect_project_type(path)
            progress.update(detect_task, description="Detection completed")

        if parsed_project_type:
            console.print(f"✅ Detected project type: {parsed_project_type.value}")
        else:
            console.print(f"[red]Could not detect project type. Please use --type to specify.[/red]")
            return

    # 检查过时的包
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        check_task = progress.add_task("Checking for outdated packages...", total=None)

        outdated_packages = dep_manager.check_outdated_packages(
            project_path=path,
            project_type=parsed_project_type,
            package_manager=package_manager
        )

        progress.update(check_task, description="Check completed")

    if not outdated_packages:
        console.print("✅ All packages are up to date!")
        return

    # 过滤特定包（如果指定了）
    if package_name:
        outdated_packages = [p for p in outdated_packages if p.name == package_name]
        if not outdated_packages:
            console.print(f"✅ Package '{package_name}' is already up to date!")
            return

    # 显示过时的包
    console.print(f"\n📋 Found {len(outdated_packages)} outdated package(s):")

    table = Table(title="Outdated Packages")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Current", style="yellow")
    table.add_column("Latest", style="green")
    table.add_column("Type", style="blue")

    for pkg in outdated_packages:
        table.add_row(
            pkg.name,
            pkg.current_version,
            pkg.latest_version,
            pkg.package_type
        )

    console.print(table)

    # 如果只是检查，不执行更新
    if check:
        return

    # 预览模式
    if dry_run:
        console.print(f"\n[yellow]Dry run mode - no packages will be updated[/yellow]")
        return

    # 确认更新
    if not click.confirm("Do you want to update these packages?"):
        console.print("[yellow]Update cancelled[/yellow]")
        return

    # 执行更新
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        update_task = progress.add_task("Updating packages...", total=None)

        result = dep_manager.update_packages(
            package_name=package_name,
            project_path=path,
            project_type=parsed_project_type,
            package_manager=package_manager,
            dev=dev
        )

        progress.update(update_task, description="Update completed")

    # 显示结果
    if result.success:
        console.print(f"\n✅ Update completed successfully!")
        if result.updated_packages:
            console.print(f"Updated {len(result.updated_packages)} package(s)")
        if result.output:
            console.print(f"[dim]{result.output}[/dim]")
    else:
        console.print(f"\n❌ [red]Update failed: {result.message}[/red]")
        if result.error:
            console.print(f"[dim red]{result.error}[/dim red]")


@cli.command()
@click.option("--create", is_flag=True, help="Create a default configuration file")
@click.option(
    "--path",
    "-p",
    "config_path",
    type=click.Path(path_type=Path),
    help="Configuration file path",
)
@click.option("--show", is_flag=True, help="Show current configuration")
@click.option("--lang-info", is_flag=True, help="Show language detection information")
def config(create: bool, config_path: Optional[Path], show: bool, lang_info: bool):
    """Manage Depx configuration"""

    if create:
        if not config_path:
            config_path = Path(".depx.yaml")

        if config_manager.create_default_config(config_path):
            console.print(f"✅ Created default configuration: {config_path}")
        else:
            console.print("❌ Failed to create configuration file")
        return

    if show:
        # Load and display current configuration
        current_config = config_manager.load_config(config_path)

        console.print("\n⚙️  [bold blue]Current Configuration[/bold blue]")

        # Scan settings
        scan_table = Table(title="Scan Settings")
        scan_table.add_column("Setting", style="cyan")
        scan_table.add_column("Value", style="yellow")

        scan_table.add_row("Max Depth", str(current_config.scan.max_depth))
        scan_table.add_row("Parallel", str(current_config.scan.parallel))
        scan_table.add_row(
            "Project Types", ", ".join(current_config.scan.project_types) or "All"
        )
        scan_table.add_row("Follow Symlinks", str(current_config.scan.follow_symlinks))

        console.print(scan_table)

        # Cleanup settings
        cleanup_table = Table(title="Cleanup Settings")
        cleanup_table.add_column("Setting", style="cyan")
        cleanup_table.add_column("Value", style="yellow")

        cleanup_table.add_row("Dry Run", str(current_config.cleanup.dry_run))
        cleanup_table.add_row(
            "Backup Before Clean", str(current_config.cleanup.backup_before_clean)
        )
        cleanup_table.add_row(
            "Cleanup Types", ", ".join(current_config.cleanup.cleanup_types)
        )
        cleanup_table.add_row(
            "Size Threshold (MB)", str(current_config.cleanup.size_threshold_mb)
        )

        console.print(cleanup_table)

        # Global settings
        global_table = Table(title="Global Settings")
        global_table.add_column("Setting", style="cyan")
        global_table.add_column("Value", style="yellow")

        global_table.add_row("Log Level", current_config.log_level)
        global_table.add_row("Cache Enabled", str(current_config.cache_enabled))
        global_table.add_row("Cache Directory", current_config.cache_directory)

        console.print(global_table)

        return

    if lang_info:
        # Display language detection information
        console.print("\n🌍 [bold blue]Language Detection Information[/bold blue]")

        detection_info = get_language_detection_info()

        # Environment variables table
        env_table = Table(title="Environment Variables")
        env_table.add_column("Variable", style="cyan")
        env_table.add_column("Value", style="yellow")

        env_table.add_row("DEPX_LANG", detection_info["DEPX_LANG"])
        env_table.add_row("LANG", detection_info["LANG"])
        env_table.add_row("LC_ALL", detection_info["LC_ALL"])

        console.print(env_table)

        # System information table
        sys_table = Table(title="System Information")
        sys_table.add_column("Item", style="cyan")
        sys_table.add_column("Value", style="yellow")

        sys_table.add_row("System Locale", detection_info["system_locale"])
        sys_table.add_row("Detected Language", detection_info["detected_language"])
        sys_table.add_row("Current Language", detection_info["current_language"])

        console.print(sys_table)

        # Terminal locale information
        if (
            "terminal_locale" in detection_info
            and detection_info["terminal_locale"] != "检测失败"
        ):
            console.print("\n📟 [bold green]Terminal Locale Information:[/bold green]")
            console.print(
                Panel(detection_info["terminal_locale"], border_style="green")
            )

        # Usage tips
        console.print("\n💡 [bold yellow]Usage Tips:[/bold yellow]")
        tips = [
            "• Use 'depx --lang zh' to force Chinese interface",
            "• Use 'depx --lang en' to force English interface",
            "• Set 'export DEPX_LANG=zh' for default Chinese",
            "• Set 'export DEPX_LANG=en' for default English",
            "• Language is auto-detected from system locale if not specified",
        ]
        for tip in tips:
            console.print(tip)

        return

    # Load configuration
    config_manager.load_config(config_path)
    console.print("✅ Configuration loaded")


def main():
    """Main entry function"""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error occurred: {e}[/red]")
        if logger.isEnabledFor(logging.DEBUG):
            import traceback

            console.print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
