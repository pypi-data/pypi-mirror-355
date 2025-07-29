"""
Tests for configuration management
"""

import os
import json
import tempfile
from pathlib import Path
import pytest

from feynman_learning.config import ConfigManager, get_config_manager


class TestConfigManager:
    """Test cases for ConfigManager"""
    
    def test_init_with_custom_path(self):
        """Test initialization with custom config file path"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as f:
            config_path = f.name
        
        try:
            config = ConfigManager(config_path)
            assert config.config_path == Path(config_path)
        finally:
            os.unlink(config_path)
    
    def test_init_default_path(self):
        """Test initialization with default config path"""
        config = ConfigManager()
        expected_path = Path.home() / ".feynman.conf"
        assert config.config_path == expected_path
    
    def test_default_config(self):
        """Test default configuration values"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as f:
            config_path = f.name
        
        try:
            config = ConfigManager(config_path)
            
            # Test AI provider defaults
            assert config.get("ai_provider.type") == "openai"
            assert config.get("ai_provider.model") == "gpt-3.5-turbo"
            assert config.get("ai_provider.base_url") == "https://api.openai.com/v1"
            assert config.get("ai_provider.organization") == ""
            
            # Test session defaults
            assert config.get("session.default_target_audience") == "beginner"
            assert config.get("session.auto_save") == True
            
            # Test learning defaults
            assert config.get("learning.min_mastery_score") == 0.7
            assert config.get("learning.max_explanation_attempts") == 3
            
        finally:
            os.unlink(config_path)
    
    def test_get_with_dot_notation(self):
        """Test getting values with dot notation"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as f:
            config_path = f.name
        
        try:
            config = ConfigManager(config_path)
            
            # Test existing key
            assert config.get("ai_provider.type") == "openai"
            
            # Test non-existing key with default
            assert config.get("non.existing.key", "default") == "default"
            
            # Test non-existing key without default
            assert config.get("non.existing.key") is None
            
        finally:
            os.unlink(config_path)
    
    def test_set_with_dot_notation(self):
        """Test setting values with dot notation"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as f:
            config_path = f.name
        
        try:
            config = ConfigManager(config_path)
            
            # Set existing key
            config.set("ai_provider.type", "local")
            assert config.get("ai_provider.type") == "local"
            
            # Set new nested key
            config.set("new.nested.key", "value")
            assert config.get("new.nested.key") == "value"
            
        finally:
            os.unlink(config_path)
    
    def test_save_and_load_config(self):
        """Test saving and loading configuration"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as f:
            config_path = f.name
        
        try:
            # Create and modify config
            config1 = ConfigManager(config_path)
            config1.set("ai_provider.type", "local")
            config1.set("ai_provider.api_key", "test-key")
            config1.set("custom.setting", "test-value")
            
            assert config1.save_config() == True
            
            # Load config in new instance
            config2 = ConfigManager(config_path)
            assert config2.get("ai_provider.type") == "local"
            assert config2.get("ai_provider.api_key") == "test-key"
            assert config2.get("custom.setting") == "test-value"
            
        finally:
            os.unlink(config_path)
    
    def test_ai_provider_config_methods(self):
        """Test AI provider specific configuration methods"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as f:
            config_path = f.name
        
        try:
            config = ConfigManager(config_path)
            
            # Test set_ai_provider_config
            config.set_ai_provider_config(
                "openai", 
                api_key="test-key", 
                model="gpt-4", 
                custom_param="custom-value"
            )
            
            # Test get_ai_provider_config
            ai_config = config.get_ai_provider_config()
            assert ai_config["type"] == "openai"
            assert ai_config["api_key"] == "test-key"
            assert ai_config["model"] == "gpt-4"
            assert ai_config["custom_param"] == "custom-value"
            
        finally:
            os.unlink(config_path)
    
    def test_has_api_key(self):
        """Test has_api_key method"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as f:
            config_path = f.name
        
        try:
            config = ConfigManager(config_path)
            
            # Initially no API key
            assert config.has_api_key("openai") == False
            
            # Set API key
            config.set("ai_provider.api_key", "test-key")
            assert config.has_api_key("openai") == True
            
            # Local provider should always return True
            assert config.has_api_key("local") == True
            
        finally:
            os.unlink(config_path)
    
    def test_reset_to_defaults(self):
        """Test resetting configuration to defaults"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as f:
            config_path = f.name
        
        try:
            config = ConfigManager(config_path)
            
            # Modify some settings
            config.set("ai_provider.type", "local")
            config.set("custom.setting", "custom-value")
            
            # Reset to defaults
            config.reset_to_defaults()
            
            # Check defaults are restored
            assert config.get("ai_provider.type") == "openai"
            assert config.get("custom.setting") is None
            
        finally:
            os.unlink(config_path)
    
    def test_show_config(self):
        """Test configuration display"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as f:
            config_path = f.name
        
        try:
            config = ConfigManager(config_path)
            config.set("ai_provider.api_key", "secret-key-12345")
            
            config_str = config.show_config()
            
            # Check that config is displayed
            assert "ai_provider:" in config_str
            assert "type: openai" in config_str
            
            # Check that API key is masked
            assert "secret-key-12345" not in config_str
            assert "secret-k..." in config_str
            
        finally:
            os.unlink(config_path)
    
    def test_backup_and_restore(self):
        """Test backup and restore functionality"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as f:
            config_path = f.name
        
        backup_path = config_path + ".backup"
        
        try:
            config = ConfigManager(config_path)
            config.set("test.setting", "original-value")
            config.save_config()
            
            # Create backup
            assert config.backup_config(backup_path) == True
            assert Path(backup_path).exists()
            
            # Modify config
            config.set("test.setting", "modified-value")
            config.save_config()
            
            # Restore from backup
            assert config.restore_config(backup_path) == True
            assert config.get("test.setting") == "original-value"
            
        finally:
            for path in [config_path, backup_path]:
                if os.path.exists(path):
                    os.unlink(path)
    
    def test_invalid_config_file(self):
        """Test handling of invalid configuration files"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            f.write("invalid json content")
            config_path = f.name
        
        try:
            # Should fall back to defaults without crashing
            config = ConfigManager(config_path)
            assert config.get("ai_provider.type") == "openai"  # Default value
            
        finally:
            os.unlink(config_path)


class TestGlobalConfigManager:
    """Test global configuration manager"""
    
    def test_get_config_manager_singleton(self):
        """Test that get_config_manager returns singleton instance"""
        config1 = get_config_manager()
        config2 = get_config_manager()
        
        assert config1 is config2  # Same instance


if __name__ == "__main__":
    pytest.main([__file__]) 