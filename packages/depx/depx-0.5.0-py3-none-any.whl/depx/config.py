"""
Configuration management for Depx

Support for YAML configuration files with custom scan rules
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class ScanConfig:
    """Scan configuration"""

    max_depth: int = 5
    parallel: bool = True
    include_patterns: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)
    project_types: List[str] = field(default_factory=list)
    follow_symlinks: bool = False


@dataclass
class CleanupConfig:
    """Cleanup configuration"""

    dry_run: bool = True
    backup_before_clean: bool = True
    cleanup_types: List[str] = field(default_factory=lambda: ["dev", "cache"])
    size_threshold_mb: int = 50
    confirm_before_clean: bool = True


@dataclass
class ExportConfig:
    """Export configuration"""

    default_format: str = "json"
    output_directory: str = "./depx-exports"
    include_metadata: bool = True
    compress_output: bool = False


@dataclass
class DepxConfig:
    """Main Depx configuration"""

    scan: ScanConfig = field(default_factory=ScanConfig)
    cleanup: CleanupConfig = field(default_factory=CleanupConfig)
    export: ExportConfig = field(default_factory=ExportConfig)

    # Global settings
    log_level: str = "INFO"
    cache_enabled: bool = True
    cache_directory: str = "~/.depx/cache"

    # Custom rules
    custom_parsers: Dict[str, Any] = field(default_factory=dict)
    ignore_directories: List[str] = field(
        default_factory=lambda: [
            ".git",
            ".svn",
            ".hg",
            "__pycache__",
            ".pytest_cache",
            "node_modules",
            ".venv",
            "venv",
            "env",
        ]
    )


class ConfigManager:
    """Configuration manager"""

    DEFAULT_CONFIG_NAMES = [
        ".depx.yaml",
        ".depx.yml",
        "depx.yaml",
        "depx.yml",
        "pyproject.toml",  # For [tool.depx] section
    ]

    def __init__(self):
        self.config = DepxConfig()
        self._config_path: Optional[Path] = None

    def load_config(self, config_path: Optional[Union[str, Path]] = None) -> DepxConfig:
        """
        Load configuration from file

        Args:
            config_path: Path to config file, or None to auto-discover

        Returns:
            Loaded configuration
        """
        if config_path:
            config_file = Path(config_path)
            if not config_file.exists():
                logger.warning(f"Config file not found: {config_file}")
                return self.config
        else:
            config_file = self._find_config_file()
            if not config_file:
                logger.info("No config file found, using defaults")
                return self.config

        self._config_path = config_file

        try:
            if config_file.suffix in [".yaml", ".yml"]:
                self._load_yaml_config(config_file)
            elif config_file.name == "pyproject.toml":
                self._load_toml_config(config_file)
            else:
                logger.warning(f"Unsupported config file format: {config_file}")

        except Exception as e:
            logger.error(f"Failed to load config from {config_file}: {e}")

        return self.config

    def save_config(self, config_path: Optional[Union[str, Path]] = None) -> bool:
        """
        Save current configuration to file

        Args:
            config_path: Path to save config, or None to use current path

        Returns:
            True if saved successfully
        """
        if config_path:
            save_path = Path(config_path)
        elif self._config_path:
            save_path = self._config_path
        else:
            save_path = Path(".depx.yaml")

        try:
            if save_path.suffix in [".yaml", ".yml"]:
                return self._save_yaml_config(save_path)
            else:
                logger.error(f"Unsupported config file format for saving: {save_path}")
                return False
        except Exception as e:
            logger.error(f"Failed to save config to {save_path}: {e}")
            return False

    def create_default_config(
        self, config_path: Union[str, Path] = ".depx.yaml"
    ) -> bool:
        """
        Create a default configuration file

        Args:
            config_path: Path where to create the config file

        Returns:
            True if created successfully
        """
        config_file = Path(config_path)

        if config_file.exists():
            logger.warning(f"Config file already exists: {config_file}")
            return False

        self.config = DepxConfig()  # Reset to defaults
        return self.save_config(config_file)

    def get_config(self) -> DepxConfig:
        """Get current configuration"""
        return self.config

    def update_config(self, **kwargs) -> None:
        """Update configuration with new values"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                logger.warning(f"Unknown config key: {key}")

    def _find_config_file(self) -> Optional[Path]:
        """Find configuration file in current directory and parents"""
        current_dir = Path.cwd()

        # Search in current directory and parents
        for directory in [current_dir] + list(current_dir.parents):
            for config_name in self.DEFAULT_CONFIG_NAMES:
                config_file = directory / config_name
                if config_file.exists():
                    logger.info(f"Found config file: {config_file}")
                    return config_file

        return None

    def _load_yaml_config(self, config_file: Path) -> None:
        """Load configuration from YAML file"""
        try:
            import yaml
        except ImportError:
            logger.error("PyYAML not installed, cannot load YAML config")
            return

        with open(config_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data:
            return

        # Update scan config
        if "scan" in data:
            scan_data = data["scan"]
            if isinstance(scan_data, dict):
                for key, value in scan_data.items():
                    if hasattr(self.config.scan, key):
                        setattr(self.config.scan, key, value)

        # Update cleanup config
        if "cleanup" in data:
            cleanup_data = data["cleanup"]
            if isinstance(cleanup_data, dict):
                for key, value in cleanup_data.items():
                    if hasattr(self.config.cleanup, key):
                        setattr(self.config.cleanup, key, value)

        # Update export config
        if "export" in data:
            export_data = data["export"]
            if isinstance(export_data, dict):
                for key, value in export_data.items():
                    if hasattr(self.config.export, key):
                        setattr(self.config.export, key, value)

        # Update global settings
        for key in [
            "log_level",
            "cache_enabled",
            "cache_directory",
            "ignore_directories",
        ]:
            if key in data:
                setattr(self.config, key, data[key])

        logger.info(f"Loaded configuration from {config_file}")

    def _load_toml_config(self, config_file: Path) -> None:
        """Load configuration from pyproject.toml [tool.depx] section"""
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                logger.error("tomllib/tomli not available, cannot load TOML config")
                return

        with open(config_file, "rb") as f:
            data = tomllib.load(f)

        depx_config = data.get("tool", {}).get("depx", {})
        if not depx_config:
            return

        # Similar to YAML loading but from tool.depx section
        self._apply_config_data(depx_config)
        logger.info(f"Loaded configuration from {config_file} [tool.depx]")

    def _save_yaml_config(self, config_file: Path) -> bool:
        """Save configuration to YAML file"""
        try:
            import yaml
        except ImportError:
            logger.error("PyYAML not installed, cannot save YAML config")
            return False

        # Convert config to dict
        config_dict = {
            "scan": {
                "max_depth": self.config.scan.max_depth,
                "parallel": self.config.scan.parallel,
                "include_patterns": self.config.scan.include_patterns,
                "exclude_patterns": self.config.scan.exclude_patterns,
                "project_types": self.config.scan.project_types,
                "follow_symlinks": self.config.scan.follow_symlinks,
            },
            "cleanup": {
                "dry_run": self.config.cleanup.dry_run,
                "backup_before_clean": self.config.cleanup.backup_before_clean,
                "cleanup_types": self.config.cleanup.cleanup_types,
                "size_threshold_mb": self.config.cleanup.size_threshold_mb,
                "confirm_before_clean": self.config.cleanup.confirm_before_clean,
            },
            "export": {
                "default_format": self.config.export.default_format,
                "output_directory": self.config.export.output_directory,
                "include_metadata": self.config.export.include_metadata,
                "compress_output": self.config.export.compress_output,
            },
            "log_level": self.config.log_level,
            "cache_enabled": self.config.cache_enabled,
            "cache_directory": self.config.cache_directory,
            "ignore_directories": self.config.ignore_directories,
        }

        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)

        logger.info(f"Saved configuration to {config_file}")
        return True

    def _apply_config_data(self, data: Dict[str, Any]) -> None:
        """Apply configuration data to current config"""
        # Update scan config
        if "scan" in data:
            scan_data = data["scan"]
            if isinstance(scan_data, dict):
                for key, value in scan_data.items():
                    if hasattr(self.config.scan, key):
                        setattr(self.config.scan, key, value)

        # Update cleanup config
        if "cleanup" in data:
            cleanup_data = data["cleanup"]
            if isinstance(cleanup_data, dict):
                for key, value in cleanup_data.items():
                    if hasattr(self.config.cleanup, key):
                        setattr(self.config.cleanup, key, value)

        # Update export config
        if "export" in data:
            export_data = data["export"]
            if isinstance(export_data, dict):
                for key, value in export_data.items():
                    if hasattr(self.config.export, key):
                        setattr(self.config.export, key, value)

        # Update global settings
        for key in [
            "log_level",
            "cache_enabled",
            "cache_directory",
            "ignore_directories",
        ]:
            if key in data:
                setattr(self.config, key, data[key])


# Global config manager instance
config_manager = ConfigManager()


def get_config() -> DepxConfig:
    """Get global configuration"""
    return config_manager.get_config()


def load_config(config_path: Optional[Union[str, Path]] = None) -> DepxConfig:
    """Load configuration from file"""
    return config_manager.load_config(config_path)


def save_config(config_path: Optional[Union[str, Path]] = None) -> bool:
    """Save current configuration to file"""
    return config_manager.save_config(config_path)
