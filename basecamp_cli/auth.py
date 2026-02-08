"""OAuth2 authentication for Basecamp CLI."""

import webbrowser
import click
from typing import Optional, Dict, Any
from urllib.parse import urlencode

from .config import Config
from .token_manager import TokenManager
import requests


class AuthHandler:
    """Handles OAuth2 authentication flow."""

    AUTHORIZATION_URL = "https://launchpad.37signals.com/authorization/new"
    TOKEN_URL = "https://launchpad.37signals.com/authorization/token"

    def __init__(self):
        """Initialize authentication handler."""
        self.config = Config()

    def get_authorization_url(self, client_id: str, redirect_uri: str, account_id: Optional[int] = None) -> str:
        """Generate OAuth2 authorization URL.

        Args:
            client_id: OAuth2 client ID
            redirect_uri: OAuth2 redirect URI
            account_id: Basecamp account ID (optional)

        Returns:
            Authorization URL
        """
        params = {
            "type": "web_server",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
        }
        if account_id:
            params["account_id"] = str(account_id)

        query_string = urlencode(params)
        return f"{self.AUTHORIZATION_URL}?{query_string}"

    def exchange_code_for_token(
        self, authorization_code: str, client_id: str, client_secret: str, redirect_uri: str
    ) -> Dict[str, Any]:
        """Exchange authorization code for access token.

        Args:
            authorization_code: Authorization code from OAuth2 flow
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            redirect_uri: OAuth2 redirect URI

        Returns:
            Token response dictionary
        """
        data = {
            "type": "web_server",
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "code": authorization_code,
        }

        try:
            response = requests.post(self.TOKEN_URL, data=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            click.echo(f"Error exchanging authorization code: {e}", err=True)
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_data = e.response.json()
                    click.echo(f"Error details: {error_data}", err=True)
                except ValueError:
                    pass
            raise

    def authenticate(self, account_id: Optional[int] = None) -> None:
        """Perform OAuth2 authentication flow.

        Args:
            account_id: Basecamp account ID (optional)
        """
        oauth_config = self.config.get_oauth_config()
        if not oauth_config:
            click.echo("OAuth2 not configured. Please run 'basecamp configure' first.", err=True)
            return

        # Get account_id from config if not provided
        if account_id is None:
            account_id = self.config.get_account_id()
        
        # Save account_id if provided or if we got it from config
        if account_id is not None:
            self.config.set_account_id(account_id)
            click.echo(f"Account ID {account_id} saved as default.")
        
        # Create TokenManager with the correct account_id (as string)
        account_id_str = str(account_id) if account_id else "default"
        token_manager = TokenManager(account_id=account_id_str)

        client_id = oauth_config["client_id"]
        client_secret = oauth_config["client_secret"]
        redirect_uri = oauth_config.get("redirect_uri", "urn:ietf:wg:oauth:2.0:oob")

        # Warn if using OOB redirect (known browser compatibility issues)
        if redirect_uri == "urn:ietf:wg:oauth:2.0:oob":
            click.echo(
                "⚠️  Warning: OOB redirect URI may not work in modern browsers.",
                err=True
            )
            click.echo(
                "   If you see 'scheme does not have a registered handler' error,",
                err=True
            )
            click.echo(
                "   please use localhost redirect instead:",
                err=True
            )
            click.echo(
                "   1. Register 'http://localhost:8080/callback' in Basecamp Launchpad",
                err=True
            )
            click.echo(
                "   2. Run: basecamp configure --redirect-uri http://localhost:8080/callback",
                err=True
            )
            click.echo()

        # Generate authorization URL
        auth_url = self.get_authorization_url(client_id, redirect_uri, account_id)

        click.echo("Opening browser for authentication...")
        click.echo(f"If browser doesn't open, visit: {auth_url}")

        try:
            webbrowser.open(auth_url)
        except Exception:
            pass  # Browser opening failed, user can manually visit URL

        # Get authorization code from user
        if redirect_uri == "urn:ietf:wg:oauth:2.0:oob":
            click.echo("\n⚠️  OOB Redirect Flow:")
            click.echo("   Modern browsers cannot handle 'urn:' scheme redirects.")
            click.echo("   After clicking 'Allow access', you may see an error in the browser console.")
            click.echo("\n   To get the authorization code:")
            click.echo("   1. Check the browser console - the code may be in the error message")
            click.echo("   2. Look at the page URL - it may contain '?code=...' or '#code=...'")
            click.echo("   3. Check the page content - the code might be displayed")
            click.echo("   4. If you see 'urn:ietf:wg:oauth:2.0:oob?code=XXXXX' in console,")
            click.echo("      extract the code part (everything after 'code=')")
            click.echo("\n   Recommended: Switch to localhost redirect for better reliability.")
            authorization_code = click.prompt("\nEnter the authorization code", type=str)
        else:
            click.echo(f"\nAfter authorizing, you'll be redirected to: {redirect_uri}")
            click.echo("Check the redirect URL for the 'code' parameter.")
            authorization_code = click.prompt("Enter the authorization code from the redirect URL", type=str)

        # Exchange code for token
        try:
            token_response = self.exchange_code_for_token(
                authorization_code, client_id, client_secret, redirect_uri
            )

            access_token = token_response.get("access_token")
            refresh_token = token_response.get("refresh_token")
            expires_in = token_response.get("expires_in")

            if access_token:
                token_manager.store_tokens(access_token, refresh_token, expires_in)
                click.echo("Authentication successful! Tokens stored securely.")
            else:
                click.echo("Error: No access token in response", err=True)
        except Exception as e:
            click.echo(f"Authentication failed: {e}", err=True)
            raise
