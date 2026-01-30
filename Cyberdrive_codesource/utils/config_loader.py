"""
Configuration loader for YAML and JSON files
"""
import yaml
import json
from pathlib import Path
from typing import Dict, Any

class ConfigLoader:
    """Load and manage configuration files"""
    
    @staticmethod
    def load_yaml(file_path: str | Path) -> Dict[str, Any]:
        """
        Load YAML configuration file
        
        Args:
            file_path: Path to YAML file
            
        Returns:
            Configuration dictionary
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return config or {}
    
    @staticmethod
    def load_json(file_path: str | Path) -> Dict[str, Any]:
        """
        Load JSON configuration file
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Configuration dictionary
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        return config
    
    @staticmethod
    def save_yaml(data: Dict[str, Any], file_path: str | Path):
        """Save data to YAML file"""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    
    @staticmethod
    def save_json(data: Dict[str, Any], file_path: str | Path, indent: int = 2):
        """Save data to JSON file"""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent)

    @staticmethod
    def get_value(config: Dict[str, Any], path: str, default: Any = None) -> Any:
        """
        Get nested value from config using dot notation
        
        Example:
            config = {'server': {'name': 'RC Car'}}
            get_value(config, 'server.name') -> 'RC Car'
        """
        keys = path.split('.')
        value = config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value