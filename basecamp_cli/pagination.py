"""Pagination utilities for interactive CLI navigation."""

import sys
import click
from typing import Callable, List, Dict, Any, Optional, Tuple


def handle_pagination(
    items: List[Dict[str, Any]],
    next_page_url: Optional[str],
    fetch_next_page: Callable[[str], Tuple[List[Dict[str, Any]], Optional[str]]],
    format_func: Callable[[List[Dict[str, Any]]], str],
    all_pages: bool = False,
    interactive: bool = True
) -> List[Dict[str, Any]]:
    """Handle pagination with interactive keyboard navigation.

    Args:
        items: Current page of items
        next_page_url: URL for next page (if available)
        fetch_next_page: Function to fetch next page, takes URL and returns (items, next_url)
        format_func: Function to format items for display
        all_pages: If True, automatically fetch all pages without interaction
        interactive: If True, enable interactive pagination (only for table format)

    Returns:
        Complete list of all items (from all pages fetched)
    """
    all_items = items.copy()
    current_next_url = next_page_url

    # If --all-pages is set, fetch everything automatically
    if all_pages:
        while current_next_url:
            click.echo(f"Loading more items... ({len(all_items)} so far)", err=True)
            next_items, current_next_url = fetch_next_page(current_next_url)
            all_items.extend(next_items)
        return all_items

    # If no more pages, return what we have
    if not current_next_url:
        return all_items

    # Non-interactive mode (for json/plain formats) - just return first page
    if not interactive:
        return all_items

    # Interactive pagination (for table format)
    # Display current page
    click.echo(format_func(all_items))
    
    # Show pagination prompt
    while current_next_url:
        click.echo(f"\nShowing {len(all_items)} item(s). More pages available.", err=True)
        choice = click.prompt(
            "Press Enter to load next page, 'a' to load all pages, or 'q' to quit",
            default="",
            show_default=False
        ).strip().lower()

        if choice == 'q':
            break
        elif choice == 'a':
            # Load all remaining pages
            while current_next_url:
                click.echo(f"Loading more items... ({len(all_items)} so far)", err=True)
                next_items, current_next_url = fetch_next_page(current_next_url)
                all_items.extend(next_items)
            # Display final result
            click.echo(format_func(all_items))
            break
        elif choice == '':
            # Load next page
            next_items, current_next_url = fetch_next_page(current_next_url)
            all_items.extend(next_items)
            click.echo(format_func(next_items))
        else:
            click.echo("Invalid choice. Press Enter, 'a', or 'q'.", err=True)
            continue

    return all_items
