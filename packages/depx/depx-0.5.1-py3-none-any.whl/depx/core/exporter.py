"""
Export functionality for analysis results

Support multiple export formats: JSON, CSV, HTML
"""

import csv
import json
import logging
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..parsers.base import DependencyInfo, GlobalDependencyInfo, ProjectInfo
from ..utils.file_utils import format_size

logger = logging.getLogger(__name__)


class AnalysisExporter:
    """Export analysis results to various formats"""

    def __init__(self):
        self.timestamp = datetime.now().isoformat()

    def export_projects(
        self, projects: List[ProjectInfo], output_path: Path, format: str = "json"
    ) -> bool:
        """
        Export project analysis results

        Args:
            projects: List of projects to export
            output_path: Output file path
            format: Export format ('json', 'csv', 'html')

        Returns:
            True if export successful
        """
        try:
            if format.lower() == "json":
                return self._export_projects_json(projects, output_path)
            elif format.lower() == "csv":
                return self._export_projects_csv(projects, output_path)
            elif format.lower() == "html":
                return self._export_projects_html(projects, output_path)
            else:
                logger.error(f"Unsupported export format: {format}")
                return False
        except Exception as e:
            logger.error(f"Failed to export projects: {e}")
            return False

    def export_dependencies(
        self,
        dependencies: List[GlobalDependencyInfo],
        output_path: Path,
        format: str = "json",
    ) -> bool:
        """
        Export global dependencies analysis

        Args:
            dependencies: List of global dependencies
            output_path: Output file path
            format: Export format ('json', 'csv', 'html')

        Returns:
            True if export successful
        """
        try:
            if format.lower() == "json":
                return self._export_dependencies_json(dependencies, output_path)
            elif format.lower() == "csv":
                return self._export_dependencies_csv(dependencies, output_path)
            elif format.lower() == "html":
                return self._export_dependencies_html(dependencies, output_path)
            else:
                logger.error(f"Unsupported export format: {format}")
                return False
        except Exception as e:
            logger.error(f"Failed to export dependencies: {e}")
            return False

    def export_analysis_report(
        self, report: Dict[str, Any], output_path: Path, format: str = "json"
    ) -> bool:
        """
        Export complete analysis report

        Args:
            report: Analysis report from DependencyAnalyzer
            output_path: Output file path
            format: Export format ('json', 'html')

        Returns:
            True if export successful
        """
        try:
            if format.lower() == "json":
                return self._export_report_json(report, output_path)
            elif format.lower() == "html":
                return self._export_report_html(report, output_path)
            else:
                logger.error(f"Unsupported export format for reports: {format}")
                return False
        except Exception as e:
            logger.error(f"Failed to export analysis report: {e}")
            return False

    def _export_projects_json(
        self, projects: List[ProjectInfo], output_path: Path
    ) -> bool:
        """Export projects to JSON format"""
        data = {
            "export_info": {
                "timestamp": self.timestamp,
                "format": "json",
                "type": "projects",
                "count": len(projects),
            },
            "projects": [],
        }

        for project in projects:
            project_data = {
                "name": project.name,
                "path": str(project.path),
                "project_type": project.project_type.value,
                "config_file": (
                    str(project.config_file) if project.config_file else None
                ),
                "total_size_bytes": project.total_size_bytes,
                "total_size_formatted": format_size(project.total_size_bytes),
                "metadata": project.metadata,
                "dependencies": [],
            }

            for dep in project.dependencies:
                dep_data = {
                    "name": dep.name,
                    "version": dep.version,
                    "installed_version": dep.installed_version,
                    "dependency_type": dep.dependency_type.value,
                    "size_bytes": dep.size_bytes,
                    "size_formatted": format_size(dep.size_bytes),
                    "install_path": str(dep.install_path) if dep.install_path else None,
                }
                project_data["dependencies"].append(dep_data)

            data["projects"].append(project_data)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Exported {len(projects)} projects to {output_path}")
        return True

    def _export_projects_csv(
        self, projects: List[ProjectInfo], output_path: Path
    ) -> bool:
        """Export projects to CSV format"""
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow(
                [
                    "Project Name",
                    "Project Type",
                    "Path",
                    "Config File",
                    "Total Dependencies",
                    "Total Size (Bytes)",
                    "Total Size (Formatted)",
                ]
            )

            # Write project data
            for project in projects:
                writer.writerow(
                    [
                        project.name,
                        project.project_type.value,
                        str(project.path),
                        str(project.config_file) if project.config_file else "",
                        len(project.dependencies),
                        project.total_size_bytes,
                        format_size(project.total_size_bytes),
                    ]
                )

        logger.info(f"Exported {len(projects)} projects to {output_path}")
        return True

    def _export_projects_html(
        self, projects: List[ProjectInfo], output_path: Path
    ) -> bool:
        """Export projects to HTML format"""
        html_content = self._generate_projects_html(projects)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"Exported {len(projects)} projects to {output_path}")
        return True

    def _export_dependencies_json(
        self, dependencies: List[GlobalDependencyInfo], output_path: Path
    ) -> bool:
        """Export global dependencies to JSON format"""
        data = {
            "export_info": {
                "timestamp": self.timestamp,
                "format": "json",
                "type": "global_dependencies",
                "count": len(dependencies),
            },
            "dependencies": [],
        }

        for dep in dependencies:
            dep_data = {
                "name": dep.name,
                "version": dep.version,
                "package_manager": dep.package_manager.value,
                "size_bytes": dep.size_bytes,
                "size_formatted": format_size(dep.size_bytes),
                "install_path": str(dep.install_path) if dep.install_path else None,
            }
            data["dependencies"].append(dep_data)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(
            f"Exported {len(dependencies)} global dependencies to {output_path}"
        )
        return True

    def _export_dependencies_csv(
        self, dependencies: List[GlobalDependencyInfo], output_path: Path
    ) -> bool:
        """Export global dependencies to CSV format"""
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow(
                [
                    "Name",
                    "Version",
                    "Package Manager",
                    "Size (Bytes)",
                    "Size (Formatted)",
                    "Install Path",
                ]
            )

            # Write dependency data
            for dep in dependencies:
                writer.writerow(
                    [
                        dep.name,
                        dep.version,
                        dep.package_manager.value,
                        dep.size_bytes,
                        format_size(dep.size_bytes),
                        str(dep.install_path) if dep.install_path else "",
                    ]
                )

        logger.info(
            f"Exported {len(dependencies)} global dependencies to {output_path}"
        )
        return True

    def _export_dependencies_html(
        self, dependencies: List[GlobalDependencyInfo], output_path: Path
    ) -> bool:
        """Export global dependencies to HTML format"""
        html_content = self._generate_dependencies_html(dependencies)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(
            f"Exported {len(dependencies)} global dependencies to {output_path}"
        )
        return True

    def _export_report_json(self, report: Dict[str, Any], output_path: Path) -> bool:
        """Export analysis report to JSON format"""
        data = {
            "export_info": {
                "timestamp": self.timestamp,
                "format": "json",
                "type": "analysis_report",
            },
            "report": report,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Exported analysis report to {output_path}")
        return True

    def _export_report_html(self, report: Dict[str, Any], output_path: Path) -> bool:
        """Export analysis report to HTML format"""
        html_content = self._generate_report_html(report)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"Exported analysis report to {output_path}")
        return True

    def _generate_projects_html(self, projects: List[ProjectInfo]) -> str:
        """Generate HTML content for projects"""
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Depx Projects Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .summary {{ background-color: #f9f9f9; padding: 15px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <h1>Depx Projects Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Generated:</strong> {self.timestamp}</p>
        <p><strong>Total Projects:</strong> {len(projects)}</p>
        <p><strong>Total Size:</strong> {format_size(sum(p.total_size_bytes for p in projects))}</p>
    </div>
    
    <h2>Projects</h2>
    <table>
        <thead>
            <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Path</th>
                <th>Dependencies</th>
                <th>Size</th>
            </tr>
        </thead>
        <tbody>
"""

        for project in projects:
            html += f"""
            <tr>
                <td>{project.name}</td>
                <td>{project.project_type.value}</td>
                <td>{project.path}</td>
                <td>{len(project.dependencies)}</td>
                <td>{format_size(project.total_size_bytes)}</td>
            </tr>
"""

        html += """
        </tbody>
    </table>
</body>
</html>
"""
        return html

    def _generate_dependencies_html(
        self, dependencies: List[GlobalDependencyInfo]
    ) -> str:
        """Generate HTML content for global dependencies"""
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Depx Global Dependencies Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .summary {{ background-color: #f9f9f9; padding: 15px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <h1>Depx Global Dependencies Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Generated:</strong> {self.timestamp}</p>
        <p><strong>Total Dependencies:</strong> {len(dependencies)}</p>
        <p><strong>Total Size:</strong> {format_size(sum(d.size_bytes for d in dependencies))}</p>
    </div>
    
    <h2>Global Dependencies</h2>
    <table>
        <thead>
            <tr>
                <th>Name</th>
                <th>Version</th>
                <th>Package Manager</th>
                <th>Size</th>
                <th>Install Path</th>
            </tr>
        </thead>
        <tbody>
"""

        for dep in dependencies:
            html += f"""
            <tr>
                <td>{dep.name}</td>
                <td>{dep.version}</td>
                <td>{dep.package_manager.value}</td>
                <td>{format_size(dep.size_bytes)}</td>
                <td>{dep.install_path if dep.install_path else 'Unknown'}</td>
            </tr>
"""

        html += """
        </tbody>
    </table>
</body>
</html>
"""
        return html

    def _generate_report_html(self, report: Dict[str, Any]) -> str:
        """Generate HTML content for analysis report"""
        summary = report.get("summary", {})

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Depx Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .summary {{ background-color: #f9f9f9; padding: 15px; margin-bottom: 20px; }}
        .section {{ margin-bottom: 30px; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>Depx Analysis Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Generated:</strong> {self.timestamp}</p>
        <p><strong>Total Projects:</strong> {summary.get('total_projects', 0)}</p>
        <p><strong>Total Dependencies:</strong> {summary.get('total_dependencies', 0)}</p>
        <p><strong>Total Size:</strong> {summary.get('total_size_formatted', 'Unknown')}</p>
    </div>
    
    <div class="section">
        <h2>Largest Dependencies</h2>
        <table>
            <thead>
                <tr><th>Name</th><th>Size</th></tr>
            </thead>
            <tbody>
"""

        dep_stats = report.get("dependency_stats", {})
        largest_deps = dep_stats.get("largest_dependencies", [])

        for name, size in largest_deps[:10]:  # Top 10
            html += f"<tr><td>{name}</td><td>{format_size(size)}</td></tr>"

        html += """
            </tbody>
        </table>
    </div>
</body>
</html>
"""
        return html
