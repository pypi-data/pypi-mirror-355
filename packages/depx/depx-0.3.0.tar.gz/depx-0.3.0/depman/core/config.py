"""
Configuration management for DepMan.
"""
import os
import yaml
from pathlib import Path
import platform
import logging


class Config:
    """Configuration manager for DepMan."""

    def __init__(self, config_path=None):
        """
        Initialize the configuration manager.

        Args:
            config_path (Path, optional): Path to the configuration file. 
                                          Defaults to ~/.depman/config.yml.
        """
        self.logger = logging.getLogger("depman.config")
        
        # Default config path is ~/.depman/config.yml
        if config_path is None:
            self.config_dir = Path.home() / ".depman"
            self.config_path = self.config_dir / "config.yml"
        else:
            self.config_path = Path(config_path)
            self.config_dir = self.config_path.parent
        
        # Ensure the config directory exists
        self.config_dir.mkdir(exist_ok=True, parents=True)
        
        # Default configuration
        self.default_config = {
            "package_managers": {
                "detected": {},
                "paths": {},
                "preferred": {},
            },
            "cache_dir": str(self.config_dir / "cache"),
            "log_level": "INFO",
            "security_scan_enabled": True,
            "security_db_path": str(self.config_dir / "security_db"),
            "repositories": {},
        }
        
        # Load or create configuration
        self.config = self._load_config()
        
        # Set up logging
        self._setup_logging()
        
        # Detect system info
        self.system_info = self._detect_system_info()
        self.logger.debug(f"Detected system: {self.system_info}")
        
        # Make sure cache directory exists
        Path(self.get("cache_dir")).mkdir(exist_ok=True, parents=True)
    
    def _detect_system_info(self):
        """
        Detect information about the system.
        
        Returns:
            dict: System information including OS, architecture, etc.
        """
        system = platform.system().lower()
        info = {
            "os": system,
            "architecture": platform.machine(),
            "os_version": platform.version(),
            "python_version": platform.python_version(),
        }
        
        # Add more detailed OS information
        if system == "linux":
            # Try to get distribution info
            try:
                import distro
                info["distribution"] = distro.id()
                info["distribution_version"] = distro.version()
            except ImportError:
                try:
                    with open("/etc/os-release") as f:
                        os_release = dict(line.strip().split("=", 1) for line in f if "=" in line)
                    info["distribution"] = os_release.get("ID", "").strip('"')
                    info["distribution_version"] = os_release.get("VERSION_ID", "").strip('"')
                except (FileNotFoundError, IOError):
                    info["distribution"] = "unknown"
                    info["distribution_version"] = "unknown"
        
        return info
        
    def _load_config(self):
        """
        Load the configuration from file or create a new one.
        
        Returns:
            dict: The loaded configuration.
        """
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    config = yaml.safe_load(f)
                    
                # Merge with defaults for any missing keys
                merged_config = self.default_config.copy()
                self._deep_update(merged_config, config)
                    
                return merged_config
            except Exception as e:
                print(f"Error loading config: {e}. Using defaults.")
                return self.default_config.copy()
        else:
            # Create default config
            try:
                with open(self.config_path, "w") as f:
                    yaml.dump(self.default_config, f, default_flow_style=False)
            except Exception as e:
                print(f"Error creating default config: {e}")
            
            return self.default_config.copy()
            
    def _deep_update(self, d, u):
        """
        Recursively update a dictionary.
        
        Args:
            d (dict): The dictionary to update.
            u (dict): The dictionary with updates.
        
        Returns:
            dict: The updated dictionary.
        """
        for k, v in u.items():
            if isinstance(v, dict):
                d[k] = self._deep_update(d.get(k, {}), v)
            else:
                d[k] = v
        return d
            
    def _setup_logging(self):
        """Set up logging based on the configuration."""
        log_level_str = self.get("log_level", "INFO")
        log_level = getattr(logging, log_level_str.upper(), logging.INFO)
        
        logs_dir = self.config_dir / "logs"
        logs_dir.mkdir(exist_ok=True, parents=True)
        
        log_file = logs_dir / "depman.log"
        
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def get(self, key, default=None):
        """
        Get a configuration value.
        
        Args:
            key (str): The key to get.
            default: The default value if the key doesn't exist.
            
        Returns:
            The value for the key or the default.
        """
        keys = key.split(".")
        value = self.config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key, value):
        """
        Set a configuration value.
        
        Args:
            key (str): The key to set.
            value: The value to set.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        keys = key.split(".")
        config = self.config
        
        # Navigate to the right level
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            elif not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]
                
        # Set the value
        config[keys[-1]] = value
        
        # Save the configuration
        return self.save()
    
    def save(self):
        """
        Save the configuration to disk.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            with open(self.config_path, "w") as f:
                yaml.dump(self.config, f, default_flow_style=False)
            return True
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
            return False 