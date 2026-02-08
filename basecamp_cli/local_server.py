"""Simple local HTTP server for OAuth2 callback."""

import http.server
import socketserver
import urllib.parse
from typing import Optional


class OAuthCallbackHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler for OAuth2 callback."""

    authorization_code: Optional[str] = None

    def do_GET(self):
        """Handle GET request and extract authorization code."""
        parsed_path = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_path.query)

        if "code" in query_params:
            OAuthCallbackHandler.authorization_code = query_params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"""
                <html>
                <head><title>Authorization Successful</title></head>
                <body>
                    <h1>Authorization Successful!</h1>
                    <p>You can close this window and return to the terminal.</p>
                    <p>Authorization code: <strong>"""
                + OAuthCallbackHandler.authorization_code.encode()
                + b"""</strong></p>
                </body>
                </html>
                """
            )
        elif "error" in query_params:
            error = query_params["error"][0]
            error_description = query_params.get("error_description", [""])[0]
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                f"""
                <html>
                <head><title>Authorization Failed</title></head>
                <body>
                    <h1>Authorization Failed</h1>
                    <p>Error: {error}</p>
                    <p>Description: {error_description}</p>
                </body>
                </html>
                """.encode()
            )
        else:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"""
                <html>
                <head><title>Waiting for Authorization</title></head>
                <body>
                    <h1>Waiting for authorization...</h1>
                    <p>Please authorize the application in the other window.</p>
                </body>
                </html>
                """
            )

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def start_local_server(port: int = 8080) -> str:
    """Start a local HTTP server to receive OAuth2 callback.

    Args:
        port: Port number to listen on (default: 8080)

    Returns:
        The authorization code received from the callback
    """
    OAuthCallbackHandler.authorization_code = None

    with socketserver.TCPServer(("", port), OAuthCallbackHandler) as httpd:
        httpd.timeout = 300  # 5 minute timeout
        httpd.handle_request()

    return OAuthCallbackHandler.authorization_code or ""
