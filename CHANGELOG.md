# Changelog

## Fixes and Improvements

### Code Fixes

1. **Fixed `get_accounts()` method in `api_client.py`**
   - Previously used incorrect endpoint `/projects.json`
   - Updated to return empty list with documentation note that Basecamp API v3 doesn't provide a direct accounts endpoint
   - Accounts are typically identified by account_id in project URLs

2. **Fixed URL encoding in `auth.py`**
   - Replaced manual query string construction with `urllib.parse.urlencode()` for proper URL encoding
   - Ensures special characters and account IDs are properly encoded in authorization URLs

3. **Fixed return type annotation in `api_client.py`**
   - Changed `_make_request()` return type from `Dict[str, Any]` to `Any`
   - Correctly handles both dict and list responses from the API
   - Prevents type checking issues when methods return lists (e.g., `get_projects()`)

4. **Improved error handling in `api_client.py`**
   - Enhanced error message extraction from API responses
   - Now checks multiple common error response fields: `error`, `message`, `errors`
   - Better handling of non-JSON error responses
   - Includes response text in error messages when available

### Test Suite

1. **Created comprehensive test suite**
   - `tests/test_config.py` - 8 tests for configuration management
   - `tests/test_token_manager.py` - 12 tests for token storage
   - `tests/test_auth.py` - 5 tests for authentication
   - `tests/test_api_client.py` - 15+ tests for API client
   - `tests/test_cli.py` - 12+ tests for CLI commands

2. **Test infrastructure**
   - `tests/conftest.py` with reusable fixtures
   - Proper mocking of external dependencies (keyring, requests, webbrowser)
   - Temporary directory handling for configuration tests

3. **Fixed test issues**
   - Corrected `test_authenticate_success` to properly mock `requests.post` instead of instance method
   - Added test for list response handling in `_make_request`
   - Added test for `get_accounts()` method

### Documentation

1. **Added TESTING.md**
   - Guide for running tests
   - Test structure documentation
   - Coverage information

2. **Updated README.md**
   - Already comprehensive with usage examples

## Testing Status

- All Python files compile without syntax errors
- All test files compile without syntax errors
- No linter errors detected
- Test suite ready to run with pytest (requires: `pip install -e ".[dev]"`)

## Next Steps

To run the full test suite:

```bash
pip install -e ".[dev]"
pytest tests/ -v
```
