#!/usr/bin/env python3
"""
DepMan - A universal dependency manager CLI.
"""
import sys
from pathlib import Path

import click
import colorama

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
        if package:
            click.echo(f"Installing package: {package}" + (" (project)" if project else " (global)"))
            
            # Use specified package manager if provided
            if manager:
                click.echo(f"Using package manager: {manager}")
                manager_obj.install(package, project=project, pkg_manager=manager)
            else:
                manager_obj.install(package, project=project)
                
        elif file:
            click.echo(f"Installing dependencies from file: {file}")
            manager_obj.install_from_file(file)
        elif project:
            click.echo("Installing all project dependencies")
            manager_obj.install_all_project_dependencies()
        else:
            click.echo("Error: Please specify a package name or use --project to install all project dependencies")
            sys.exit(1)
            
        click.echo(click.style("Installation completed successfully.", fg="green"))
    except Exception as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        sys.exit(1)


@cli.command()
@click.argument('package')
@click.option('--project', is_flag=True, help='Uninstall from the current project instead of globally.')
@click.pass_context
def uninstall(ctx, package, project):
    """Uninstall a package."""
    manager = ctx.obj['manager']
    
    try:
        click.echo(f"Uninstalling package: {package}" + (" (project)" if project else " (global)"))
        manager.uninstall(package, project=project)
        click.echo(click.style("Uninstallation completed successfully.", fg="green"))
    except Exception as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        sys.exit(1)


@cli.command()
@click.argument('package', required=False)
@click.option('--project', is_flag=True, help='Upgrade in the current project instead of globally.')
@click.option('--all', 'upgrade_all', is_flag=True, help='Upgrade all packages.')
@click.pass_context
def upgrade(ctx, package, project, upgrade_all):
    """Upgrade a package or all packages."""
    manager = ctx.obj['manager']
    
    try:
        if upgrade_all:
            click.echo(f"Upgrading all packages" + (" (project)" if project else " (global)"))
            manager.upgrade_all(project=project)
        elif package:
            click.echo(f"Upgrading package: {package}" + (" (project)" if project else " (global)"))
            manager.upgrade(package, project=project)
        else:
            click.echo("Error: Please specify a package name or use --all to upgrade all packages")
            sys.exit(1)
            
        click.echo(click.style("Upgrade completed successfully.", fg="green"))
    except Exception as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        sys.exit(1)


@cli.command()
@click.option('--global', 'global_scan', is_flag=True, help='Scan global dependencies.')
@click.option('--security', is_flag=True, help='Perform security vulnerability scan.')
@click.pass_context
def scan(ctx, global_scan, security):
    """Scan for dependencies in the current project or globally."""
    manager = ctx.obj['manager']
    
    try:
        if global_scan:
            click.echo("Scanning global dependencies")
            results = manager.scan_global(security=security)
        else:
            click.echo("Scanning project dependencies")
            results = manager.scan_project(Path.cwd(), security=security)
            
        # Display results
        if results:
            click.echo("\nScan Results:")
            for result in results:
                click.echo(f" - {result}")
        else:
            click.echo("No dependencies found.")
            
    except Exception as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        sys.exit(1)


@cli.command()
@click.argument('package')
@click.pass_context
def path(ctx, package):
    """Show the installation path of a package."""
    manager = ctx.obj['manager']
    
    try:
        path = manager.get_package_path(package)
        if path:
            click.echo(f"Package '{package}' is installed at: {path}")
        else:
            click.echo(f"Package '{package}' not found.")
            sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        sys.exit(1)


@cli.command()
@click.option('--project', is_flag=True, help='List project dependencies.')
@click.option('--global', 'global_deps', is_flag=True, help='List global dependencies.')
@click.pass_context
def list(ctx, project, global_deps):
    """List installed dependencies."""
    manager = ctx.obj['manager']
    
    try:
        if not project and not global_deps:
            # Default to project dependencies if no flag is specified
            project = True
            
        if project:
            click.echo("Project Dependencies:")
            deps = manager.list_project_dependencies()
        else:
            click.echo("Global Dependencies:")
            deps = manager.list_global_dependencies()
            
        if deps:
            for dep in deps:
                click.echo(f" - {dep['name']} ({dep['version']})")
        else:
            click.echo("No dependencies found.")
            
    except Exception as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        sys.exit(1)


@cli.command()
@click.option('--project', is_flag=True, help='Show project dependency tree.')
@click.pass_context
def tree(ctx, project):
    """Show dependency tree."""
    manager = ctx.obj['manager']
    
    try:
        if project:
            click.echo("Project Dependency Tree:")
            tree_data = manager.get_project_dependency_tree()
        else:
            click.echo("Error: Currently only project dependency trees are supported.")
            sys.exit(1)
            
        if tree_data:
            for line in tree_data:
                click.echo(line)
        else:
            click.echo("No dependencies found.")
            
    except Exception as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        sys.exit(1)


@cli.command()
@click.argument('keyword')
@click.pass_context
def search(ctx, keyword):
    """Search for packages."""
    manager = ctx.obj['manager']
    
    try:
        click.echo(f"Searching for packages matching: {keyword}")
        results = manager.search_packages(keyword)
        
        if results:
            click.echo("\nSearch Results:")
            for result in results:
                pm_name = result.get('package_manager', 'unknown')
                click.echo(f" - {result['name']} ({pm_name}): {result['description']}")
        else:
            click.echo("No matching packages found.")
            
    except Exception as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli() 