"""Configuration management for Basecamp CLI."""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
import click


class Config:
    """Manages OAuth2 configuration and settings."""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize configuration manager.

        Args:
            config_dir: Directory to store configuration files. Defaults to ~/.basecamp
        """
        if config_dir is None:
            config_dir = Path.home() / ".basecamp"
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "config.json"
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> Dict[str, Any]:
        """Load configuration from file.

        Returns:
            Dictionary containing configuration settings
        """
        if not self.config_file.exists():
            return {}
        try:
            with open(self.config_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            click.echo(f"Error loading config: {e}", err=True)
            return {}

    def save(self, config: Dict[str, Any]) -> None:
        """Save configuration to file.

        Args:
            config: Dictionary containing configuration settings
        """
        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=2)
            os.chmod(self.config_file, 0o600)  # Restrict permissions
        except IOError as e:
            click.echo(f"Error saving config: {e}", err=True)
            raise

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key doesn't exist

        Returns:
            Configuration value or default
        """
        config = self.load()
        return config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            key: Configuration key
            value: Configuration value
        """
        config = self.load()
        config[key] = value
        self.save(config)

    def configure_oauth(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str = "http://localhost:8080/callback",
    ) -> None:
        """Configure OAuth2 settings.

        Args:
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            redirect_uri: OAuth2 redirect URI (defaults to out-of-band)
        """
        config = self.load()
        config["oauth"] = {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
        }
        self.save(config)

    def get_oauth_config(self) -> Optional[Dict[str, str]]:
        """Get OAuth2 configuration.

        Returns:
            Dictionary with OAuth2 settings or None if not configured
        """
        return self.get("oauth")

    def get_account_id(self) -> Optional[int]:
        """Get the configured account ID.

        Returns:
            Account ID as integer or None if not configured
        """
        account_id = self.get("account_id")
        if account_id is not None:
            return int(account_id)
        return None

    def set_account_id(self, account_id: int) -> None:
        """Set the account ID.

        Args:
            account_id: Basecamp account ID
        """
        self.set("account_id", account_id)
