"""Tests for auth.py."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from basecamp_cli.auth import AuthHandler


class TestAuthHandler:
    """Test cases for AuthHandler class."""

    def test_init(self):
        """Test AuthHandler initialization."""
        handler = AuthHandler()
        assert handler.config is not None
        assert handler.token_manager is not None

    def test_get_authorization_url(self):
        """Test authorization URL generation."""
        handler = AuthHandler()
        url = handler.get_authorization_url(
            client_id="test_id",
            redirect_uri="http://localhost:8080"
        )
        
        assert "launchpad.37signals.com" in url
        assert "client_id=test_id" in url
        assert "redirect_uri=http://localhost:8080" in url
        assert "type=web_server" in url

    def test_get_authorization_url_with_account_id(self):
        """Test authorization URL generation with account ID."""
        handler = AuthHandler()
        url = handler.get_authorization_url(
            client_id="test_id",
            redirect_uri="http://localhost:8080",
            account_id=123456
        )
        
        assert "account_id=123456" in url

    @patch('basecamp_cli.auth.requests.post')
    def test_exchange_code_for_token_success(self, mock_post):
        """Test successful token exchange."""
        handler = AuthHandler()
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 7200
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = handler.exchange_code_for_token(
            authorization_code="test_code",
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost:8080"
        )
        
        assert result["access_token"] == "test_access_token"
        assert result["refresh_token"] == "test_refresh_token"
        mock_post.assert_called_once()

    @patch('basecamp_cli.auth.requests.post')
    def test_exchange_code_for_token_http_error(self, mock_post):
        """Test token exchange with HTTP error."""
        import requests
        handler = AuthHandler()
        mock_response = Mock()
        mock_response.json.return_value = {"error": "invalid_grant"}
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_response.status_code = 400
        mock_post.return_value = mock_response
        
        with pytest.raises(requests.exceptions.HTTPError):
            handler.exchange_code_for_token(
                authorization_code="invalid_code",
                client_id="test_id",
                client_secret="test_secret",
                redirect_uri="http://localhost:8080"
            )

    @patch('basecamp_cli.auth.requests.post')
    def test_exchange_code_for_token_request_error(self, mock_post):
        """Test token exchange with request error."""
        import requests
        handler = AuthHandler()
        mock_post.side_effect = requests.exceptions.ConnectionError()
        
        with pytest.raises(requests.exceptions.ConnectionError):
            handler.exchange_code_for_token(
                authorization_code="test_code",
                client_id="test_id",
                client_secret="test_secret",
                redirect_uri="http://localhost:8080"
            )

    @patch('basecamp_cli.auth.webbrowser')
    @patch('basecamp_cli.auth.click')
    @patch('basecamp_cli.auth.requests.post')
    def test_authenticate_success(self, mock_post, mock_click, mock_webbrowser, temp_config_dir):
        """Test successful authentication flow."""
        from basecamp_cli.config import Config
        from basecamp_cli.token_manager import TokenManager
        
        # Setup config
        config = Config(config_dir=temp_config_dir)
        config.configure_oauth(
            client_id="test_id",
            client_secret="test_secret"
        )
        
        handler = AuthHandler()
        handler.config = config
        
        # Mock token exchange response
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "test_token",
            "refresh_token": "test_refresh",
            "expires_in": 7200
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        # Mock user input
        mock_click.prompt.return_value = "auth_code_123"
        mock_click.echo = Mock()
        
        # Mock token manager
        handler.token_manager = Mock(spec=TokenManager)
        
        handler.authenticate()
        
        mock_webbrowser.open.assert_called_once()
        mock_post.assert_called_once()
        handler.token_manager.store_tokens.assert_called_once()

    @patch('basecamp_cli.auth.click')
    def test_authenticate_not_configured(self, mock_click, temp_config_dir):
        """Test authentication when OAuth2 is not configured."""
        from basecamp_cli.config import Config
        
        handler = AuthHandler()
        handler.config = Config(config_dir=temp_config_dir)
        mock_click.echo = Mock()
        
        handler.authenticate()
        
        mock_click.echo.assert_called()
        # Should not proceed with authentication
