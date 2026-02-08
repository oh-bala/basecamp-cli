"""Tests for cli.py."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner
from basecamp_cli.cli import cli


class TestCLI:
    """Test cases for CLI commands."""

    def test_cli_version(self):
        """Test CLI version command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    @patch('basecamp_cli.cli.Config')
    def test_configure(self, mock_config_class):
        """Test configure command."""
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["configure"],
            input="test_client_id\ntest_client_secret\n"
        )
        
        assert result.exit_code == 0
        mock_config.configure_oauth.assert_called_once()

    @patch('basecamp_cli.cli.TokenManager')
    def test_logout(self, mock_token_manager_class):
        """Test logout command."""
        mock_token_manager = Mock()
        mock_token_manager_class.return_value = mock_token_manager
        
        runner = CliRunner()
        result = runner.invoke(cli, ["logout"])
        
        assert result.exit_code == 0
        mock_token_manager.clear_tokens.assert_called_once()

    @patch('basecamp_cli.cli.BasecampAPIClient')
    def test_projects_list(self, mock_client_class):
        """Test projects list command."""
        mock_client = Mock()
        mock_client.get_projects.return_value = (
            [
                {"id": 1, "name": "Project 1", "description": "Desc 1"},
                {"id": 2, "name": "Project 2", "description": "Desc 2"}
            ],
            None  # No next page
        )
        mock_client_class.return_value = mock_client
        
        runner = CliRunner()
        result = runner.invoke(cli, ["projects", "list", "--account-id", "123456"])
        
        assert result.exit_code == 0
        assert "Project 1" in result.output
        assert "Project 2" in result.output

    @patch('basecamp_cli.cli.BasecampAPIClient')
    def test_projects_list_json(self, mock_client_class):
        """Test projects list command with JSON output."""
        import json
        mock_client = Mock()
        mock_client.get_projects.return_value = ([{"id": 1, "name": "Project 1"}], None)
        mock_client_class.return_value = mock_client
        
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["projects", "list", "--account-id", "123456", "--format", "json"]
        )
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1

    @patch('basecamp_cli.cli.BasecampAPIClient')
    def test_projects_list_plain(self, mock_client_class):
        """Test projects list command with plain output."""
        mock_client = Mock()
        mock_client.get_projects.return_value = ([{"id": 1, "name": "Project 1"}], None)
        mock_client_class.return_value = mock_client
        
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["projects", "list", "--account-id", "123456", "--format", "plain"]
        )
        
        assert result.exit_code == 0
        assert "id" in result.output
        assert "name" in result.output
        assert "1" in result.output
        assert "Project 1" in result.output

    @patch('basecamp_cli.cli.BasecampAPIClient')
    def test_projects_get(self, mock_client_class):
        """Test projects get command."""
        mock_client = Mock()
        mock_client.get_project.return_value = {
            "id": 789,
            "name": "Test Project",
            "description": "Test Description",
            "created_at": "2024-01-01",
            "updated_at": "2024-01-02"
        }
        mock_client_class.return_value = mock_client
        
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["projects", "get", "789", "--account-id", "123456"]
        )
        
        assert result.exit_code == 0
        assert "Test Project" in result.output

    @patch('basecamp_cli.cli.BasecampAPIClient')
    def test_projects_create(self, mock_client_class):
        """Test projects create command."""
        mock_client = Mock()
        mock_client.create_project.return_value = {
            "id": 1,
            "name": "New Project",
            "description": "New Description"
        }
        mock_client_class.return_value = mock_client
        
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "projects", "create",
                "--name", "New Project",
                "--description", "New Description",
                "--account-id", "123456"
            ]
        )
        
        assert result.exit_code == 0
        assert "New Project" in result.output
        mock_client.create_project.assert_called_once_with("New Project", "New Description")

    @patch('basecamp_cli.cli.BasecampAPIClient')
    def test_projects_update(self, mock_client_class):
        """Test projects update command."""
        mock_client = Mock()
        mock_client.update_project.return_value = {
            "id": 789,
            "name": "Updated Project",
            "description": "Updated Description"
        }
        mock_client_class.return_value = mock_client
        
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "projects", "update", "789",
                "--name", "Updated Project",
                "--account-id", "123456"
            ]
        )
        
        assert result.exit_code == 0
        assert "Updated Project" in result.output

    @patch('basecamp_cli.cli.BasecampAPIClient')
    def test_projects_delete(self, mock_client_class):
        """Test projects delete command."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["projects", "delete", "789", "--account-id", "123456", "--yes"]
        )
        
        assert result.exit_code == 0
        mock_client.delete_project.assert_called_once_with(789)
        assert "789" in result.output or "deleted" in result.output.lower()

    @patch('basecamp_cli.cli.BasecampAPIClient')
    def test_projects_delete_json(self, mock_client_class):
        """Test projects delete command with JSON output."""
        import json
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["projects", "delete", "789", "--account-id", "123456", "--format", "json", "--yes"]
        )
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["project_id"] == 789
        assert data["status"] == "deleted"

    @patch('basecamp_cli.cli.BasecampAPIClient')
    def test_todos_list(self, mock_client_class):
        """Test todos list command."""
        mock_client = Mock()
        mock_client.get_todos.return_value = (
            [
                {"id": 1, "content": "Todo 1", "status": "active"},
                {"id": 2, "content": "Todo 2", "status": "completed"}
            ],
            None
        )
        mock_client_class.return_value = mock_client
        
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "todos", "list",
                "--project-id", "789",
                "--todo-set-id", "456",
                "--account-id", "123456"
            ]
        )
        
        assert result.exit_code == 0
        assert "Todo 1" in result.output

    @patch('basecamp_cli.cli.BasecampAPIClient')
    def test_todos_create(self, mock_client_class):
        """Test todos create command."""
        mock_client = Mock()
        mock_client.create_todo.return_value = {
            "id": 1,
            "content": "New Todo",
            "status": "active"
        }
        mock_client_class.return_value = mock_client
        
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "todos", "create",
                "--project-id", "789",
                "--todo-set-id", "456",
                "--content", "New Todo",
                "--account-id", "123456"
            ]
        )
        
        assert result.exit_code == 0
        assert "New Todo" in result.output
        mock_client.create_todo.assert_called_once()

    @patch('basecamp_cli.cli.BasecampAPIClient')
    def test_projects_list_error(self, mock_client_class):
        """Test projects list command with API error."""
        from basecamp_cli.api_client import BasecampAPIError
        
        mock_client = Mock()
        mock_client.get_projects.side_effect = BasecampAPIError("API Error")
        mock_client_class.return_value = mock_client
        
        runner = CliRunner()
        result = runner.invoke(cli, ["projects", "list", "--account-id", "123456"])
        
        assert result.exit_code != 0
        assert "Error" in result.output

    @patch('basecamp_cli.cli.BasecampAPIClient')
    @patch('basecamp_cli.cli.Config')
    def test_projects_list_with_default_account_id(self, mock_config_class, mock_client_class):
        """Test projects list command using default account ID from config."""
        mock_config = Mock()
        mock_config.get_account_id.return_value = 123456
        mock_config_class.return_value = mock_config
        
        mock_client = Mock()
        mock_client.get_projects.return_value = (
            [{"id": 1, "name": "Project 1", "description": "Desc 1"}],
            None
        )
        mock_client_class.return_value = mock_client
        
        runner = CliRunner()
        result = runner.invoke(cli, ["projects", "list"])
        
        assert result.exit_code == 0
        assert "Project 1" in result.output
        mock_client_class.assert_called_once_with(account_id=123456)

    @patch('basecamp_cli.cli.BasecampAPIClient')
    @patch('basecamp_cli.cli.Config')
    def test_projects_list_without_account_id_error(self, mock_config_class, mock_client_class):
        """Test projects list command fails when account ID is not provided and not configured."""
        mock_config = Mock()
        mock_config.get_account_id.return_value = None
        mock_config_class.return_value = mock_config
        
        runner = CliRunner()
        result = runner.invoke(cli, ["projects", "list"])
        
        assert result.exit_code != 0
        assert "Account ID is required" in result.output
