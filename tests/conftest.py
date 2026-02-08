"""Pytest configuration and fixtures."""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for configuration files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_keyring():
    """Mock keyring module."""
    import keyring
    from unittest.mock import patch
    
    with patch('basecamp_cli.token_manager.keyring') as mock_kr:
        mock_kr.get_password.return_value = None
        mock_kr.set_password.return_value = None
        mock_kr.delete_password.return_value = None
        yield mock_kr


@pytest.fixture
def mock_requests():
    """Mock requests module."""
    from unittest.mock import patch
    
    with patch('basecamp_cli.api_client.requests') as mock_req:
        yield mock_req


@pytest.fixture
def mock_webbrowser():
    """Mock webbrowser module."""
    from unittest.mock import patch
    
    with patch('basecamp_cli.auth.webbrowser') as mock_wb:
        mock_wb.open.return_value = True
        yield mock_wb


@pytest.fixture
def sample_oauth_config():
    """Sample OAuth2 configuration."""
    return {
        "client_id": "test_client_id",
        "client_secret": "test_client_secret",
        "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
    }


@pytest.fixture
def sample_token_data():
    """Sample token data."""
    from datetime import datetime, timedelta
    
    return {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "expires_at": (datetime.now() + timedelta(hours=2)).isoformat(),
    }
