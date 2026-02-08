"""Tests for api_client.py."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from basecamp_cli.api_client import BasecampAPIClient, BasecampAPIError
from basecamp_cli.token_manager import TokenManager


class TestBasecampAPIClient:
    """Test cases for BasecampAPIClient class."""

    @patch('basecamp_cli.api_client.TokenManager')
    def test_init(self, mock_token_manager_class):
        """Test BasecampAPIClient initialization."""
        mock_token_manager = Mock()
        mock_token_manager_class.return_value = mock_token_manager
        
        client = BasecampAPIClient(account_id=123456)
        
        assert client.account_id == 123456
        assert client.BASE_URL == "https://3.basecampapi.com"

    @patch('basecamp_cli.api_client.requests.request')
    def test_make_request_success(self, mock_request):
        """Test successful API request."""
        mock_response = Mock()
        mock_response.json.return_value = {"id": 1, "name": "Test"}
        mock_response.status_code = 200
        mock_response.content = b'{"id": 1, "name": "Test"}'
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response
        
        token_manager = Mock()
        token_manager.get_access_token.return_value = "test_token"
        
        client = BasecampAPIClient(token_manager=token_manager)
        result = client._make_request("GET", "/test")
        
        assert result == {"id": 1, "name": "Test"}
        mock_request.assert_called_once()

    @patch('basecamp_cli.api_client.requests.request')
    def test_make_request_no_token(self, mock_request):
        """Test API request without access token."""
        token_manager = Mock()
        token_manager.get_access_token.return_value = None
        
        client = BasecampAPIClient(token_manager=token_manager)
        
        with pytest.raises(BasecampAPIError, match="No access token"):
            client._make_request("GET", "/test")

    @patch('basecamp_cli.api_client.requests.request')
    def test_make_request_http_error(self, mock_request):
        """Test API request with HTTP error."""
        import requests
        mock_response = Mock()
        mock_response.json.return_value = {"error": "Not found"}
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_request.return_value = mock_response
        
        token_manager = Mock()
        token_manager.get_access_token.return_value = "test_token"
        
        client = BasecampAPIClient(token_manager=token_manager)
        
        with pytest.raises(BasecampAPIError):
            client._make_request("GET", "/test")

    @patch('basecamp_cli.api_client.requests.request')
    def test_make_request_empty_response(self, mock_request):
        """Test API request with empty response (204)."""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_response.content = b''
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response
        
        token_manager = Mock()
        token_manager.get_access_token.return_value = "test_token"
        
        client = BasecampAPIClient(token_manager=token_manager)
        result = client._make_request("DELETE", "/test")
        
        assert result == {}

    @patch('basecamp_cli.api_client.requests.request')
    def test_make_request_list_response(self, mock_request):
        """Test API request returning a list."""
        mock_response = Mock()
        mock_response.json.return_value = [{"id": 1}, {"id": 2}]
        mock_response.status_code = 200
        mock_response.content = b'[{"id": 1}, {"id": 2}]'
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response
        
        token_manager = Mock()
        token_manager.get_access_token.return_value = "test_token"
        
        client = BasecampAPIClient(token_manager=token_manager)
        result = client._make_request("GET", "/test")
        
        assert isinstance(result, list)
        assert len(result) == 2

    def test_get_accounts(self):
        """Test getting accounts (returns empty list as API doesn't support it)."""
        token_manager = Mock()
        token_manager.get_access_token.return_value = "test_token"
        
        client = BasecampAPIClient(token_manager=token_manager)
        accounts = client.get_accounts()
        
        assert accounts == []

    @patch.object(BasecampAPIClient, '_make_request')
    def test_get_projects(self, mock_make_request):
        """Test getting projects list."""
        # Mock response object with headers
        mock_response = Mock()
        mock_response.headers = {"Link": ""}
        
        mock_make_request.return_value = ([
            {"id": 1, "name": "Project 1"},
            {"id": 2, "name": "Project 2"}
        ], mock_response)
        
        token_manager = Mock()
        token_manager.get_access_token.return_value = "test_token"
        
        client = BasecampAPIClient(account_id=123456, token_manager=token_manager)
        projects, next_url = client.get_projects()
        
        assert len(projects) == 2
        assert next_url is None
        mock_make_request.assert_called_once_with("GET", "/123456/projects.json", return_response=True)

    @patch.object(BasecampAPIClient, '_make_request')
    def test_get_projects_no_account_id(self, mock_make_request):
        """Test getting projects without account ID."""
        token_manager = Mock()
        token_manager.get_access_token.return_value = "test_token"
        
        client = BasecampAPIClient(token_manager=token_manager)
        
        with pytest.raises(BasecampAPIError, match="Account ID is required"):
            client.get_projects()

    @patch.object(BasecampAPIClient, '_make_request')
    def test_get_project(self, mock_make_request):
        """Test getting a specific project."""
        mock_make_request.return_value = {"id": 1, "name": "Test Project"}
        
        token_manager = Mock()
        token_manager.get_access_token.return_value = "test_token"
        
        client = BasecampAPIClient(account_id=123456, token_manager=token_manager)
        project = client.get_project(789)
        
        assert project["id"] == 1
        mock_make_request.assert_called_once_with("GET", "/123456/projects/789.json")

    @patch.object(BasecampAPIClient, '_make_request')
    def test_create_project(self, mock_make_request):
        """Test creating a project."""
        mock_make_request.return_value = {"id": 1, "name": "New Project"}
        
        token_manager = Mock()
        token_manager.get_access_token.return_value = "test_token"
        
        client = BasecampAPIClient(account_id=123456, token_manager=token_manager)
        project = client.create_project("New Project", "Description")
        
        assert project["name"] == "New Project"
        mock_make_request.assert_called_once_with(
            "POST", "/123456/projects.json", data={"name": "New Project", "description": "Description"}
        )

    @patch.object(BasecampAPIClient, '_make_request')
    def test_update_project(self, mock_make_request):
        """Test updating a project."""
        mock_make_request.return_value = {"id": 1, "name": "Updated Project"}
        
        token_manager = Mock()
        token_manager.get_access_token.return_value = "test_token"
        
        client = BasecampAPIClient(account_id=123456, token_manager=token_manager)
        project = client.update_project(789, name="Updated Project")
        
        assert project["name"] == "Updated Project"
        mock_make_request.assert_called_once_with(
            "PUT", "/123456/projects/789.json", data={"name": "Updated Project"}
        )

    @patch.object(BasecampAPIClient, '_make_request')
    def test_delete_project(self, mock_make_request):
        """Test deleting a project."""
        mock_make_request.return_value = {}
        
        token_manager = Mock()
        token_manager.get_access_token.return_value = "test_token"
        
        client = BasecampAPIClient(account_id=123456, token_manager=token_manager)
        client.delete_project(789)
        
        mock_make_request.assert_called_once_with("DELETE", "/123456/projects/789.json")

    @patch.object(BasecampAPIClient, '_make_request')
    def test_get_todos(self, mock_make_request):
        """Test getting todos."""
        # Mock response object with headers
        mock_response = Mock()
        mock_response.headers = {"Link": ""}
        
        mock_make_request.return_value = ([
            {"id": 1, "content": "Todo 1"},
            {"id": 2, "content": "Todo 2"}
        ], mock_response)
        
        token_manager = Mock()
        token_manager.get_access_token.return_value = "test_token"
        
        client = BasecampAPIClient(account_id=123456, token_manager=token_manager)
        todos, next_url = client.get_todos(789, 456)
        
        assert len(todos) == 2
        assert next_url is None
        mock_make_request.assert_called_once_with("GET", "/123456/projects/789/todosets/456/todos.json", return_response=True)

    @patch.object(BasecampAPIClient, '_make_request')
    def test_create_todo(self, mock_make_request):
        """Test creating a todo."""
        mock_make_request.return_value = {"id": 1, "content": "New Todo"}
        
        token_manager = Mock()
        token_manager.get_access_token.return_value = "test_token"
        
        client = BasecampAPIClient(account_id=123456, token_manager=token_manager)
        todo = client.create_todo(789, 456, "New Todo", [123, 456])
        
        assert todo["content"] == "New Todo"
        mock_make_request.assert_called_once_with(
            "POST",
            "/123456/projects/789/todosets/456/todos.json",
            data={"content": "New Todo", "assignee_ids": [123, 456]}
        )
