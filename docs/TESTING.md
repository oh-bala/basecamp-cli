# Testing Guide

## Running Tests

To run the test suite, first install the development dependencies:

```bash
pip install -e ".[dev]"
```

Then run pytest:

```bash
pytest tests/ -v
```

To run with coverage:

```bash
pytest tests/ --cov=basecamp_cli --cov-report=html
```

## Test Structure

The test suite is organized as follows:

- `tests/test_config.py` - Tests for configuration management
- `tests/test_token_manager.py` - Tests for secure token storage
- `tests/test_auth.py` - Tests for OAuth2 authentication
- `tests/test_api_client.py` - Tests for Basecamp API client
- `tests/test_cli.py` - Tests for CLI commands

## Test Coverage

The test suite covers:

1. **Configuration Management**
   - Loading and saving configuration
   - OAuth2 configuration
   - Default values and error handling

2. **Token Management**
   - Storing and retrieving tokens
   - Token expiration checking
   - Secure storage using keyring

3. **Authentication**
   - Authorization URL generation
   - Token exchange
   - Authentication flow

4. **API Client**
   - HTTP request handling
   - Error handling
   - Project operations
   - Todo operations

5. **CLI Commands**
   - All command-line operations
   - Output formatting (JSON/table)
   - Error handling

## Mocking

Tests use mocking for:
- External API calls (requests)
- Keyring operations
- Browser opening (webbrowser)
- User input (click.prompt)

## Running Specific Tests

Run a specific test file:

```bash
pytest tests/test_config.py -v
```

Run a specific test:

```bash
pytest tests/test_config.py::TestConfig::test_save_and_load -v
```
