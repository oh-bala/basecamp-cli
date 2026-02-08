# Basecamp CLI

A command-line interface for interacting with the Basecamp API, similar to the AWS CLI. This tool provides OAuth2 authentication, secure token storage, and convenient commands for managing Basecamp projects and todos.

## Features

- **OAuth2 Configuration**: Easy setup and configuration of OAuth2 credentials
- **Secure Token Storage**: Uses system keyring for secure token storage
- **Account ID Management**: Configure default account ID during authentication
- **Project Management**: Create, list, get, update, and delete projects
- **Todo Management**: List and create todos in Basecamp projects
- **Recordings Management**: List, trash, archive, and unarchive recordings
- **Search**: Search across all Basecamp content with advanced filters
- **Multiple Output Formats**: JSON, table, and plain text formats (plain is default)
- **Pagination Support**: Interactive pagination for table format, automatic pagination with `--all-pages`

## Installation

### Quick Install (Recommended)

Install Basecamp CLI with a single command:

```bash
sh -c "$(curl -fsSL https://raw.githubusercontent.com/oh-bala/basecamp-cli/main/install.sh)"
```

This will:
- Check for Python 3.8+ and pip
- Clone the repository
- Install the CLI tool
- Verify the installation

**Alternative installation methods:**

With a custom repository URL:
```bash
REPO_URL=https://github.com/oh-bala/basecamp-cli.git sh -c "$(curl -fsSL https://raw.githubusercontent.com/oh-bala/basecamp-cli/main/install.sh)"
```

Download and run locally:
```bash
curl -fsSL https://raw.githubusercontent.com/oh-bala/basecamp-cli/main/install.sh -o install.sh
sh install.sh
```

### From Source

If you prefer to install manually:

```bash
# Clone the repository
git clone https://github.com/oh-bala/basecamp-cli.git
cd basecamp-cli

# Install in development mode
pip install -e .

# Or install normally
pip install .
```

### Requirements

- Python 3.8 or higher
- pip (Python package installer)
- git (for cloning the repository)
- Basecamp OAuth2 credentials (Client ID and Client Secret)

## Quick Start

### 1. Register OAuth2 Application

Before using the CLI, you need to register an OAuth2 application with Basecamp:

1. Go to [Basecamp Launchpad](https://launchpad.37signals.com/integrations)
2. Click "New integration" or "Create a new integration"
3. Fill in:
   - **Name**: Basecamp CLI (or any name)
   - **Description**: Command-line interface for Basecamp API
   - **Redirect URI**: `http://localhost:8080/callback` ⚠️ **Recommended** (OOB has browser issues)
4. Save and copy your **Client ID** and **Client Secret**

📖 **Detailed Setup Guide**: See [OAUTH_SETUP.md](OAUTH_SETUP.md) for complete instructions.

⚠️ **Important**: Use `http://localhost:8080/callback` instead of OOB redirect URI. Modern browsers cannot handle `urn:ietf:wg:oauth:2.0:oob` redirects and will show "scheme does not have a registered handler" errors.

### 2. Configure OAuth2 Settings

Configure your OAuth2 credentials:

```bash
basecamp configure
```

This will prompt you for:
- OAuth2 Client ID
- OAuth2 Client Secret
- Redirect URI (defaults to `http://localhost:8080/callback` - press Enter to use default)

**Note**: 
- The redirect URI must match what you registered in Basecamp Launchpad
- After authorization, Basecamp will redirect to `http://localhost:8080/callback?code=AUTHORIZATION_CODE`
- Copy the code from the URL and paste it when prompted

### 3. Authenticate

Authenticate with Basecamp:

```bash
basecamp auth
```

This will:
1. Open your browser for OAuth2 authorization
2. Prompt you to enter the authorization code (shown on the redirect page)
3. Store your access token securely

You can optionally specify an account ID, which will be saved as the default:

```bash
basecamp auth --account-id 123456
```

**Note**: Once you configure an account ID during authentication, you don't need to specify `--account-id` in subsequent commands. The CLI will use the configured default automatically.

### 4. Use the CLI

Once authenticated, you can use various commands:

```bash
# List projects (uses configured account ID automatically)
basecamp projects list

# Or override with a different account ID
basecamp projects list --account-id 999999

# Get project details
basecamp projects get 789

# Create a project
basecamp projects create --name "My Project" --description "Project description"

# Update a project
basecamp projects update 789 --name "Updated Name"

# Delete a project
basecamp projects delete 789

# List todos
basecamp todos list --project-id 789 --todo-set-id 456

# Create a todo
basecamp todos create --project-id 789 --todo-set-id 456 --content "Complete task"

# Search for content
basecamp search "meeting notes"

# List recordings
basecamp recordings list --type Todo
```

## Commands

### Configuration

- `basecamp configure` - Configure OAuth2 settings
- `basecamp config-path` - Show where configuration is stored
- `basecamp auth [--account-id <id>]` - Authenticate with Basecamp (optionally save account ID as default)
- `basecamp logout` - Clear stored authentication tokens

### Projects

- `basecamp projects list [--account-id <id>] [--format <format>] [--all-pages]` - List all projects
- `basecamp projects get <project-id> [--account-id <id>] [--format <format>]` - Get project details
- `basecamp projects create [--account-id <id>] [--format <format>]` - Create a new project
- `basecamp projects update <project-id> [--account-id <id>] [--format <format>]` - Update a project
- `basecamp projects delete <project-id> [--account-id <id>] [--format <format>]` - Delete a project

### Todos

- `basecamp todos list [--account-id <id>] [--format <format>] [--all-pages]` - List todos in a todo set
- `basecamp todos create [--account-id <id>] [--format <format>]` - Create a new todo

### Recordings

- `basecamp recordings list --type <type> [--bucket <ids>] [--status <status>] [--sort <field>] [--direction <dir>] [--account-id <id>] [--format <format>] [--all-pages]` - List recordings
- `basecamp recordings trash <project-id> <recording-id> [--account-id <id>] [--format <format>]` - Trash a recording
- `basecamp recordings archive <project-id> <recording-id> [--account-id <id>] [--format <format>]` - Archive a recording
- `basecamp recordings unarchive <project-id> <recording-id> [--account-id <id>] [--format <format>]` - Unarchive a recording

**Recording Types**: `Comment`, `Document`, `Kanban::Card`, `Kanban::Step`, `Message`, `Question::Answer`, `Schedule::Entry`, `Todo`, `Todolist`, `Upload`, `Vault`

### Search

- `basecamp search <query> [--type <type>] [--bucket-id <id>] [--creator-id <id>] [--file-type <type>] [--exclude-chat] [--page <n>] [--per-page <n>] [--account-id <id>] [--format <format>] [--all-pages]` - Search recordings across the account
- `basecamp search-metadata [--account-id <id>] [--format <format>]` - Get search metadata with valid filter options (use this to see available recording types and file types for filtering)

## Output Formats

Most commands support `--format` option with three choices:
- `plain` (default) - Human-readable key-value pairs, one per line
- `table` - Formatted table with columns (supports interactive pagination)
- `json` - JSON output for scripting

**Examples:**
```bash
# Plain format (default) - readable key:value pairs
basecamp projects list

# Table format - formatted columns
basecamp projects list --format table

# JSON format - for scripting
basecamp projects list --format json
```

**Plain Format Example:**
```
id: 1
name: Project 1
description: Description 1

id: 2
name: Project 2
description: Description 2
```

## Pagination

Commands that return lists support pagination:

### Default Behavior
By default, only the first page of results is returned.

### Interactive Pagination (Table Format)
When using `--format table`, you can navigate pages interactively:
- Press **Enter** to load the next page
- Press **'a'** to load all remaining pages
- Press **'q'** to quit

### Automatic Pagination
Use `--all-pages` flag to automatically load all pages:

```bash
# Load all projects automatically
basecamp projects list --all-pages

# Load all search results
basecamp search "meeting" --all-pages
```

**Note**: For `json` and `plain` formats, use `--all-pages` to load all results. Interactive pagination only works with `table` format.

## Configuration Storage

### OAuth2 Credentials and Account ID

Configuration is stored in:

```
~/.basecamp/config.json
```

**Details:**
- **Location**: `~/.basecamp/config.json` (or `$HOME/.basecamp/config.json`)
- **Format**: JSON file
- **Permissions**: `600` (read/write for owner only - secure)
- **Structure**:
  ```json
  {
    "oauth": {
      "client_id": "your_client_id",
      "client_secret": "your_client_secret",
      "redirect_uri": "http://localhost:8080/callback"
    },
    "account_id": 123456
  }
  ```

**To view config location:**
```bash
basecamp config-path
```

**Account ID**: When you run `basecamp auth --account-id <id>`, the account ID is saved as the default. All subsequent commands will use this account ID automatically unless you override it with `--account-id`.

### Access Tokens

Access tokens are stored securely using the system keyring:
- **macOS**: Keychain Access
- **Windows**: Windows Credential Manager
- **Linux**: Secret Service (GNOME Keyring, KWallet, etc.)

**Note**: Tokens are stored separately from credentials for additional security.

## Redirect URI Configuration

### Recommended: Localhost Redirect

For command-line applications, use a **localhost redirect URI**:

```
http://localhost:8080/callback
```

This is the **recommended option** because:
- ✅ Works reliably in all modern browsers
- ✅ Shows authorization code in URL (easy to copy)
- ✅ No browser compatibility issues
- ✅ Simple to use

**To use localhost redirect:**
1. Register `http://localhost:8080/callback` as the redirect URI in Basecamp Launchpad
2. Run `basecamp configure` and press Enter when prompted for redirect URI (uses default)
3. After authorization, copy the `code` parameter from the redirect URL

### ⚠️ Out-of-Band (OOB) - Not Recommended

The OOB redirect URI `urn:ietf:wg:oauth:2.0:oob` has **known browser compatibility issues**:
- ❌ Modern browsers show "scheme does not have a registered handler" errors
- ❌ Redirect doesn't work properly
- ❌ Requires manual code extraction from browser console

**If you must use OOB:**
1. Register `urn:ietf:wg:oauth:2.0:oob` in Basecamp Launchpad
2. Configure with: `basecamp configure --redirect-uri urn:ietf:wg:oauth:2.0:oob`
3. After clicking "Allow access", check browser console for the code in error messages

**Important**: The redirect URI must **exactly match** what's registered in Basecamp.

📖 **For detailed OAuth2 setup instructions**, see [OAUTH_SETUP.md](OAUTH_SETUP.md)

## Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black basecamp_cli/

# Lint code
flake8 basecamp_cli/
```

## Examples

### Account ID Management

```bash
# Set default account ID during authentication
basecamp auth --account-id 123456

# All commands now use account ID 123456 automatically
basecamp projects list
basecamp todos list --project-id 789 --todo-set-id 456

# Override default account ID for a specific command
basecamp projects list --account-id 999999
```

### Pagination Examples

```bash
# Interactive pagination (table format)
basecamp projects list --format table
# Shows first page, then prompts for next page

# Load all pages automatically
basecamp projects list --all-pages

# Load all pages in JSON format
basecamp projects list --format json --all-pages
```

### Recordings Examples

```bash
# List all Todo recordings
basecamp recordings list --type Todo

# List archived Messages from specific projects
basecamp recordings list --type Message --bucket 123,456 --status archived

# Trash a recording
basecamp recordings trash 123 789

# Archive a recording
basecamp recordings archive 123 789
```

### Search Examples

```bash
# Simple search
basecamp search "authentication"

# Search with filters
basecamp search "project" --type Document --bucket-id 123

# Search excluding chats
basecamp search "meeting" --exclude-chat

# Get search metadata to see valid filter options
# This shows available recording types and file types you can use with --type and --file-type
basecamp search-metadata

# Search with pagination
basecamp search "important" --page 2 --per-page 25

# Load all search results automatically
basecamp search "todo" --all-pages

# Search with interactive pagination (table format)
basecamp search "meeting" --format table
```

## Project Structure

```
basecamp-cli/
├── basecamp_cli/
│   ├── __init__.py
│   ├── cli.py           # Main CLI entry point
│   ├── config.py        # Configuration management
│   ├── token_manager.py # Secure token storage
│   ├── auth.py          # OAuth2 authentication
│   ├── api_client.py    # Basecamp API client
│   ├── formatter.py     # Output formatting (json, table, plain)
│   ├── pagination.py    # Pagination handling
│   └── local_server.py  # Local OAuth callback server
├── pyproject.toml       # Project configuration
├── setup.py             # Setup script
├── requirements.txt     # Python dependencies
├── install.sh           # One-line installation script
└── README.md            # This file
```

## API Reference

The CLI uses the Basecamp API v3. For more information about the API, see:
- [Basecamp API Documentation](https://github.com/basecamp/bc3-api)

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
