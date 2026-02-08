"""Output formatting utilities for Basecamp CLI."""

import json
import click
from typing import Any, Dict, List, Optional, Union


class Formatter:
    """Handles output formatting for CLI commands."""

    @staticmethod
    def format_output(data: Union[Dict[str, Any], List[Dict[str, Any]]], format_type: str) -> str:
        """Format data according to the specified format type.

        Args:
            data: Data to format (dict for single item, list for multiple items)
            format_type: Format type ('json', 'table', or 'plain')

        Returns:
            Formatted string output
        """
        if format_type == "json":
            return Formatter._format_json(data)
        elif format_type == "table":
            return Formatter._format_table(data)
        elif format_type == "plain":
            return Formatter._format_plain(data)
        else:
            raise ValueError(f"Unknown format type: {format_type}")

    @staticmethod
    def _format_json(data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> str:
        """Format data as JSON."""
        return json.dumps(data, indent=2)

    @staticmethod
    def _format_table(data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> str:
        """Format data as a table."""
        if isinstance(data, list):
            if not data:
                return "No items found."
            return Formatter._format_list_table(data)
        else:
            return Formatter._format_dict_table(data)

    @staticmethod
    def _format_list_table(items: List[Dict[str, Any]]) -> str:
        """Format a list of items as a table."""
        if not items:
            return "No items found."

        # Get all unique keys from all items
        all_keys = set()
        for item in items:
            all_keys.update(item.keys())

        # Sort keys for consistent ordering (common keys first)
        common_keys = ["id", "name", "description", "content", "status", "created_at", "updated_at"]
        ordered_keys = [k for k in common_keys if k in all_keys]
        ordered_keys.extend(sorted([k for k in all_keys if k not in common_keys]))

        # Calculate column widths
        col_widths = {}
        for key in ordered_keys:
            col_widths[key] = max(
                len(str(key)),
                max((
                    len(str(item.get(key) if item.get(key) is not None else "N/A"))
                    for item in items
                ), default=0)
            )

        # Build table
        lines = []
        
        # Header
        header = " | ".join(str(key).ljust(col_widths[key]) for key in ordered_keys)
        lines.append(header)
        lines.append("-" * len(header))

        # Rows
        for item in items:
            row = " | ".join(
                str(item.get(key) if item.get(key) is not None else "N/A").ljust(col_widths[key])
                for key in ordered_keys
            )
            lines.append(row)

        return "\n".join(lines)

    @staticmethod
    def _format_dict_table(data: Dict[str, Any]) -> str:
        """Format a single dictionary as a table."""
        if not data:
            return "No data available."

        lines = []
        max_key_width = max(len(str(k)) for k in data.keys()) if data else 0

        for key, value in data.items():
            if value is None:
                value_str = "N/A"
            elif isinstance(value, (dict, list)):
                value_str = json.dumps(value, indent=2)
                # Indent multi-line values
                value_lines = value_str.split("\n")
                lines.append(f"{str(key).ljust(max_key_width)}  {value_lines[0]}")
                for line in value_lines[1:]:
                    lines.append(" " * (max_key_width + 2) + line)
                continue
            else:
                value_str = str(value)
            lines.append(f"{str(key).ljust(max_key_width)}  {value_str}")

        return "\n".join(lines)

    @staticmethod
    def _format_plain(data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> str:
        """Format data as plain text (key: value pairs, one per line)."""
        if isinstance(data, list):
            if not data:
                return "No items found."
            return Formatter._format_list_plain(data)
        else:
            return Formatter._format_dict_plain(data)

    @staticmethod
    def _format_list_plain(items: List[Dict[str, Any]]) -> str:
        """Format a list of items as key: value pairs, separated by blank lines."""
        if not items:
            return "No items found."

        # Get all unique keys from all items
        all_keys = set()
        for item in items:
            all_keys.update(item.keys())

        # Sort keys for consistent ordering
        common_keys = ["id", "name", "description", "content", "status", "created_at", "updated_at"]
        ordered_keys = [k for k in common_keys if k in all_keys]
        ordered_keys.extend(sorted([k for k in all_keys if k not in common_keys]))

        lines = []
        for idx, item in enumerate(items):
            # Add blank line between items (except before first item)
            if idx > 0:
                lines.append("")
            
            # Format each field as key: value
            for key in ordered_keys:
                value = item.get(key)
                if value is None:
                    value_str = ""
                elif isinstance(value, (dict, list)):
                    value_str = json.dumps(value, indent=2)
                    # Indent multi-line JSON values
                    value_lines = value_str.split("\n")
                    lines.append(f"{key}: {value_lines[0]}")
                    for line in value_lines[1:]:
                        lines.append(f"  {line}")
                else:
                    value_str = str(value)
                    lines.append(f"{key}: {value_str}")

        return "\n".join(lines)

    @staticmethod
    def _format_dict_plain(data: Dict[str, Any]) -> str:
        """Format a single dictionary as key: value pairs, one per line."""
        if not data:
            return "No data available."

        lines = []
        for key, value in data.items():
            if value is None:
                value_str = ""
            elif isinstance(value, (dict, list)):
                value_str = json.dumps(value, indent=2)
                # Indent multi-line JSON values
                value_lines = value_str.split("\n")
                lines.append(f"{key}: {value_lines[0]}")
                for line in value_lines[1:]:
                    lines.append(f"  {line}")
            else:
                value_str = str(value)
                lines.append(f"{key}: {value_str}")

        return "\n".join(lines)
