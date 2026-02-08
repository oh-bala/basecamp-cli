"""Tests for token_manager.py."""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from basecamp_cli.token_manager import TokenManager


class TestTokenManager:
    """Test cases for TokenManager class."""

    def test_init_default_account(self):
        """Test TokenManager initialization with default account."""
        manager = TokenManager()
        assert manager.account_id == "default"

    def test_init_custom_account(self):
        """Test TokenManager initialization with custom account."""
        manager = TokenManager(account_id="account123")
        assert manager.account_id == "account123"

    def test_get_keyring_key(self):
        """Test keyring key generation."""
        manager = TokenManager(account_id="test_account")
        assert manager._get_keyring_key() == "tokens:test_account"

    @patch('basecamp_cli.token_manager.keyring')
    def test_store_tokens(self, mock_keyring):
        """Test storing tokens."""
        manager = TokenManager()
        manager.store_tokens(
            access_token="test_token",
            refresh_token="test_refresh",
            expires_in=7200
        )
        
        mock_keyring.set_password.assert_called_once()
        call_args = mock_keyring.set_password.call_args
        assert call_args[0][0] == TokenManager.SERVICE_NAME
        assert call_args[0][1] == "tokens:default"
        
        # Verify stored data
        stored_data = json.loads(call_args[0][2])
        assert stored_data["access_token"] == "test_token"
        assert stored_data["refresh_token"] == "test_refresh"
        assert stored_data["expires_at"] is not None

    @patch('basecamp_cli.token_manager.keyring')
    def test_store_tokens_no_expires(self, mock_keyring):
        """Test storing tokens without expiration."""
        manager = TokenManager()
        manager.store_tokens(access_token="test_token")
        
        call_args = mock_keyring.set_password.call_args
        stored_data = json.loads(call_args[0][2])
        assert stored_data["expires_at"] is None

    @patch('basecamp_cli.token_manager.keyring')
    def test_get_tokens(self, mock_keyring):
        """Test retrieving tokens."""
        manager = TokenManager()
        token_data = {
            "access_token": "test_token",
            "refresh_token": "test_refresh",
            "expires_at": None
        }
        mock_keyring.get_password.return_value = json.dumps(token_data)
        
        result = manager.get_tokens()
        assert result == token_data
        mock_keyring.get_password.assert_called_once_with(
            TokenManager.SERVICE_NAME, "tokens:default"
        )

    @patch('basecamp_cli.token_manager.keyring')
    def test_get_tokens_not_found(self, mock_keyring):
        """Test retrieving tokens when not found."""
        manager = TokenManager()
        mock_keyring.get_password.return_value = None
        
        result = manager.get_tokens()
        assert result is None

    @patch('basecamp_cli.token_manager.keyring')
    def test_get_access_token(self, mock_keyring):
        """Test getting access token."""
        manager = TokenManager()
        token_data = {
            "access_token": "test_token",
            "refresh_token": "test_refresh",
            "expires_at": None
        }
        mock_keyring.get_password.return_value = json.dumps(token_data)
        
        result = manager.get_access_token()
        assert result == "test_token"

    @patch('basecamp_cli.token_manager.keyring')
    def test_get_access_token_not_found(self, mock_keyring):
        """Test getting access token when tokens not found."""
        manager = TokenManager()
        mock_keyring.get_password.return_value = None
        
        result = manager.get_access_token()
        assert result is None

    @patch('basecamp_cli.token_manager.keyring')
    def test_is_token_expired_no_tokens(self, mock_keyring):
        """Test token expiration check when no tokens."""
        manager = TokenManager()
        mock_keyring.get_password.return_value = None
        
        assert manager.is_token_expired() is True

    @patch('basecamp_cli.token_manager.keyring')
    def test_is_token_expired_no_expires_at(self, mock_keyring):
        """Test token expiration check when no expiration info."""
        manager = TokenManager()
        token_data = {
            "access_token": "test_token",
            "expires_at": None
        }
        mock_keyring.get_password.return_value = json.dumps(token_data)
        
        assert manager.is_token_expired() is False

    @patch('basecamp_cli.token_manager.keyring')
    def test_is_token_expired_not_expired(self, mock_keyring):
        """Test token expiration check when token is not expired."""
        manager = TokenManager()
        expires_at = (datetime.now() + timedelta(hours=1)).isoformat()
        token_data = {
            "access_token": "test_token",
            "expires_at": expires_at
        }
        mock_keyring.get_password.return_value = json.dumps(token_data)
        
        assert manager.is_token_expired() is False

    @patch('basecamp_cli.token_manager.keyring')
    def test_is_token_expired_expired(self, mock_keyring):
        """Test token expiration check when token is expired."""
        manager = TokenManager()
        expires_at = (datetime.now() - timedelta(hours=1)).isoformat()
        token_data = {
            "access_token": "test_token",
            "expires_at": expires_at
        }
        mock_keyring.get_password.return_value = json.dumps(token_data)
        
        assert manager.is_token_expired() is True

    @patch('basecamp_cli.token_manager.keyring')
    def test_clear_tokens(self, mock_keyring):
        """Test clearing tokens."""
        manager = TokenManager()
        manager.clear_tokens()
        
        mock_keyring.delete_password.assert_called_once_with(
            TokenManager.SERVICE_NAME, "tokens:default"
        )

    @patch('basecamp_cli.token_manager.keyring')
    def test_clear_tokens_not_found(self, mock_keyring):
        """Test clearing tokens when they don't exist."""
        import keyring.errors
        manager = TokenManager()
        mock_keyring.delete_password.side_effect = keyring.errors.PasswordDeleteError()
        
        # Should not raise an exception
        manager.clear_tokens()
