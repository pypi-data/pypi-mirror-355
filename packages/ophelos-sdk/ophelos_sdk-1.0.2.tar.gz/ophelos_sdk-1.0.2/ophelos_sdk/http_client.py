"""
HTTP client for making authenticated requests to the Ophelos API.
"""

import time
import random
from typing import Optional, Dict, Any, List, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .auth import OAuth2Authenticator
from .exceptions import (
    OphelosAPIError,
    AuthenticationError,
    ValidationError,
    NotFoundError,
    RateLimitError,
    ConflictError,
    ForbiddenError,
    ServerError,
)


class JitteredRetry(Retry):
    """Custom retry class with exponential backoff and additive jitter."""

    def get_backoff_time(self) -> float:
        """
        Calculate backoff time with additive jitter.

        Uses standard exponential backoff plus random 0-1.5 seconds.
        This maintains predictable base timing while preventing thundering herd.
        """
        backoff_time = super().get_backoff_time()
        if backoff_time <= 0:
            return 0

        # Additive jitter: standard backoff + random 0-1.5 seconds
        jitter_amount = random.uniform(0, 1.5)
        return backoff_time + jitter_amount


class HTTPClient:
    """HTTP client for making authenticated requests to Ophelos API."""

    def __init__(
        self,
        authenticator: OAuth2Authenticator,
        base_url: str,
        tenant_id: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize HTTP client.

        Args:
            authenticator: OAuth2 authenticator instance
            base_url: Base URL for API requests
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
        """
        self.authenticator = authenticator
        self.base_url = base_url.rstrip("/")
        self.tenant_id = tenant_id
        self.timeout = timeout

        # Configure session with jittered retry strategy
        self.session = requests.Session()

        retry_strategy = JitteredRetry(
            total=max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            backoff_factor=1,
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _prepare_headers(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Prepare headers for request including authentication."""
        request_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "ophelos-python-sdk/1.0.2",
        }

        request_headers.update(self.authenticator.get_auth_headers())

        if self.tenant_id:
            request_headers["OPHELOS_TENANT_ID"] = self.tenant_id

        if headers:
            request_headers.update(headers)

        return request_headers

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle API response and raise appropriate exceptions for errors.

        Args:
            response: HTTP response object

        Returns:
            Parsed JSON response data

        Raises:
            OphelosAPIError: For various API errors
        """
        try:
            json_data = response.json() if response.content else {}
            response_data = json_data if isinstance(json_data, dict) else {"data": json_data}
        except ValueError:
            response_data = {"message": response.text}

        if response.status_code >= 400:
            message = response_data.get("message", f"HTTP {response.status_code}")

            if response.status_code == 401:
                self.authenticator.invalidate_token()
                raise AuthenticationError(message, response_data=response_data)
            elif response.status_code == 403:
                raise ForbiddenError(message, response_data=response_data)
            elif response.status_code == 404:
                raise NotFoundError(message, response_data=response_data)
            elif response.status_code == 409:
                raise ConflictError(message, response_data=response_data)
            elif response.status_code == 422:
                raise ValidationError(message, response_data=response_data)
            elif response.status_code == 429:
                raise RateLimitError(message, response_data=response_data)
            elif response.status_code >= 500:
                raise ServerError(
                    message, status_code=response.status_code, response_data=response_data
                )
            else:
                raise OphelosAPIError(
                    message, status_code=response.status_code, response_data=response_data
                )

        return response_data

    def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make GET request.

        Args:
            path: API endpoint path
            params: Query parameters
            headers: Additional headers

        Returns:
            Response data
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        request_headers = self._prepare_headers(headers)

        response = self.session.get(
            url, params=params, headers=request_headers, timeout=self.timeout
        )

        return self._handle_response(response)

    def post(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make POST request.

        Args:
            path: API endpoint path
            data: Request body data
            params: Query parameters
            headers: Additional headers

        Returns:
            Response data
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        request_headers = self._prepare_headers(headers)

        response = self.session.post(
            url, json=data, params=params, headers=request_headers, timeout=self.timeout
        )

        return self._handle_response(response)

    def put(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make PUT request.

        Args:
            path: API endpoint path
            data: Request body data
            params: Query parameters
            headers: Additional headers

        Returns:
            Response data
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        request_headers = self._prepare_headers(headers)

        response = self.session.put(
            url, json=data, params=params, headers=request_headers, timeout=self.timeout
        )

        return self._handle_response(response)

    def patch(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make PATCH request.

        Args:
            path: API endpoint path
            data: Request body data
            params: Query parameters
            headers: Additional headers

        Returns:
            Response data
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        request_headers = self._prepare_headers(headers)

        response = self.session.patch(
            url, json=data, params=params, headers=request_headers, timeout=self.timeout
        )

        return self._handle_response(response)

    def delete(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make DELETE request.

        Args:
            path: API endpoint path
            params: Query parameters
            headers: Additional headers

        Returns:
            Response data
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        request_headers = self._prepare_headers(headers)

        response = self.session.delete(
            url, params=params, headers=request_headers, timeout=self.timeout
        )

        return self._handle_response(response)
