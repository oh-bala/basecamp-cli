"""Tests for config.py."""

import pytest
import json
from pathlib import Path
from basecamp_cli.config import Config


class TestConfig:
    """Test cases for Config class."""

    def test_init_default_dir(self, temp_config_dir):
        """Test Config initialization with default directory."""
        config = Config(config_dir=temp_config_dir)
        assert config.config_dir == temp_config_dir
        assert config.config_file == temp_config_dir / "config.json"
        assert config.config_dir.exists()

    def test_load_nonexistent_file(self, temp_config_dir):
        """Test loading non-existent config file."""
        config = Config(config_dir=temp_config_dir)
        result = config.load()
        assert result == {}

    def test_save_and_load(self, temp_config_dir):
        """Test saving and loading configuration."""
        config = Config(config_dir=temp_config_dir)
        test_data = {"key1": "value1", "key2": 123}
        config.save(test_data)
        
        result = config.load()
        assert result == test_data

    def test_get_set(self, temp_config_dir):
        """Test get and set methods."""
        config = Config(config_dir=temp_config_dir)
        
        # Test setting and getting a value
        config.set("test_key", "test_value")
        assert config.get("test_key") == "test_value"
        
        # Test getting non-existent key with default
        assert config.get("nonexistent", "default") == "default"

    def test_configure_oauth(self, temp_config_dir):
        """Test OAuth2 configuration."""
        config = Config(config_dir=temp_config_dir)
        config.configure_oauth(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost:8080"
        )
        
        oauth_config = config.get_oauth_config()
        assert oauth_config["client_id"] == "test_id"
        assert oauth_config["client_secret"] == "test_secret"
        assert oauth_config["redirect_uri"] == "http://localhost:8080"

    def test_configure_oauth_default_redirect(self, temp_config_dir):
        """Test OAuth2 configuration with default redirect URI."""
        config = Config(config_dir=temp_config_dir)
        config.configure_oauth(
            client_id="test_id",
            client_secret="test_secret"
        )
        
        oauth_config = config.get_oauth_config()
        assert oauth_config["redirect_uri"] == "urn:ietf:wg:oauth:2.0:oob"

    def test_get_oauth_config_not_configured(self, temp_config_dir):
        """Test getting OAuth config when not configured."""
        config = Config(config_dir=temp_config_dir)
        assert config.get_oauth_config() is None

    def test_get_set_account_id(self, temp_config_dir):
        """Test getting and setting account ID."""
        config = Config(config_dir=temp_config_dir)
        
        # Test getting non-existent account_id
        assert config.get_account_id() is None
        
        # Test setting and getting account_id
        config.set_account_id(123456)
        assert config.get_account_id() == 123456
        
        # Test updating account_id
        config.set_account_id(789012)
        assert config.get_account_id() == 789012

    def test_save_invalid_json_handling(self, temp_config_dir, monkeypatch):
        """Test handling of invalid JSON when loading."""
        config = Config(config_dir=temp_config_dir)
        
        # Write invalid JSON
        config_file = temp_config_dir / "config.json"
        config_file.write_text("invalid json{")
        
        # Should return empty dict on error
        result = config.load()
        assert result == {}
