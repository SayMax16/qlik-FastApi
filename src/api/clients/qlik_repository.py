"""Qlik Sense Repository API client."""

import json
import ssl
from typing import Dict, List, Any, Optional
import httpx
import logging

from src.api.core.config import Settings
from src.api.clients.base import BaseClient
from src.api.utils.qlik_helpers import generate_xrfkey

logger = logging.getLogger(__name__)


class QlikRepositoryClient(BaseClient):
    """Client for Qlik Sense Repository API using httpx."""

    def __init__(self, settings: Settings):
        """
        Initialize Qlik Repository API client.

        Args:
            settings: Application settings containing Qlik Sense configuration
        """
        super().__init__(settings)

        # Setup SSL verification
        if self.settings.QLIK_VERIFY_SSL:
            ssl_context = ssl.create_default_context()
            cert_path, key_path, ca_path = settings.get_cert_paths()
            if ca_path.exists():
                ssl_context.load_verify_locations(str(ca_path))
        else:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

        # Setup client certificates if provided
        cert = None
        cert_path, key_path, ca_path = settings.get_cert_paths()
        if cert_path.exists() and key_path.exists():
            cert = (str(cert_path), str(key_path))

        # Create httpx client with certificates and SSL context
        self.client = httpx.Client(
            verify=ssl_context if self.settings.QLIK_VERIFY_SSL else False,
            cert=cert,
            timeout=self.settings.QLIK_REQUEST_TIMEOUT,
            headers={
                "X-Qlik-User": f"UserDirectory={self.settings.QLIK_USER_DIRECTORY}; UserId={self.settings.QLIK_USER_ID}",
                "Content-Type": "application/json",
            },
        )

    def connect(self):
        """
        Repository API uses stateless HTTP/HTTPS connections.
        This method is for interface compatibility with BaseClient.
        """
        pass

    def disconnect(self):
        """Close the HTTP client."""
        self.client.close()

    def _get_api_url(self, endpoint: str) -> str:
        """
        Get full API URL for endpoint.

        Args:
            endpoint: API endpoint path

        Returns:
            Complete URL for the endpoint
        """
        base_url = f"https://{self.settings.QLIK_SENSE_HOST}:{self.settings.QLIK_REPOSITORY_PORT}"
        return f"{base_url}/qrs/{endpoint}"

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make HTTP request to Repository API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            **kwargs: Additional arguments for httpx request

        Returns:
            Response data as dictionary
        """
        try:
            url = self._get_api_url(endpoint)

            # Generate dynamic xrfkey for each request
            xrfkey = generate_xrfkey()

            # Add xrfkey parameter to all requests
            params = kwargs.get('params', {})
            params['xrfkey'] = xrfkey
            kwargs['params'] = params

            # Add xrfkey header
            headers = kwargs.get('headers', {})
            headers['X-Qlik-Xrfkey'] = xrfkey
            kwargs['headers'] = headers

            response = self.client.request(method, url, **kwargs)
            response.raise_for_status()

            if response.headers.get("content-type", "").startswith("application/json"):
                return response.json()
            else:
                return {"raw_response": response.text}

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
        except Exception as e:
            logger.error(f"Request error: {str(e)}")
            return {"error": str(e)}

    def get_comprehensive_apps(
        self,
        limit: int = 25,
        offset: int = 0,
        name: Optional[str] = None,
        stream: Optional[str] = None,
        published: Optional[bool] = True,
        exclude_streams: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get minimal list of apps with essential fields and proper filtering/pagination.

        Args:
            limit: Maximum number of apps to return (1-50, default 25)
            offset: Number of apps to skip (for pagination)
            name: Filter by app name (case-insensitive, supports wildcards)
            stream: Filter by stream name (case-insensitive, supports wildcards)
            published: Filter by published status (None for all)
            exclude_streams: List of stream names to exclude

        Returns:
            Dictionary with apps list and pagination info
        """
        if limit is None or limit < 1:
            limit = 25
        if limit > 50:
            limit = 50
        if offset is None or offset < 0:
            offset = 0

        filters: List[str] = []
        if published is not None:
            filters.append(f"published eq {'true' if published else 'false'}")
        if name:
            raw_name = name.replace('*', '')
            safe_name = raw_name.replace("'", "''")
            filters.append(f"name so '{safe_name}'")
        if stream:
            raw_stream = stream.replace('*', '')
            safe_stream = raw_stream.replace("'", "''")
            filters.append(f"stream.name so '{safe_stream}'")

        params: Dict[str, Any] = {}
        if filters:
            params["filter"] = " and ".join(filters)
        params["orderby"] = "modifiedDate desc"

        apps_result = self._make_request("GET", "app/full", params=params)

        if isinstance(apps_result, list):
            apps = apps_result
        elif isinstance(apps_result, dict):
            if "error" in apps_result:
                apps = []
            else:
                apps = apps_result.get("data", []) or apps_result.get("apps", [])
        else:
            apps = []

        minimal_apps: List[Dict[str, Any]] = []
        for app in apps:
            try:
                is_published = bool(app.get("published", False))
                stream_name = app.get("stream", {}).get("name", "") if is_published else ""
                minimal_apps.append({
                    "guid": app.get("id", ""),
                    "name": app.get("name", ""),
                    "description": app.get("description") or "",
                    "stream": stream_name or "",
                    "modified_dttm": app.get("modifiedDate", "") or "",
                    "reload_dttm": app.get("lastReloadTime", "") or "",
                })
            except Exception:
                continue

        # Apply additional filters
        if name:
            lowered = name.lower().replace('*', '')
            minimal_apps = [a for a in minimal_apps if lowered in (a.get("name", "").lower())]
        if stream:
            lowered_stream = stream.lower().replace('*', '')
            minimal_apps = [a for a in minimal_apps if lowered_stream in (a.get("stream", "").lower())]
        if exclude_streams:
            excluded_lower = [s.lower() for s in exclude_streams]
            minimal_apps = [a for a in minimal_apps if a.get("stream", "").lower() not in excluded_lower]
        if published is not None:
            if published:
                minimal_apps = [a for a in minimal_apps if a.get("stream", "") != ""]
            else:
                minimal_apps = [a for a in minimal_apps if a.get("stream", "") == ""]

        total_found = len(minimal_apps)
        paginated_apps = minimal_apps[offset:offset + limit]

        return {
            "apps": paginated_apps,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "returned": len(paginated_apps),
                "total_found": total_found,
                "has_more": (offset + limit) < total_found,
                "next_offset": (offset + limit) if (offset + limit) < total_found else None,
            },
        }

    def get_app_by_id(self, app_id: str) -> Dict[str, Any]:
        """
        Get specific app by ID.

        Args:
            app_id: Application GUID

        Returns:
            App information dictionary
        """
        return self._make_request("GET", f"app/{app_id}")

    def get_streams(self) -> List[Dict[str, Any]]:
        """
        Get list of streams.

        Returns:
            List of stream information dictionaries
        """
        result = self._make_request("GET", "stream/full")
        return result if isinstance(result, list) else []

    def start_task(self, task_id: str) -> Dict[str, Any]:
        """
        Start a task execution.

        Note: This method is an administrative function for triggering reload tasks.

        Args:
            task_id: Task GUID

        Returns:
            Task execution result
        """
        return self._make_request("POST", f"task/{task_id}/start")

    def get_app_metadata(self, app_id: str) -> Dict[str, Any]:
        """
        Get detailed app metadata using Engine REST API.

        Args:
            app_id: Application GUID

        Returns:
            Detailed metadata dictionary
        """
        try:
            base_url = f"https://{self.settings.QLIK_SENSE_HOST}"
            url = f"{base_url}/api/v1/apps/{app_id}/data/metadata"

            # Generate xrfkey
            xrfkey = generate_xrfkey()
            params = {'xrfkey': xrfkey}

            # Add xrfkey header
            headers = {
                'X-Qlik-Xrfkey': xrfkey,
                "X-Qlik-User": f"UserDirectory={self.settings.QLIK_USER_DIRECTORY}; UserId={self.settings.QLIK_USER_ID}",
            }

            response = self.client.request("GET", url, params=params, headers=headers)
            response.raise_for_status()

            if response.headers.get("content-type", "").startswith("application/json"):
                return response.json()
            else:
                return {"raw_response": response.text}

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
        except Exception as e:
            logger.error(f"Request error: {str(e)}")
            return {"error": str(e)}

    def get_app_reload_tasks(self, app_id: str) -> List[Dict[str, Any]]:
        """
        Get reload tasks for specific app.

        Args:
            app_id: Application GUID

        Returns:
            List of reload task information dictionaries
        """
        filter_query = f"app.id eq {app_id}"
        endpoint = f"reloadtask/full?filter={filter_query}"

        result = self._make_request("GET", endpoint)
        return result if isinstance(result, list) else []

    def get_task_executions(self, task_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get execution history for a task.

        Args:
            task_id: Task GUID
            limit: Maximum number of executions to return

        Returns:
            List of task execution results
        """
        endpoint = f"executionresult/full?filter=executionId eq {task_id}&orderby=startTime desc"
        if limit:
            endpoint += f"&limit={limit}"

        result = self._make_request("GET", endpoint)
        return result if isinstance(result, list) else []

    def get_app_objects(self, app_id: str, object_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get app objects (sheets, charts, etc.).

        Args:
            app_id: Application GUID
            object_type: Optional filter by object type (e.g., "sheet", "chart")

        Returns:
            List of object information dictionaries
        """
        filter_query = f"app.id eq {app_id}"
        if object_type:
            filter_query += f" and objectType eq '{object_type}'"

        endpoint = f"app/object/full?filter={filter_query}"

        result = self._make_request("GET", endpoint)
        return result if isinstance(result, list) else []

    def get_reload_tasks_for_app(self, app_id: str) -> List[Dict[str, Any]]:
        """
        Get all reload tasks associated with an app.

        Args:
            app_id: Application GUID

        Returns:
            List of reload task information dictionaries
        """
        filter_query = f"app.id eq {app_id}"
        endpoint = f"reloadtask/full?filter={filter_query}"

        result = self._make_request("GET", endpoint)
        return result if isinstance(result, list) else []

    def close(self):
        """Close the HTTP client (alias for disconnect)."""
        self.disconnect()
