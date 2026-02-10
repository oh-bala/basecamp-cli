"""Main CLI entry point for Basecamp CLI."""

import click
import json
from typing import Optional, List, Dict, Any

from .config import Config
from .token_manager import TokenManager
from .auth import AuthHandler
from .api_client import BasecampAPIClient, BasecampAPIError
from .formatter import Formatter
from .pagination import handle_pagination


def get_account_id(account_id: Optional[int]) -> int:
    """Get account ID from CLI argument or config.
    
    Args:
        account_id: Account ID from CLI argument (optional)
        
    Returns:
        Account ID as integer
        
    Raises:
        click.Abort: If account ID is not provided and not configured
    """
    if account_id is not None:
        return account_id
    
    config = Config()
    stored_account_id = config.get_account_id()
    if stored_account_id is not None:
        return stored_account_id
    
    click.echo("Error: Account ID is required. Either provide --account-id or configure it during 'basecamp auth --account-id <ID>'.", err=True)
    raise click.Abort()


@click.group()
@click.version_option(version="0.1.0", prog_name="basecamp")
def cli():
    """Basecamp CLI - Command-line interface for Basecamp API."""
    pass


@cli.command()
@click.option("--client-id", prompt="OAuth2 Client ID", help="Basecamp OAuth2 Client ID")
@click.option("--client-secret", prompt="OAuth2 Client Secret", hide_input=True, help="Basecamp OAuth2 Client Secret")
@click.option(
    "--redirect-uri",
    default="http://localhost:8080/callback",
    help="OAuth2 Redirect URI (default: localhost - recommended)",
)
def configure(client_id: str, client_secret: str, redirect_uri: str):
    """Configure OAuth2 settings for Basecamp API.
    
    Recommended redirect URI: http://localhost:8080/callback
    (OOB redirect 'urn:ietf:wg:oauth:2.0:oob' has browser compatibility issues)
    """
    config = Config()
    
    # Warn about OOB if user tries to use it
    if redirect_uri == "urn:ietf:wg:oauth:2.0:oob":
        click.echo(
            "⚠️  Warning: OOB redirect URI has known browser compatibility issues.",
            err=True
        )
        click.echo(
            "   Modern browsers cannot handle 'urn:' scheme redirects.",
            err=True
        )
        click.echo(
            "   Recommended: Use 'http://localhost:8080/callback' instead.",
            err=True
        )
        if not click.confirm("\nDo you want to continue with OOB anyway?"):
            redirect_uri = "http://localhost:8080/callback"
            click.echo(f"Using recommended redirect URI: {redirect_uri}")
    
    config.configure_oauth(client_id, client_secret, redirect_uri)
    click.echo("OAuth2 configuration saved successfully!")
    click.echo(f"Configuration stored in: {config.config_file}")
    
    if redirect_uri.startswith("http://localhost"):
        click.echo("\n📝 Next steps:")
        click.echo(f"   1. Register this redirect URI in Basecamp Launchpad:")
        click.echo(f"      {redirect_uri}")
        click.echo("   2. After authorization, copy the 'code' parameter from the redirect URL")
        click.echo("   3. Paste it when prompted by the CLI")


@cli.command()
def config_path():
    """Show the path where configuration is stored."""
    config = Config()
    click.echo(f"Configuration directory: {config.config_dir}")
    click.echo(f"Configuration file: {config.config_file}")
    if config.config_file.exists():
        click.echo("✓ Configuration file exists")
    else:
        click.echo("✗ Configuration file does not exist (run 'basecamp configure' first)")


@cli.command()
@click.option("--account-id", type=int, help="Basecamp Account ID")
def auth(account_id: Optional[int]):
    """Authenticate with Basecamp using OAuth2."""
    auth_handler = AuthHandler()
    auth_handler.authenticate(account_id)


@cli.command()
def logout():
    """Clear stored authentication tokens."""
    token_manager = TokenManager()
    token_manager.clear_tokens()
    click.echo("Logged out successfully. Tokens cleared.")


@cli.command("tokens")
@click.option("--account-id", type=int, help="Basecamp Account ID (uses configured default if not provided)")
@click.option("--show-full", is_flag=True, help="Show full token values (default: masked)")
@click.option("--format", type=click.Choice(["json", "table", "plain"]), default="plain", help="Output format (json, table, plain)")
def get_tokens(account_id: Optional[int], show_full: bool, format: str):
    """Display stored authentication tokens."""
    # Get account ID from config if not provided
    if account_id is None:
        config = Config()
        stored_account_id = config.get_account_id()
        if stored_account_id is not None:
            account_id = stored_account_id
    
    # Use account_id string for TokenManager
    account_id_str = str(account_id) if account_id else "default"
    token_manager = TokenManager(account_id=account_id_str)
    
    tokens = token_manager.get_tokens()
    
    if not tokens:
        click.echo("No tokens found. Run 'basecamp auth' to authenticate.", err=True)
        raise click.Abort()
    
    # Prepare token data for display
    token_data = {
        "account_id": account_id_str,
        "has_access_token": bool(tokens.get("access_token")),
        "has_refresh_token": bool(tokens.get("refresh_token")),
        "is_expired": token_manager.is_token_expired(),
        "expires_at": tokens.get("expires_at"),
    }
    
    # Add token values (masked or full based on flag)
    if show_full:
        token_data["access_token"] = tokens.get("access_token")
        token_data["refresh_token"] = tokens.get("refresh_token")
    else:
        access_token = tokens.get("access_token", "")
        refresh_token = tokens.get("refresh_token", "")
        
        # Mask tokens: show first 8 and last 4 characters
        def mask_token(token: str) -> str:
            if not token:
                return None
            if len(token) <= 12:
                return "*" * len(token)
            return f"{token[:8]}...{token[-4:]}"
        
        token_data["access_token"] = mask_token(access_token)
        token_data["refresh_token"] = mask_token(refresh_token)
    
    output = Formatter.format_output(token_data, format)
    click.echo(output)


@cli.group()
def projects():
    """Manage Basecamp projects."""
    pass


@projects.command("list")
@click.option("--account-id", type=int, help="Basecamp Account ID (uses configured default if not provided)")
@click.option("--format", type=click.Choice(["json", "table", "plain"]), default="plain", help="Output format (json, table, plain)")
@click.option("--all-pages", is_flag=True, help="Automatically load all pages without interaction")
def list_projects(account_id: Optional[int], format: str, all_pages: bool):
    """List all projects in an account."""
    try:
        account_id = get_account_id(account_id)
        client = BasecampAPIClient(account_id=account_id)
        projects, next_page_url = client.get_projects(all_pages=all_pages)

        def fetch_next_page(url: str):
            return client.get_projects(page_url=url, all_pages=False)

        def format_items(items: List[Dict[str, Any]]) -> str:
            return Formatter.format_output(items, format)

        # For json/plain formats, if not --all-pages, just show first page
        # For table format, enable interactive pagination
        interactive = (format == "table" and not all_pages)

        # Handle pagination (interactive or all-pages)
        all_projects = handle_pagination(
            projects,
            next_page_url,
            fetch_next_page,
            format_items,
            all_pages=all_pages,
            interactive=interactive
        )

        # Output final result (if not already displayed interactively)
        if not interactive or all_pages:
            output = Formatter.format_output(all_projects, format)
            click.echo(output)
    except BasecampAPIError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@projects.command("get")
@click.argument("project_id", type=int)
@click.option("--account-id", type=int, help="Basecamp Account ID (uses configured default if not provided)")
@click.option("--format", type=click.Choice(["json", "table", "plain"]), default="plain", help="Output format (json, table, plain)")
def get_project(project_id: int, account_id: Optional[int], format: str):
    """Get details of a specific project."""
    try:
        account_id = get_account_id(account_id)
        client = BasecampAPIClient(account_id=account_id)
        project = client.get_project(project_id)

        output = Formatter.format_output(project, format)
        click.echo(output)
    except BasecampAPIError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@projects.command("create")
@click.option("--name", prompt="Project name", help="Project name")
@click.option("--description", help="Project description")
@click.option("--account-id", type=int, help="Basecamp Account ID (uses configured default if not provided)")
@click.option("--format", type=click.Choice(["json", "table", "plain"]), default="plain", help="Output format (json, table, plain)")
def create_project(name: str, description: Optional[str], account_id: Optional[int], format: str):
    """Create a new project."""
    try:
        account_id = get_account_id(account_id)
        client = BasecampAPIClient(account_id=account_id)
        project = client.create_project(name, description)

        output = Formatter.format_output(project, format)
        click.echo(output)
    except BasecampAPIError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@projects.command("update")
@click.argument("project_id", type=int)
@click.option("--name", help="New project name")
@click.option("--description", help="New project description")
@click.option("--account-id", type=int, help="Basecamp Account ID (uses configured default if not provided)")
@click.option("--format", type=click.Choice(["json", "table", "plain"]), default="plain", help="Output format (json, table, plain)")
def update_project(project_id: int, name: Optional[str], description: Optional[str], account_id: Optional[int], format: str):
    """Update an existing project."""
    if not name and not description:
        click.echo("Error: At least one of --name or --description must be provided", err=True)
        raise click.Abort()

    try:
        account_id = get_account_id(account_id)
        client = BasecampAPIClient(account_id=account_id)
        project = client.update_project(project_id, name, description)

        output = Formatter.format_output(project, format)
        click.echo(output)
    except BasecampAPIError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@projects.command("delete")
@click.argument("project_id", type=int)
@click.option("--account-id", type=int, help="Basecamp Account ID (uses configured default if not provided)")
@click.option("--format", type=click.Choice(["json", "table", "plain"]), default="plain", help="Output format (json, table, plain)")
@click.confirmation_option(prompt="Are you sure you want to delete this project?")
def delete_project(project_id: int, account_id: Optional[int], format: str):
    """Delete a project."""
    try:
        account_id = get_account_id(account_id)
        client = BasecampAPIClient(account_id=account_id)
        client.delete_project(project_id)
        
        result = {"status": "deleted", "project_id": project_id, "message": f"Project {project_id} deleted successfully"}
        output = Formatter.format_output(result, format)
        click.echo(output)
    except BasecampAPIError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.group()
def todos():
    """Manage todos in Basecamp projects."""
    pass


@todos.command("list")
@click.option("--project-id", type=int, required=True, help="Project ID")
@click.option("--todo-set-id", type=int, required=True, help="Todo Set ID")
@click.option("--account-id", type=int, help="Basecamp Account ID (uses configured default if not provided)")
@click.option("--format", type=click.Choice(["json", "table", "plain"]), default="plain", help="Output format (json, table, plain)")
@click.option("--all-pages", is_flag=True, help="Automatically load all pages without interaction")
def list_todos(project_id: int, todo_set_id: int, account_id: Optional[int], format: str, all_pages: bool):
    """List todos in a todo set."""
    try:
        account_id = get_account_id(account_id)
        client = BasecampAPIClient(account_id=account_id)
        todos_list, next_page_url = client.get_todos(project_id, todo_set_id, all_pages=all_pages)

        def fetch_next_page(url: str):
            return client.get_todos(project_id, todo_set_id, page_url=url, all_pages=False)

        def format_items(items: List[Dict[str, Any]]) -> str:
            return Formatter.format_output(items, format)

        # For json/plain formats, if not --all-pages, just show first page
        # For table format, enable interactive pagination
        interactive = (format == "table" and not all_pages)

        # Handle pagination (interactive or all-pages)
        all_todos = handle_pagination(
            todos_list,
            next_page_url,
            fetch_next_page,
            format_items,
            all_pages=all_pages,
            interactive=interactive
        )

        # Output final result (if not already displayed interactively)
        if not interactive or all_pages:
            output = Formatter.format_output(all_todos, format)
            click.echo(output)
    except BasecampAPIError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@todos.command("create")
@click.option("--project-id", type=int, required=True, help="Project ID")
@click.option("--todo-set-id", type=int, required=True, help="Todo Set ID")
@click.option("--content", prompt="Todo content", help="Todo content")
@click.option("--assignee-ids", help="Comma-separated list of assignee user IDs")
@click.option("--account-id", type=int, help="Basecamp Account ID (uses configured default if not provided)")
@click.option("--format", type=click.Choice(["json", "table", "plain"]), default="plain", help="Output format (json, table, plain)")
def create_todo(project_id: int, todo_set_id: int, content: str, assignee_ids: Optional[str], account_id: Optional[int], format: str):
    """Create a new todo."""
    assignee_id_list = None
    if assignee_ids:
        assignee_id_list = [int(id.strip()) for id in assignee_ids.split(",")]

    try:
        account_id = get_account_id(account_id)
        client = BasecampAPIClient(account_id=account_id)
        todo = client.create_todo(project_id, todo_set_id, content, assignee_id_list)

        output = Formatter.format_output(todo, format)
        click.echo(output)
    except BasecampAPIError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.group()
def recordings():
    """Manage recordings in Basecamp projects."""
    pass


@recordings.command("list")
@click.option("--type", "recording_type", required=True, 
              type=click.Choice([
                  "Comment", "Document", "Kanban::Card", "Kanban::Step",
                  "Message", "Question::Answer", "Schedule::Entry", 
                  "Todo", "Todolist", "Upload", "Vault"
              ]),
              help="Type of recording to list")
@click.option("--bucket", help="Single or comma-separated list of project IDs")
@click.option("--status", type=click.Choice(["active", "archived", "trashed"]), 
              default="active", help="Status filter (default: active)")
@click.option("--sort", type=click.Choice(["created_at", "updated_at"]), 
              default="created_at", help="Sort field (default: created_at)")
@click.option("--direction", type=click.Choice(["asc", "desc"]), 
              default="desc", help="Sort direction (default: desc)")
@click.option("--account-id", type=int, help="Basecamp Account ID (uses configured default if not provided)")
@click.option("--format", type=click.Choice(["json", "table", "plain"]), default="plain", help="Output format (json, table, plain)")
@click.option("--all-pages", is_flag=True, help="Automatically load all pages without interaction")
def list_recordings(recording_type: str, bucket: Optional[str], status: str, sort: str, direction: str, 
                    account_id: Optional[int], format: str, all_pages: bool):
    """List recordings of a specific type."""
    try:
        account_id = get_account_id(account_id)
        client = BasecampAPIClient(account_id=account_id)
        recordings_list, next_page_url = client.get_recordings(
            recording_type=recording_type,
            bucket=bucket,
            status=status,
            sort=sort,
            direction=direction,
            all_pages=all_pages
        )

        def fetch_next_page(url: str):
            return client.get_recordings(
                recording_type=recording_type,
                bucket=bucket,
                status=status,
                sort=sort,
                direction=direction,
                page_url=url,
                all_pages=False
            )

        def format_items(items: List[Dict[str, Any]]) -> str:
            return Formatter.format_output(items, format)

        # For json/plain formats, if not --all-pages, just show first page
        # For table format, enable interactive pagination
        interactive = (format == "table" and not all_pages)

        # Handle pagination (interactive or all-pages)
        all_recordings = handle_pagination(
            recordings_list,
            next_page_url,
            fetch_next_page,
            format_items,
            all_pages=all_pages,
            interactive=interactive
        )

        # Output final result (if not already displayed interactively)
        if not interactive or all_pages:
            output = Formatter.format_output(all_recordings, format)
            click.echo(output)
    except BasecampAPIError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@recordings.command("trash")
@click.argument("project_id", type=int)
@click.argument("recording_id", type=int)
@click.option("--account-id", type=int, help="Basecamp Account ID (uses configured default if not provided)")
@click.option("--format", type=click.Choice(["json", "table", "plain"]), default="plain", help="Output format (json, table, plain)")
def trash_recording(project_id: int, recording_id: int, account_id: Optional[int], format: str):
    """Trash a recording."""
    try:
        account_id = get_account_id(account_id)
        client = BasecampAPIClient(account_id=account_id)
        client.trash_recording(project_id, recording_id)
        
        result = {
            "status": "trashed",
            "project_id": project_id,
            "recording_id": recording_id,
            "message": f"Recording {recording_id} trashed successfully"
        }
        output = Formatter.format_output(result, format)
        click.echo(output)
    except BasecampAPIError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@recordings.command("archive")
@click.argument("project_id", type=int)
@click.argument("recording_id", type=int)
@click.option("--account-id", type=int, help="Basecamp Account ID (uses configured default if not provided)")
@click.option("--format", type=click.Choice(["json", "table", "plain"]), default="plain", help="Output format (json, table, plain)")
def archive_recording(project_id: int, recording_id: int, account_id: Optional[int], format: str):
    """Archive a recording."""
    try:
        account_id = get_account_id(account_id)
        client = BasecampAPIClient(account_id=account_id)
        client.archive_recording(project_id, recording_id)
        
        result = {
            "status": "archived",
            "project_id": project_id,
            "recording_id": recording_id,
            "message": f"Recording {recording_id} archived successfully"
        }
        output = Formatter.format_output(result, format)
        click.echo(output)
    except BasecampAPIError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@recordings.command("unarchive")
@click.argument("project_id", type=int)
@click.argument("recording_id", type=int)
@click.option("--account-id", type=int, help="Basecamp Account ID (uses configured default if not provided)")
@click.option("--format", type=click.Choice(["json", "table", "plain"]), default="plain", help="Output format (json, table, plain)")
def unarchive_recording(project_id: int, recording_id: int, account_id: Optional[int], format: str):
    """Unarchive a recording (mark as active)."""
    try:
        account_id = get_account_id(account_id)
        client = BasecampAPIClient(account_id=account_id)
        client.unarchive_recording(project_id, recording_id)
        
        result = {
            "status": "active",
            "project_id": project_id,
            "recording_id": recording_id,
            "message": f"Recording {recording_id} unarchived successfully"
        }
        output = Formatter.format_output(result, format)
        click.echo(output)
    except BasecampAPIError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


def _handle_search_pagination(client: BasecampAPIClient, query: str, recording_type: Optional[str],
                               bucket_id: Optional[int], creator_id: Optional[int], file_type: Optional[str],
                               exclude_chat: bool, page: int, per_page: int, format: str, all_pages: bool,
                               initial_results: List[Dict[str, Any]], next_page: Optional[int]):
    """Helper function to handle search pagination."""
    if all_pages and next_page:
        # Already fetched all pages in the API call
        all_results = initial_results
    elif not all_pages and next_page and format == "table":
        # Interactive pagination for table format
        all_results = initial_results.copy()
        current_page = next_page
        
        while current_page:
            click.echo(Formatter.format_output(all_results, format))
            click.echo(f"\nShowing {len(all_results)} result(s). Page {current_page - 1} of results.", err=True)
            choice = click.prompt(
                "Press Enter to load next page, 'a' to load all pages, or 'q' to quit",
                default="",
                show_default=False
            ).strip().lower()

            if choice == 'q':
                break
            elif choice == 'a':
                # Load all remaining pages
                while current_page:
                    click.echo(f"Loading more results... ({len(all_results)} so far)", err=True)
                    next_results, current_page = client.search_recordings(
                        query=query,
                        recording_type=recording_type,
                        bucket_id=bucket_id,
                        creator_id=creator_id,
                        file_type=file_type,
                        exclude_chat=exclude_chat,
                        page=current_page,
                        per_page=per_page,
                        all_pages=False
                    )
                    all_results.extend(next_results)
                break
            elif choice == '':
                # Load next page
                next_results, current_page = client.search_recordings(
                    query=query,
                    recording_type=recording_type,
                    bucket_id=bucket_id,
                    creator_id=creator_id,
                    file_type=file_type,
                    exclude_chat=exclude_chat,
                    page=current_page,
                    per_page=per_page,
                    all_pages=False
                )
                all_results.extend(next_results)
            else:
                click.echo("Invalid choice. Press Enter, 'a', or 'q'.", err=True)
                continue
        
        # Display final result
        click.echo(Formatter.format_output(all_results, format))
        return all_results
    else:
        all_results = initial_results

    # Output final result
    output = Formatter.format_output(all_results, format)
    click.echo(output)
    
    # Show pagination info for non-interactive modes
    if next_page and not all_pages and format != "table":
        click.echo(f"\nMore results available. Use --page {next_page} to see next page, or --all-pages to load all.", err=True)
    
    return all_results


@cli.group()
def people():
    """Manage people in Basecamp."""
    pass


@people.command("list")
@click.option("--project-id", type=int, help="Filter by project ID (list people on a specific project)")
@click.option("--account-id", type=int, help="Basecamp Account ID (uses configured default if not provided)")
@click.option("--format", type=click.Choice(["json", "table", "plain"]), default="plain", help="Output format (json, table, plain)")
@click.option("--all-pages", is_flag=True, help="Automatically load all pages without interaction")
def list_people(project_id: Optional[int], account_id: Optional[int], format: str, all_pages: bool):
    """List all people visible to the current user, or people on a specific project."""
    try:
        account_id = get_account_id(account_id)
        client = BasecampAPIClient(account_id=account_id)
        
        if project_id:
            people_list, next_page_url = client.get_project_people(project_id, all_pages=all_pages)
            
            def fetch_next_page(url: str):
                return client.get_project_people(project_id, page_url=url, all_pages=False)
        else:
            people_list, next_page_url = client.get_people(all_pages=all_pages)
            
            def fetch_next_page(url: str):
                return client.get_people(page_url=url, all_pages=False)

        def format_items(items: List[Dict[str, Any]]) -> str:
            return Formatter.format_output(items, format)

        # For json/plain formats, if not --all-pages, just show first page
        # For table format, enable interactive pagination
        interactive = (format == "table" and not all_pages)

        # Handle pagination (interactive or all-pages)
        all_people = handle_pagination(
            people_list,
            next_page_url,
            fetch_next_page,
            format_items,
            all_pages=all_pages,
            interactive=interactive
        )

        # Output final result (if not already displayed interactively)
        if not interactive or all_pages:
            output = Formatter.format_output(all_people, format)
            click.echo(output)
    except BasecampAPIError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@people.command("get")
@click.argument("person_id", type=int)
@click.option("--account-id", type=int, help="Basecamp Account ID (uses configured default if not provided)")
@click.option("--format", type=click.Choice(["json", "table", "plain"]), default="plain", help="Output format (json, table, plain)")
def get_person(person_id: int, account_id: Optional[int], format: str):
    """Get details of a specific person."""
    try:
        account_id = get_account_id(account_id)
        client = BasecampAPIClient(account_id=account_id)
        person = client.get_person(person_id)

        output = Formatter.format_output(person, format)
        click.echo(output)
    except BasecampAPIError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@people.command("profile")
@click.option("--account-id", type=int, help="Basecamp Account ID (uses configured default if not provided)")
@click.option("--format", type=click.Choice(["json", "table", "plain"]), default="plain", help="Output format (json, table, plain)")
def get_profile(account_id: Optional[int], format: str):
    """Get current user's personal info."""
    try:
        account_id = get_account_id(account_id)
        client = BasecampAPIClient(account_id=account_id)
        profile = client.get_my_profile()

        output = Formatter.format_output(profile, format)
        click.echo(output)
    except BasecampAPIError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@people.command("pingable")
@click.option("--account-id", type=int, help="Basecamp Account ID (uses configured default if not provided)")
@click.option("--format", type=click.Choice(["json", "table", "plain"]), default="plain", help="Output format (json, table, plain)")
def list_pingable_people(account_id: Optional[int], format: str):
    """List all people who can be pinged."""
    try:
        account_id = get_account_id(account_id)
        client = BasecampAPIClient(account_id=account_id)
        pingable_people = client.get_pingable_people()

        output = Formatter.format_output(pingable_people, format)
        click.echo(output)
    except BasecampAPIError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@people.command("grant-access")
@click.argument("project_id", type=int)
@click.option("--grant-ids", help="Comma-separated list of person IDs to grant access to")
@click.option("--revoke-ids", help="Comma-separated list of person IDs to revoke access from")
@click.option("--create", help="JSON array of new people to create and grant access to. Each person should have 'name' and 'email_address', and optionally 'title' and 'company_name'")
@click.option("--account-id", type=int, help="Basecamp Account ID (uses configured default if not provided)")
@click.option("--format", type=click.Choice(["json", "table", "plain"]), default="plain", help="Output format (json, table, plain)")
def grant_project_access(project_id: int, grant_ids: Optional[str], revoke_ids: Optional[str], create: Optional[str], account_id: Optional[int], format: str):
    """Update who can access a project. Grant access, revoke access, or create new people and grant them access."""
    if not grant_ids and not revoke_ids and not create:
        click.echo("Error: At least one of --grant-ids, --revoke-ids, or --create must be provided", err=True)
        raise click.Abort()

    grant_id_list = None
    if grant_ids:
        grant_id_list = [int(id.strip()) for id in grant_ids.split(",")]

    revoke_id_list = None
    if revoke_ids:
        revoke_id_list = [int(id.strip()) for id in revoke_ids.split(",")]

    create_people_list = None
    if create:
        try:
            create_people_list = json.loads(create)
            if not isinstance(create_people_list, list):
                click.echo("Error: --create must be a JSON array", err=True)
                raise click.Abort()
        except json.JSONDecodeError as e:
            click.echo(f"Error: Invalid JSON in --create: {e}", err=True)
            raise click.Abort()

    try:
        account_id = get_account_id(account_id)
        client = BasecampAPIClient(account_id=account_id)
        result = client.update_project_access(
            project_id,
            grant_ids=grant_id_list,
            revoke_ids=revoke_id_list,
            create_people=create_people_list
        )

        output = Formatter.format_output(result, format)
        click.echo(output)
    except BasecampAPIError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.command("search-metadata")
@click.option("--account-id", type=int, help="Basecamp Account ID (uses configured default if not provided)")
@click.option("--format", type=click.Choice(["json", "table", "plain"]), default="plain", help="Output format (json, table, plain)")
def search_metadata(account_id: Optional[int], format: str):
    """Get search metadata with valid filter options."""
    try:
        account_id = get_account_id(account_id)
        client = BasecampAPIClient(account_id=account_id)
        metadata = client.get_search_metadata()

        output = Formatter.format_output(metadata, format)
        click.echo(output)
    except BasecampAPIError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.command("search")
@click.argument("query")
@click.option("--type", "recording_type", help="Filter by recording type (use 'basecamp search-metadata' to see valid types)")
@click.option("--bucket-id", type=int, help="Filter by project ID")
@click.option("--creator-id", type=int, help="Filter by creator person ID")
@click.option("--file-type", help="Filter attachments by type (use 'basecamp search-metadata' to see valid file types)")
@click.option("--exclude-chat", is_flag=True, help="Exclude chat results")
@click.option("--page", type=int, default=1, help="Page number (default: 1)")
@click.option("--per-page", type=int, default=50, help="Results per page (default: 50)")
@click.option("--account-id", type=int, help="Basecamp Account ID (uses configured default if not provided)")
@click.option("--format", type=click.Choice(["json", "table", "plain"]), default="plain", help="Output format (json, table, plain)")
@click.option("--all-pages", is_flag=True, help="Automatically load all pages without interaction")
def search(query: str, recording_type: Optional[str], bucket_id: Optional[int], 
           creator_id: Optional[int], file_type: Optional[str], exclude_chat: bool,
           page: int, per_page: int, account_id: Optional[int], format: str, all_pages: bool):
    """Search recordings across the account."""
    try:
        account_id = get_account_id(account_id)
        client = BasecampAPIClient(account_id=account_id)
        results, next_page = client.search_recordings(
            query=query,
            recording_type=recording_type,
            bucket_id=bucket_id,
            creator_id=creator_id,
            file_type=file_type,
            exclude_chat=exclude_chat,
            page=page,
            per_page=per_page,
            all_pages=all_pages
        )

        _handle_search_pagination(
            client, query, recording_type, bucket_id, creator_id, file_type,
            exclude_chat, page, per_page, format, all_pages, results, next_page
        )
    except BasecampAPIError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
