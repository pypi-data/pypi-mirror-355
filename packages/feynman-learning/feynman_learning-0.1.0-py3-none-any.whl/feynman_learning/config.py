"""
Configuration management for feynman-learning
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """Manages user configuration settings"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            config_file: Path to config file (defaults to ~/.feynman.conf)
        """
        if config_file:
            self.config_path = Path(config_file)
        else:
            self.config_path = Path.home() / ".feynman.conf"
        
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if not self.config_path.exists():
            return self._get_default_config()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Ensure all required keys exist
                default_config = self._get_default_config()
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Warning: Could not load config file {self.config_path}: {e}")
            print("Using default configuration.")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "ai_provider": {
                "type": "openai",  # openai, local, or none
                "api_key": "",
                "model": "gpt-3.5-turbo",
                "base_url": "https://api.openai.com/v1",
                "timeout": 30.0,
                "organization": ""
            },
            "session": {
                "default_target_audience": "beginner",
                "auto_save": True,
                "session_timeout_minutes": 60
            },
            "display": {
                "show_tips": True,
                "use_colors": True,
                "compact_mode": False
            },
            "learning": {
                "min_mastery_score": 0.7,
                "max_explanation_attempts": 3,
                "auto_identify_gaps": True
            }
        }
    
    def save_config(self) -> bool:
        """Save current configuration to file"""
        try:
            # Create directory if it doesn't exist
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config file {self.config_path}: {e}")
            return False
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        
        Args:
            key_path: Dot-separated path to config value (e.g., 'ai_provider.type')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any) -> None:
        """
        Set configuration value using dot notation
        
        Args:
            key_path: Dot-separated path to config value (e.g., 'ai_provider.type')
            value: Value to set
        """
        keys = key_path.split('.')
        current = self._config
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the final key
        current[keys[-1]] = value
    
    def get_ai_provider_config(self) -> Dict[str, Any]:
        """Get AI provider configuration"""
        return self._config.get("ai_provider", {})
    
    def set_ai_provider_config(self, provider_type: str, **kwargs) -> None:
        """
        Set AI provider configuration
        
        Args:
            provider_type: Type of provider ('openai', 'local', 'none')
            **kwargs: Additional provider settings
        """
        if "ai_provider" not in self._config:
            self._config["ai_provider"] = {}
        
        self._config["ai_provider"]["type"] = provider_type
        
        for key, value in kwargs.items():
            if value is not None:  # Only set non-None values
                self._config["ai_provider"][key] = value
    
    def has_api_key(self, provider_type: str = None) -> bool:
        """Check if API key is configured for the given provider"""
        if provider_type is None:
            provider_type = self.get("ai_provider.type", "openai")
        
        if provider_type == "openai":
            api_key = self.get("ai_provider.api_key", "")
            return bool(api_key and api_key != "")
        elif provider_type == "local":
            # Local providers might not need real API keys
            return True
        else:
            return False
    
    def get_session_config(self) -> Dict[str, Any]:
        """Get session configuration"""
        return self._config.get("session", {})
    
    def get_display_config(self) -> Dict[str, Any]:
        """Get display configuration"""
        return self._config.get("display", {})
    
    def get_learning_config(self) -> Dict[str, Any]:
        """Get learning configuration"""
        return self._config.get("learning", {})
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults"""
        self._config = self._get_default_config()
    
    def show_config(self) -> str:
        """Return formatted configuration for display"""
        def format_dict(d: Dict[str, Any], indent: int = 0) -> str:
            result = []
            prefix = "  " * indent
            
            for key, value in d.items():
                if isinstance(value, dict):
                    result.append(f"{prefix}{key}:")
                    result.append(format_dict(value, indent + 1))
                else:
                    # Hide sensitive information
                    if key == "api_key" and value:
                        display_value = f"{value[:8]}..." if len(value) > 8 else "***"
                    else:
                        display_value = value
                    result.append(f"{prefix}{key}: {display_value}")
            
            return "\n".join(result)
        
        return format_dict(self._config)
    
    def backup_config(self, backup_path: Optional[str] = None) -> bool:
        """Create a backup of the current configuration"""
        if backup_path is None:
            backup_path = str(self.config_path) + ".backup"
        
        try:
            if self.config_path.exists():
                import shutil
                shutil.copy2(self.config_path, backup_path)
                return True
            return False
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
    
    def restore_config(self, backup_path: Optional[str] = None) -> bool:
        """Restore configuration from backup"""
        if backup_path is None:
            backup_path = str(self.config_path) + ".backup"
        
        try:
            backup_file = Path(backup_path)
            if backup_file.exists():
                import shutil
                shutil.copy2(backup_file, self.config_path)
                self._config = self._load_config()
                return True
            return False
        except Exception as e:
            print(f"Error restoring backup: {e}")
            return False


# Global config instance
_config_manager = None

def get_config_manager() -> ConfigManager:
    """Get global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

def reset_config_manager():
    """Reset the global config manager (useful after config file changes)"""
    global _config_manager
    _config_manager = None 