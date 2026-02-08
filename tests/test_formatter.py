"""Tests for formatter.py."""

import pytest
import json
from basecamp_cli.formatter import Formatter


class TestFormatter:
    """Test cases for Formatter class."""

    def test_format_json_single_item(self):
        """Test formatting a single item as JSON."""
        data = {"id": 1, "name": "Test Project"}
        result = Formatter.format_output(data, "json")
        parsed = json.loads(result)
        assert parsed == data

    def test_format_json_list(self):
        """Test formatting a list as JSON."""
        data = [{"id": 1, "name": "Project 1"}, {"id": 2, "name": "Project 2"}]
        result = Formatter.format_output(data, "json")
        parsed = json.loads(result)
        assert parsed == data

    def test_format_table_single_item(self):
        """Test formatting a single item as table."""
        data = {"id": 1, "name": "Test Project", "description": "Test Description"}
        result = Formatter.format_output(data, "table")
        assert "id" in result
        assert "name" in result
        assert "Test Project" in result
        assert "1" in result

    def test_format_table_list(self):
        """Test formatting a list as table."""
        data = [
            {"id": 1, "name": "Project 1"},
            {"id": 2, "name": "Project 2"}
        ]
        result = Formatter.format_output(data, "table")
        assert "id" in result
        assert "name" in result
        assert "Project 1" in result
        assert "Project 2" in result
        assert "|" in result  # Table should have separators

    def test_format_table_empty_list(self):
        """Test formatting an empty list as table."""
        data = []
        result = Formatter.format_output(data, "table")
        assert "No items found" in result

    def test_format_plain_single_item(self):
        """Test formatting a single item as plain text."""
        data = {"id": 1, "name": "Test Project"}
        result = Formatter.format_output(data, "plain")
        assert "id: 1" in result
        assert "name: Test Project" in result
        assert "\n" in result  # Should have line breaks

    def test_format_plain_list(self):
        """Test formatting a list as plain text."""
        data = [
            {"id": 1, "name": "Project 1"},
            {"id": 2, "name": "Project 2"}
        ]
        result = Formatter.format_output(data, "plain")
        assert "id: 1" in result
        assert "name: Project 1" in result
        assert "id: 2" in result
        assert "name: Project 2" in result
        assert "\n" in result  # Should have line breaks

    def test_format_plain_empty_list(self):
        """Test formatting an empty list as plain text."""
        data = []
        result = Formatter.format_output(data, "plain")
        assert "No items found" in result

    def test_format_invalid_format(self):
        """Test formatting with invalid format type."""
        data = {"id": 1}
        with pytest.raises(ValueError):
            Formatter.format_output(data, "invalid")

    def test_format_table_with_nested_data(self):
        """Test formatting table with nested dictionaries."""
        data = {
            "id": 1,
            "name": "Test",
            "metadata": {"key": "value"},
            "tags": ["tag1", "tag2"]
        }
        result = Formatter.format_output(data, "table")
        assert "id" in result
        assert "name" in result
        assert "metadata" in result

    def test_format_plain_with_nested_data(self):
        """Test formatting plain with nested dictionaries."""
        data = {
            "id": 1,
            "name": "Test",
            "metadata": {"key": "value"}
        }
        result = Formatter.format_output(data, "plain")
        assert "id" in result
        assert "name" in result
        assert "metadata" in result
