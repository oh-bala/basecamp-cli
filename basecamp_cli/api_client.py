"""Basecamp API client."""

import requests
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urljoin, urlparse, parse_qs
import re
import click

from .token_manager import TokenManager
from .config import Config


class BasecampAPIError(Exception):
    """Base exception for Basecamp API errors."""

    pass


class BasecampAPIClient:
    """Client for interacting with Basecamp API."""

    BASE_URL = "https://3.basecampapi.com"

    def __init__(self, account_id: Optional[int] = None, token_manager: Optional[TokenManager] = None):
        """Initialize Basecamp API client.

        Args:
            account_id: Basecamp account ID
            token_manager: TokenManager instance (creates default if not provided)
        """
        self.account_id = account_id
        self.token_manager = token_manager or TokenManager()
        self.config = Config()

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for API requests.

        Returns:
            Dictionary of HTTP headers
        """
        access_token = self.token_manager.get_access_token()
        if not access_token:
            raise BasecampAPIError("No access token available. Please authenticate first.")

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "User-Agent": "Basecamp CLI (basecamp-cli/0.1.0)",
        }
        return headers

    def _parse_link_header(self, link_header: Optional[str]) -> Dict[str, str]:
        """Parse Link header to extract pagination URLs.

        Args:
            link_header: Link header value from response

        Returns:
            Dictionary mapping rel types to URLs (e.g., {'next': '...', 'prev': '...'})
        """
        if not link_header:
            return {}

        links = {}
        # Parse Link header format: <url>; rel="type", <url>; rel="type"
        pattern = r'<([^>]+)>;\s*rel="([^"]+)"'
        matches = re.findall(pattern, link_header)

        for url, rel in matches:
            links[rel] = url

        return links

    def _make_request(
        self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None, return_response: bool = False
    ) -> Any:
        """Make an HTTP request to the Basecamp API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (relative to base URL)
            data: Request body data (for POST/PUT)
            params: Query parameters
            return_response: If True, return tuple of (data, response), else just data

        Returns:
            JSON response data (can be dict, list, or other JSON-serializable types)
            If return_response=True, returns tuple of (data, response)

        Raises:
            BasecampAPIError: If the request fails
        """
        url = urljoin(self.BASE_URL, endpoint)
        headers = self._get_headers()

        try:
            response = requests.request(
                method=method, url=url, headers=headers, json=data, params=params
            )
            response.raise_for_status()

            # Handle empty responses
            if response.status_code == 204 or not response.content:
                if return_response:
                    return {}, response
                return {}

            data = response.json()
            if return_response:
                return data, response
            return data
        except requests.exceptions.HTTPError as e:
            error_msg = f"API request failed: {e}"
            if e.response is not None:
                try:
                    error_data = e.response.json()
                    # Try to extract error message from common error response formats
                    if isinstance(error_data, dict):
                        error_msg = (
                            error_data.get("error")
                            or error_data.get("message")
                            or error_data.get("errors")
                            or error_msg
                        )
                        # If errors is a list or dict, format it nicely
                        if isinstance(error_msg, (list, dict)) and error_msg != error_data.get("errors"):
                            error_msg = str(error_msg)
                except (ValueError, AttributeError):
                    # Response is not JSON or doesn't have expected structure
                    if e.response.text:
                        error_msg = f"{error_msg}: {e.response.text[:200]}"
            raise BasecampAPIError(error_msg) from e
        except requests.exceptions.RequestException as e:
            raise BasecampAPIError(f"Request failed: {e}") from e

    def get_accounts(self) -> List[Dict[str, Any]]:
        """Get list of accounts the user has access to.

        Note: Basecamp API v3 doesn't have a direct accounts endpoint.
        Account information is typically obtained from the OAuth response
        or by accessing projects. This method is kept for future API support.

        Returns:
            List of account dictionaries
        """
        # Basecamp API v3 doesn't provide a direct accounts endpoint
        # Accounts are typically identified by account_id in project URLs
        # For now, return empty list - this can be enhanced when API supports it
        return []

    def get_projects(
        self, 
        account_id: Optional[int] = None, 
        all_pages: bool = False,
        page_url: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Get list of projects.

        Args:
            account_id: Account ID (uses instance account_id if not provided)
            all_pages: If True, fetch all pages automatically
            page_url: Specific page URL to fetch (for pagination)

        Returns:
            Tuple of (list of project dictionaries, next_page_url)
        """
        account_id = account_id or self.account_id
        if not account_id:
            raise BasecampAPIError("Account ID is required")

        if page_url:
            # Extract endpoint from full URL
            parsed = urlparse(page_url)
            endpoint = parsed.path + ("?" + parsed.query if parsed.query else "")
        else:
            endpoint = f"/{account_id}/projects.json"

        data, response = self._make_request("GET", endpoint, return_response=True)
        
        # Parse pagination links
        link_header = response.headers.get("Link", "")
        links = self._parse_link_header(link_header)
        next_page_url = links.get("next")

        # Ensure data is a list
        if not isinstance(data, list):
            data = []

        # If all_pages is True, fetch all remaining pages
        if all_pages and next_page_url:
            all_data = data.copy()
            while next_page_url:
                parsed = urlparse(next_page_url)
                next_endpoint = parsed.path + ("?" + parsed.query if parsed.query else "")
                next_data, next_response = self._make_request("GET", next_endpoint, return_response=True)
                if isinstance(next_data, list):
                    all_data.extend(next_data)
                else:
                    all_data.append(next_data)
                
                next_link_header = next_response.headers.get("Link", "")
                next_links = self._parse_link_header(next_link_header)
                next_page_url = next_links.get("next")
            
            return all_data, None

        return data, next_page_url

    def get_project(self, project_id: int, account_id: Optional[int] = None) -> Dict[str, Any]:
        """Get a specific project.

        Args:
            project_id: Project ID
            account_id: Account ID (uses instance account_id if not provided)

        Returns:
            Project dictionary
        """
        account_id = account_id or self.account_id
        if not account_id:
            raise BasecampAPIError("Account ID is required")

        endpoint = f"/{account_id}/projects/{project_id}.json"
        return self._make_request("GET", endpoint)

    def create_project(
        self, name: str, description: Optional[str] = None, account_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a new project.

        Args:
            name: Project name
            description: Project description (optional)
            account_id: Account ID (uses instance account_id if not provided)

        Returns:
            Created project dictionary
        """
        account_id = account_id or self.account_id
        if not account_id:
            raise BasecampAPIError("Account ID is required")

        data = {"name": name}
        if description:
            data["description"] = description

        endpoint = f"/{account_id}/projects.json"
        return self._make_request("POST", endpoint, data=data)

    def update_project(
        self,
        project_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        account_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Update a project.

        Args:
            project_id: Project ID
            name: New project name (optional)
            description: New project description (optional)
            account_id: Account ID (uses instance account_id if not provided)

        Returns:
            Updated project dictionary
        """
        account_id = account_id or self.account_id
        if not account_id:
            raise BasecampAPIError("Account ID is required")

        data = {}
        if name:
            data["name"] = name
        if description:
            data["description"] = description

        endpoint = f"/{account_id}/projects/{project_id}.json"
        return self._make_request("PUT", endpoint, data=data)

    def delete_project(self, project_id: int, account_id: Optional[int] = None) -> None:
        """Delete a project.

        Args:
            project_id: Project ID
            account_id: Account ID (uses instance account_id if not provided)
        """
        account_id = account_id or self.account_id
        if not account_id:
            raise BasecampAPIError("Account ID is required")

        endpoint = f"/{account_id}/projects/{project_id}.json"
        self._make_request("DELETE", endpoint)

    def get_todos(
        self, 
        project_id: int, 
        todo_set_id: int, 
        account_id: Optional[int] = None,
        all_pages: bool = False,
        page_url: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Get todos from a todo set.

        Args:
            project_id: Project ID
            todo_set_id: Todo set ID
            account_id: Account ID (uses instance account_id if not provided)
            all_pages: If True, fetch all pages automatically
            page_url: Specific page URL to fetch (for pagination)

        Returns:
            Tuple of (list of todo dictionaries, next_page_url)
        """
        account_id = account_id or self.account_id
        if not account_id:
            raise BasecampAPIError("Account ID is required")

        if page_url:
            # Extract endpoint from full URL
            parsed = urlparse(page_url)
            endpoint = parsed.path + ("?" + parsed.query if parsed.query else "")
        else:
            endpoint = f"/{account_id}/projects/{project_id}/todosets/{todo_set_id}/todos.json"

        data, response = self._make_request("GET", endpoint, return_response=True)
        
        # Parse pagination links
        link_header = response.headers.get("Link", "")
        links = self._parse_link_header(link_header)
        next_page_url = links.get("next")

        # Ensure data is a list
        if not isinstance(data, list):
            data = []

        # If all_pages is True, fetch all remaining pages
        if all_pages and next_page_url:
            all_data = data.copy()
            while next_page_url:
                parsed = urlparse(next_page_url)
                next_endpoint = parsed.path + ("?" + parsed.query if parsed.query else "")
                next_data, next_response = self._make_request("GET", next_endpoint, return_response=True)
                if isinstance(next_data, list):
                    all_data.extend(next_data)
                else:
                    all_data.append(next_data)
                
                next_link_header = next_response.headers.get("Link", "")
                next_links = self._parse_link_header(next_link_header)
                next_page_url = next_links.get("next")
            
            return all_data, None

        return data, next_page_url

    def create_todo(
        self,
        project_id: int,
        todo_set_id: int,
        content: str,
        assignee_ids: Optional[List[int]] = None,
        account_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Create a new todo.

        Args:
            project_id: Project ID
            todo_set_id: Todo set ID
            content: Todo content
            assignee_ids: List of assignee user IDs (optional)
            account_id: Account ID (uses instance account_id if not provided)

        Returns:
            Created todo dictionary
        """
        account_id = account_id or self.account_id
        if not account_id:
            raise BasecampAPIError("Account ID is required")

        data = {"content": content}
        if assignee_ids:
            data["assignee_ids"] = assignee_ids

        endpoint = f"/{account_id}/projects/{project_id}/todosets/{todo_set_id}/todos.json"
        return self._make_request("POST", endpoint, data=data)

    def get_recordings(
        self,
        recording_type: str,
        account_id: Optional[int] = None,
        bucket: Optional[str] = None,
        status: Optional[str] = None,
        sort: Optional[str] = None,
        direction: Optional[str] = None,
        all_pages: bool = False,
        page_url: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Get recordings of a specific type.

        Args:
            recording_type: Type of recording (Comment, Document, Kanban::Card, Kanban::Step,
                           Message, Question::Answer, Schedule::Entry, Todo, Todolist, Upload, Vault)
            account_id: Account ID (uses instance account_id if not provided)
            bucket: Single or comma-separated list of project IDs (optional)
            status: Status filter: 'active', 'archived', or 'trashed' (optional, default: 'active')
            sort: Sort field: 'created_at' or 'updated_at' (optional, default: 'created_at')
            direction: Sort direction: 'desc' or 'asc' (optional, default: 'desc')
            all_pages: If True, fetch all pages automatically
            page_url: Specific page URL to fetch (for pagination)

        Returns:
            Tuple of (list of recording dictionaries, next_page_url)
        """
        account_id = account_id or self.account_id
        if not account_id:
            raise BasecampAPIError("Account ID is required")

        params = {"type": recording_type}
        if bucket:
            params["bucket"] = bucket
        if status:
            params["status"] = status
        if sort:
            params["sort"] = sort
        if direction:
            params["direction"] = direction

        if page_url:
            # Extract endpoint from full URL (params are already in URL)
            parsed = urlparse(page_url)
            endpoint = parsed.path
            if parsed.query:
                endpoint += "?" + parsed.query
            # Don't pass params separately when using page_url
            data, response = self._make_request("GET", endpoint, return_response=True)
        else:
            endpoint = f"/{account_id}/projects/recordings.json"
            data, response = self._make_request("GET", endpoint, params=params, return_response=True)
        
        # Parse pagination links
        link_header = response.headers.get("Link", "")
        links = self._parse_link_header(link_header)
        next_page_url = links.get("next")

        # Ensure data is a list
        if not isinstance(data, list):
            data = []

        # If all_pages is True, fetch all remaining pages
        if all_pages and next_page_url:
            all_data = data.copy()
            while next_page_url:
                parsed = urlparse(next_page_url)
                next_endpoint = parsed.path + ("?" + parsed.query if parsed.query else "")
                next_data, next_response = self._make_request("GET", next_endpoint, return_response=True)
                if isinstance(next_data, list):
                    all_data.extend(next_data)
                else:
                    all_data.append(next_data)
                
                next_link_header = next_response.headers.get("Link", "")
                next_links = self._parse_link_header(next_link_header)
                next_page_url = next_links.get("next")
            
            return all_data, None

        return data, next_page_url

    def trash_recording(self, project_id: int, recording_id: int, account_id: Optional[int] = None) -> None:
        """Trash a recording.

        Args:
            project_id: Project ID (bucket ID)
            recording_id: Recording ID
            account_id: Account ID (uses instance account_id if not provided)
        """
        account_id = account_id or self.account_id
        if not account_id:
            raise BasecampAPIError("Account ID is required")

        endpoint = f"/{account_id}/buckets/{project_id}/recordings/{recording_id}/status/trashed.json"
        self._make_request("PUT", endpoint)

    def archive_recording(self, project_id: int, recording_id: int, account_id: Optional[int] = None) -> None:
        """Archive a recording.

        Args:
            project_id: Project ID (bucket ID)
            recording_id: Recording ID
            account_id: Account ID (uses instance account_id if not provided)
        """
        account_id = account_id or self.account_id
        if not account_id:
            raise BasecampAPIError("Account ID is required")

        endpoint = f"/{account_id}/buckets/{project_id}/recordings/{recording_id}/status/archived.json"
        self._make_request("PUT", endpoint)

    def unarchive_recording(self, project_id: int, recording_id: int, account_id: Optional[int] = None) -> None:
        """Unarchive a recording (mark as active).

        Args:
            project_id: Project ID (bucket ID)
            recording_id: Recording ID
            account_id: Account ID (uses instance account_id if not provided)
        """
        account_id = account_id or self.account_id
        if not account_id:
            raise BasecampAPIError("Account ID is required")

        endpoint = f"/{account_id}/buckets/{project_id}/recordings/{recording_id}/status/active.json"
        self._make_request("PUT", endpoint)

    def get_search_metadata(self, account_id: Optional[int] = None) -> Dict[str, Any]:
        """Get search metadata with valid filter options.

        Args:
            account_id: Account ID (uses instance account_id if not provided)

        Returns:
            Dictionary containing search metadata (recording_search_types, file_search_types, etc.)
        """
        account_id = account_id or self.account_id
        if not account_id:
            raise BasecampAPIError("Account ID is required")

        endpoint = f"/{account_id}/searches/metadata.json"
        return self._make_request("GET", endpoint)

    def search_recordings(
        self,
        query: str,
        account_id: Optional[int] = None,
        recording_type: Optional[str] = None,
        bucket_id: Optional[int] = None,
        creator_id: Optional[int] = None,
        file_type: Optional[str] = None,
        exclude_chat: bool = False,
        page: int = 1,
        per_page: int = 50,
        all_pages: bool = False
    ) -> Tuple[List[Dict[str, Any]], Optional[int]]:
        """Search recordings across the account.

        Args:
            query: Search query string (required)
            account_id: Account ID (uses instance account_id if not provided)
            recording_type: Filter by recording type (optional)
            bucket_id: Filter by project ID (optional)
            creator_id: Filter by creator person ID (optional)
            file_type: Filter attachments by type (optional)
            exclude_chat: Exclude chat results (default: False)
            page: Page number for pagination (default: 1)
            per_page: Number of results per page (default: 50)
            all_pages: If True, fetch all pages automatically

        Returns:
            Tuple of (list of recording dictionaries, next_page_number or None)
        """
        account_id = account_id or self.account_id
        if not account_id:
            raise BasecampAPIError("Account ID is required")

        params = {"q": query, "page": page, "per_page": per_page}
        if recording_type:
            params["type"] = recording_type
        if bucket_id:
            params["bucket_id"] = bucket_id
        if creator_id:
            params["creator_id"] = creator_id
        if file_type:
            params["file_type"] = file_type
        if exclude_chat:
            params["exclude_chat"] = 1

        endpoint = f"/{account_id}/search.json"
        data, response = self._make_request("GET", endpoint, params=params, return_response=True)

        # Ensure data is a list
        if not isinstance(data, list):
            data = []

        # Determine next page
        # Basecamp search uses page/per_page pagination, not Link headers
        # If we got fewer results than per_page, we're on the last page
        next_page = None
        if len(data) >= per_page:
            next_page = page + 1

        # If all_pages is True, fetch all remaining pages
        if all_pages and next_page:
            all_data = data.copy()
            current_page = next_page
            while True:
                params["page"] = current_page
                next_data, _ = self._make_request("GET", endpoint, params=params, return_response=True)
                if not isinstance(next_data, list) or len(next_data) == 0:
                    break
                all_data.extend(next_data)
                if len(next_data) < per_page:
                    break
                current_page += 1
            
            return all_data, None

        return data, next_page

    def get_people(
        self,
        account_id: Optional[int] = None,
        all_pages: bool = False,
        page_url: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Get all people visible to the current user.

        Args:
            account_id: Account ID (uses instance account_id if not provided)
            all_pages: If True, fetch all pages automatically
            page_url: Specific page URL to fetch (for pagination)

        Returns:
            Tuple of (list of people dictionaries, next_page_url)
        """
        account_id = account_id or self.account_id
        if not account_id:
            raise BasecampAPIError("Account ID is required")

        if page_url:
            # Extract endpoint from full URL
            parsed = urlparse(page_url)
            endpoint = parsed.path + ("?" + parsed.query if parsed.query else "")
        else:
            endpoint = f"/{account_id}/people.json"

        data, response = self._make_request("GET", endpoint, return_response=True)
        
        # Parse pagination links
        link_header = response.headers.get("Link", "")
        links = self._parse_link_header(link_header)
        next_page_url = links.get("next")

        # Ensure data is a list
        if not isinstance(data, list):
            data = []

        # If all_pages is True, fetch all remaining pages
        if all_pages and next_page_url:
            all_data = data.copy()
            while next_page_url:
                parsed = urlparse(next_page_url)
                next_endpoint = parsed.path + ("?" + parsed.query if parsed.query else "")
                next_data, next_response = self._make_request("GET", next_endpoint, return_response=True)
                if isinstance(next_data, list):
                    all_data.extend(next_data)
                else:
                    all_data.append(next_data)
                
                next_link_header = next_response.headers.get("Link", "")
                next_links = self._parse_link_header(next_link_header)
                next_page_url = next_links.get("next")
            
            return all_data, None

        return data, next_page_url

    def get_project_people(
        self,
        project_id: int,
        account_id: Optional[int] = None,
        all_pages: bool = False,
        page_url: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Get all people on a project.

        Args:
            project_id: Project ID
            account_id: Account ID (uses instance account_id if not provided)
            all_pages: If True, fetch all pages automatically
            page_url: Specific page URL to fetch (for pagination)

        Returns:
            Tuple of (list of people dictionaries, next_page_url)
        """
        account_id = account_id or self.account_id
        if not account_id:
            raise BasecampAPIError("Account ID is required")

        if page_url:
            # Extract endpoint from full URL
            parsed = urlparse(page_url)
            endpoint = parsed.path + ("?" + parsed.query if parsed.query else "")
        else:
            endpoint = f"/{account_id}/projects/{project_id}/people.json"

        data, response = self._make_request("GET", endpoint, return_response=True)
        
        # Parse pagination links
        link_header = response.headers.get("Link", "")
        links = self._parse_link_header(link_header)
        next_page_url = links.get("next")

        # Ensure data is a list
        if not isinstance(data, list):
            data = []

        # If all_pages is True, fetch all remaining pages
        if all_pages and next_page_url:
            all_data = data.copy()
            while next_page_url:
                parsed = urlparse(next_page_url)
                next_endpoint = parsed.path + ("?" + parsed.query if parsed.query else "")
                next_data, next_response = self._make_request("GET", next_endpoint, return_response=True)
                if isinstance(next_data, list):
                    all_data.extend(next_data)
                else:
                    all_data.append(next_data)
                
                next_link_header = next_response.headers.get("Link", "")
                next_links = self._parse_link_header(next_link_header)
                next_page_url = next_links.get("next")
            
            return all_data, None

        return data, next_page_url

    def get_person(self, person_id: int, account_id: Optional[int] = None) -> Dict[str, Any]:
        """Get a specific person.

        Args:
            person_id: Person ID
            account_id: Account ID (uses instance account_id if not provided)

        Returns:
            Person dictionary
        """
        account_id = account_id or self.account_id
        if not account_id:
            raise BasecampAPIError("Account ID is required")

        endpoint = f"/{account_id}/people/{person_id}.json"
        return self._make_request("GET", endpoint)

    def get_my_profile(self, account_id: Optional[int] = None) -> Dict[str, Any]:
        """Get current user's personal info.

        Args:
            account_id: Account ID (uses instance account_id if not provided)

        Returns:
            Current user's profile dictionary
        """
        account_id = account_id or self.account_id
        if not account_id:
            raise BasecampAPIError("Account ID is required")

        endpoint = f"/{account_id}/my/profile.json"
        return self._make_request("GET", endpoint)

    def get_pingable_people(self, account_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all people who can be pinged.

        Args:
            account_id: Account ID (uses instance account_id if not provided)

        Returns:
            List of pingable people dictionaries

        Note: This endpoint is currently not paginated.
        """
        account_id = account_id or self.account_id
        if not account_id:
            raise BasecampAPIError("Account ID is required")

        endpoint = f"/{account_id}/circles/people.json"
        data = self._make_request("GET", endpoint)
        
        # Ensure data is a list
        if not isinstance(data, list):
            data = []
        
        return data

    def update_project_access(
        self,
        project_id: int,
        grant_ids: Optional[List[int]] = None,
        revoke_ids: Optional[List[int]] = None,
        create_people: Optional[List[Dict[str, Any]]] = None,
        account_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update who can access a project.

        Args:
            project_id: Project ID
            grant_ids: List of person IDs to grant access to (optional)
            revoke_ids: List of person IDs to revoke access from (optional)
            create_people: List of new people to create and grant access to.
                          Each dict should have 'name' and 'email_address',
                          and optionally 'title' and 'company_name' (optional)
            account_id: Account ID (uses instance account_id if not provided)

        Returns:
            Dictionary with 'granted' and 'revoked' arrays

        Raises:
            BasecampAPIError: If none of grant_ids, revoke_ids, or create_people are provided
        """
        account_id = account_id or self.account_id
        if not account_id:
            raise BasecampAPIError("Account ID is required")

        if not grant_ids and not revoke_ids and not create_people:
            raise BasecampAPIError("At least one of grant_ids, revoke_ids, or create_people must be provided")

        data = {}
        if grant_ids:
            data["grant"] = grant_ids
        if revoke_ids:
            data["revoke"] = revoke_ids
        if create_people:
            data["create"] = create_people

        endpoint = f"/{account_id}/projects/{project_id}/people/users.json"
        return self._make_request("PUT", endpoint, data=data)
