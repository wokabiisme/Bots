"""Configuration loader for YAML and environment files."""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from loguru import logger


class ConfigLoader:
    """Load and manage configuration from YAML and environment."""
    
    def __init__(self, config_dir: str = "config"):
        """Initialize config loader.
        
        Args:
            config_dir: Directory containing YAML configuration files
        """
        self.config_dir = Path(config_dir)
        self.configs: Dict[str, Any] = {}
    
    def load_yaml(self, filename: str) -> Dict[str, Any]:
        """Load YAML configuration file.
        
        Args:
            filename: Name of YAML file (with or without .yaml extension)
            
        Returns:
            Configuration dictionary
        """
        if not filename.endswith('.yaml'):
            filename = f"{filename}.yaml"
        
        filepath = self.config_dir / filename
        
        if not filepath.exists():
            logger.warning(f"Configuration file not found: {filepath}")
            return {}
        
        try:
            with open(filepath, 'r') as f:
                config = yaml.safe_load(f)
                logger.info(f"Loaded configuration from {filename}")
                return config or {}
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
            return {}
    
    def load_all_configs(self) -> Dict[str, Any]:
        """Load all YAML configuration files.
        
        Returns:
            Dictionary of all configurations
        """
        self.configs = {}
        
        if not self.config_dir.exists():
            logger.warning(f"Configuration directory not found: {self.config_dir}")
            return self.configs
        
        for yaml_file in self.config_dir.glob('*.yaml'):
            config_name = yaml_file.stem
            self.configs[config_name] = self.load_yaml(config_name)
        
        logger.info(f"Loaded {len(self.configs)} configuration files")
        return self.configs
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key.
        
        Args:
            key: Configuration key (e.g., 'strategy.momentum.threshold')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.configs
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value or default
    
    def merge_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge environment variables into configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Merged configuration
        """
        # Environment variables override YAML config
        for key, value in os.environ.items():
            if key.startswith('APP_'):
                config_key = key[4:].lower()  # Remove 'APP_' prefix
                self._set_nested(config, config_key, value)
        
        return config
    
    @staticmethod
    def _set_nested(config: Dict[str, Any], key: str, value: Any) -> None:
        """Set nested dictionary value using dot notation.
        
        Args:
            config: Configuration dictionary
            key: Key path (e.g., 'strategy.momentum.threshold')
            value: Value to set
        """
        keys = key.split('.')
        current = config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value


# Global config loader instance
config_loader = ConfigLoader()
