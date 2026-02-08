"""Token management for Basecamp CLI using secure storage."""

import keyring
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import click


class TokenManager:
    """Manages OAuth2 tokens securely using keyring."""

    SERVICE_NAME = "basecamp-cli"
    KEYRING_KEY = "tokens"

    def __init__(self, account_id: Optional[str] = None):
        """Initialize token manager.

        Args:
            account_id: Basecamp account ID (optional, for multi-account support)
        """
        self.account_id = account_id or "default"

    def _get_keyring_key(self) -> str:
        """Get keyring key for this account."""
        return f"{self.KEYRING_KEY}:{self.account_id}"

    def store_tokens(
        self, access_token: str, refresh_token: Optional[str] = None, expires_in: Optional[int] = None
    ) -> None:
        """Store OAuth2 tokens securely.

        Args:
            access_token: OAuth2 access token
            refresh_token: OAuth2 refresh token (optional)
            expires_in: Token expiration time in seconds (optional)
        """
        token_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": None,
        }

        if expires_in:
            token_data["expires_at"] = (datetime.now() + timedelta(seconds=expires_in)).isoformat()

        try:
            keyring.set_password(
                self.SERVICE_NAME, self._get_keyring_key(), json.dumps(token_data)
            )
        except Exception as e:
            click.echo(f"Error storing tokens: {e}", err=True)
            raise

    def get_tokens(self) -> Optional[Dict[str, Any]]:
        """Retrieve stored tokens.

        Returns:
            Dictionary with token data or None if not found
        """
        try:
            token_json = keyring.get_password(self.SERVICE_NAME, self._get_keyring_key())
            if not token_json:
                return None
            return json.loads(token_json)
        except Exception as e:
            click.echo(f"Error retrieving tokens: {e}", err=True)
            return None

    def get_access_token(self) -> Optional[str]:
        """Get the current access token.

        Returns:
            Access token string or None if not available
        """
        tokens = self.get_tokens()
        if not tokens:
            return None
        return tokens.get("access_token")

    def is_token_expired(self) -> bool:
        """Check if the current token is expired.

        Returns:
            True if token is expired or missing, False otherwise
        """
        tokens = self.get_tokens()
        if not tokens:
            return True

        expires_at = tokens.get("expires_at")
        if not expires_at:
            return False  # No expiration info, assume valid

        try:
            expires = datetime.fromisoformat(expires_at)
            return datetime.now() >= expires
        except (ValueError, TypeError):
            return False

    def clear_tokens(self) -> None:
        """Clear stored tokens."""
        try:
            keyring.delete_password(self.SERVICE_NAME, self._get_keyring_key())
        except keyring.errors.PasswordDeleteError:
            pass  # Token doesn't exist, that's fine
