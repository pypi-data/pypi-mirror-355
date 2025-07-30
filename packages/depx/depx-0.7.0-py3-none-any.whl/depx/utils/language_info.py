"""
编程语言支持信息模块

提供支持的编程语言详细信息
"""

from dataclasses import dataclass
from typing import Dict, List

from ..parsers.base import ProjectType


@dataclass
class LanguageInfo:
    """编程语言信息"""

    name: str  # 语言名称
    project_type: ProjectType  # 项目类型
    config_files: List[str]  # 配置文件
    package_managers: List[str]  # 包管理器
    dependency_dirs: List[str]  # 依赖目录
    description: str  # 描述
    status: str  # 支持状态 (stable, beta, planned)


# 支持的语言信息
SUPPORTED_LANGUAGES: Dict[ProjectType, LanguageInfo] = {
    ProjectType.NODEJS: LanguageInfo(
        name="Node.js",
        project_type=ProjectType.NODEJS,
        config_files=[
            "package.json",
            "package-lock.json",
            "yarn.lock",
            "pnpm-lock.yaml",
        ],
        package_managers=["npm", "yarn", "pnpm"],
        dependency_dirs=["node_modules"],
        description="JavaScript/TypeScript runtime environment",
        status="stable",
    ),
    ProjectType.PYTHON: LanguageInfo(
        name="Python",
        project_type=ProjectType.PYTHON,
        config_files=[
            "requirements.txt",
            "setup.py",
            "pyproject.toml",
            "Pipfile",
            "Pipfile.lock",
        ],
        package_managers=["pip", "pipenv", "poetry", "conda"],
        dependency_dirs=["venv", ".venv", "env", "__pycache__"],
        description="High-level programming language",
        status="stable",
    ),
    ProjectType.JAVA: LanguageInfo(
        name="Java",
        project_type=ProjectType.JAVA,
        config_files=[
            "pom.xml",
            "build.gradle",
            "build.gradle.kts",
            "gradle.properties",
        ],
        package_managers=["Maven", "Gradle"],
        dependency_dirs=["target", "build", ".gradle"],
        description="Object-oriented programming language",
        status="stable",
    ),
    ProjectType.GO: LanguageInfo(
        name="Go",
        project_type=ProjectType.GO,
        config_files=["go.mod", "go.sum", "Gopkg.toml", "Gopkg.lock"],
        package_managers=["go modules", "dep"],
        dependency_dirs=["vendor"],
        description="Statically typed compiled language",
        status="stable",
    ),
    ProjectType.RUST: LanguageInfo(
        name="Rust",
        project_type=ProjectType.RUST,
        config_files=["Cargo.toml", "Cargo.lock"],
        package_managers=["Cargo"],
        dependency_dirs=["target"],
        description="Systems programming language",
        status="stable",
    ),
    ProjectType.PHP: LanguageInfo(
        name="PHP",
        project_type=ProjectType.PHP,
        config_files=["composer.json", "composer.lock"],
        package_managers=["Composer"],
        dependency_dirs=["vendor"],
        description="Server-side scripting language",
        status="stable",
    ),
    ProjectType.CSHARP: LanguageInfo(
        name="C#",
        project_type=ProjectType.CSHARP,
        config_files=[
            ".csproj",
            "packages.config",
            "project.json",
            "Directory.Build.props",
        ],
        package_managers=["NuGet", "dotnet"],
        dependency_dirs=["packages", "bin", "obj"],
        description="Object-oriented programming language",
        status="stable",
    ),
}


# 计划支持的语言
PLANNED_LANGUAGES = [
    LanguageInfo(
        name="Ruby",
        project_type=ProjectType.UNKNOWN,  # 暂时使用 UNKNOWN
        config_files=["Gemfile", "Gemfile.lock"],
        package_managers=["Bundler", "gem"],
        dependency_dirs=["vendor/bundle"],
        description="Dynamic programming language",
        status="planned",
    ),
    LanguageInfo(
        name="Swift",
        project_type=ProjectType.UNKNOWN,
        config_files=["Package.swift"],
        package_managers=["Swift Package Manager"],
        dependency_dirs=[".build"],
        description="Apple's programming language",
        status="planned",
    ),
    LanguageInfo(
        name="Dart",
        project_type=ProjectType.UNKNOWN,
        config_files=["pubspec.yaml", "pubspec.lock"],
        package_managers=["pub"],
        dependency_dirs=[".dart_tool", "build"],
        description="Client-optimized language",
        status="planned",
    ),
    LanguageInfo(
        name="Scala",
        project_type=ProjectType.UNKNOWN,
        config_files=["build.sbt", "project/build.properties"],
        package_managers=["sbt"],
        dependency_dirs=["target", "project/target"],
        description="Functional and object-oriented language",
        status="planned",
    ),
]


def get_supported_languages() -> Dict[ProjectType, LanguageInfo]:
    """获取支持的语言信息"""
    return SUPPORTED_LANGUAGES.copy()


def get_language_info(project_type: ProjectType) -> LanguageInfo:
    """获取特定语言的信息"""
    return SUPPORTED_LANGUAGES.get(project_type)


def get_all_config_files() -> List[str]:
    """获取所有支持的配置文件"""
    config_files = []
    for lang_info in SUPPORTED_LANGUAGES.values():
        config_files.extend(lang_info.config_files)
    return sorted(set(config_files))


def get_all_package_managers() -> List[str]:
    """获取所有支持的包管理器"""
    managers = []
    for lang_info in SUPPORTED_LANGUAGES.values():
        managers.extend(lang_info.package_managers)
    return sorted(set(managers))


def format_language_support_info(language: str = "en") -> str:
    """
    格式化语言支持信息

    Args:
        language: 显示语言 (en, zh)

    Returns:
        格式化的语言支持信息
    """
    if language == "zh":
        header = "🎯 支持的编程语言："
        planned_header = "\n🚧 计划支持的语言："
    else:
        header = "🎯 SUPPORTED LANGUAGES:"
        planned_header = "\n🚧 PLANNED LANGUAGES:"

    lines = [header]

    # 当前支持的语言
    for lang_info in SUPPORTED_LANGUAGES.values():
        config_str = ", ".join(lang_info.config_files[:2])  # 只显示前两个
        if len(lang_info.config_files) > 2:
            config_str += ", ..."

        managers_str = ", ".join(lang_info.package_managers)
        lines.append(f"• {lang_info.name:<10} - {config_str} ({managers_str})")

    # 计划支持的语言
    lines.append(planned_header)
    for lang_info in PLANNED_LANGUAGES:
        config_str = ", ".join(lang_info.config_files)
        managers_str = ", ".join(lang_info.package_managers)
        lines.append(f"• {lang_info.name:<10} - {config_str} ({managers_str})")

    return "\n".join(lines)


def get_language_statistics() -> Dict[str, int]:
    """获取语言支持统计信息"""
    return {
        "supported_languages": len(SUPPORTED_LANGUAGES),
        "planned_languages": len(PLANNED_LANGUAGES),
        "total_config_files": len(get_all_config_files()),
        "total_package_managers": len(get_all_package_managers()),
    }
