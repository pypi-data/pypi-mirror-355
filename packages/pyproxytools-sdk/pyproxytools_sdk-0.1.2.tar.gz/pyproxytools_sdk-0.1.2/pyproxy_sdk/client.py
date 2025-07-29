# pyproxy_sdk/client.py

import requests
from requests.auth import HTTPBasicAuth

from .exceptions import (
    PyProxyError,
    PyProxyConfigurationError,
    PyProxyAlreadyExists,
    PyProxyNotFound,
    PyProxyInvalidInput,
    PyProxyServerError,
)


class PyProxyClient:
    def __init__(
        self,
        base_url: str = "",
        username: str = "",
        password: str = "",
        timeout: int = 10,
    ):
        """
        PyProxy SDK Client

        Args:
            base_url (str): Base URL of the API (e.g. http://localhost:5000)
            username (str): HTTP Basic Auth username
            password (str): HTTP Basic Auth password
            timeout (int): Timeout for requests (default: 10 seconds)
        """

        if not base_url:
            raise PyProxyConfigurationError("Base URL must be provided")
        if not username:
            raise PyProxyConfigurationError("Username must be provided")
        if not password:
            raise PyProxyConfigurationError("Password must be provided")

        self.base_url = base_url.rstrip("/")
        self.auth = HTTPBasicAuth(username, password)
        self.timeout = timeout

    def get_status(self):
        """Retrieve proxy server status."""
        return self._get("/api/status")

    def get_settings(self):
        """Retrieve proxy server settings."""
        return self._get("/api/settings")

    def get_filtering(self):
        """Retrieve blocked domains and URLs."""
        return self._get("/api/filtering")

    def add_filtering(self, filter_type: str, value: str):
        """Add a domain or URL to the block list."""
        payload = {"type": filter_type, "value": value}
        return self._post("/api/filtering", json=payload)

    def delete_filtering(self, filter_type: str, value: str):
        """Remove a domain or URL from the block list."""
        payload = {"type": filter_type, "value": value}
        return self._delete("/api/filtering", json=payload)

    # Internal helpers
    def _get(self, path):
        response = requests.get(
            f"{self.base_url}{path}", auth=self.auth, timeout=self.timeout
        )
        self._handle_response(response)
        return response.json()

    def _post(self, path, json=None):
        response = requests.post(
            f"{self.base_url}{path}",
            auth=self.auth,
            json=json,
            timeout=self.timeout,
        )
        self._handle_response(response)
        return response.json()

    def _delete(self, path, json=None):
        response = requests.delete(
            f"{self.base_url}{path}",
            auth=self.auth,
            json=json,
            timeout=self.timeout,
        )
        self._handle_response(response)
        return response.json()

    def _handle_response(self, response):
        if response.ok:
            return

        try:
            error_data = response.json()
        except Exception:
            error_data = {"error": response.text}

        status = response.status_code
        message = (
            error_data.get("message") or error_data.get("error") or "Unknown error"
        )

        if status == 400:
            raise PyProxyInvalidInput(message)
        elif status == 404:
            raise PyProxyNotFound(message)
        elif status == 409:
            raise PyProxyAlreadyExists(message)
        elif status >= 500:
            raise PyProxyServerError(message)
        else:
            raise PyProxyError(f"Unexpected error {status}: {message}")
