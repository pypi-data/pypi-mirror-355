"""Fabric API Client for Python"""

import os
from dataclasses import dataclass
from typing import Any

import httpx
from httpx_retries import Retry, RetryTransport

from fabric_mcp import __version__ as fabric_mcp_version
from fabric_mcp.utils import Log

logger = Log().logger

DEFAULT_BASE_URL = "http://127.0.0.1:8080"  # Default for fabric --serve
DEFAULT_TIMEOUT = 30  # seconds


@dataclass
class RequestConfig:
    """Configuration for HTTP request parameters."""

    params: dict[str, Any] | None = None
    json_data: dict[str, Any] | None = None
    data: Any | None = None
    headers: dict[str, str] | None = None


class FabricApiClient:
    """Client for interacting with the Fabric REST API."""

    FABRIC_API_HEADER = "X-API-Key"
    REDACTED_HEADERS = ["Authorization", FABRIC_API_HEADER]

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        """
        Initializes the Fabric API client.

        Args:
            base_url: The base URL for the Fabric API. Defaults to env
                FABRIC_BASE_URL or DEFAULT_BASE_URL.
            api_key: The API key for authentication. Defaults to env FABRIC_API_KEY.
            timeout: Request timeout in seconds.
        """
        self.base_url = base_url or os.environ.get("FABRIC_BASE_URL", DEFAULT_BASE_URL)
        self.api_key = api_key or os.environ.get("FABRIC_API_KEY")
        self.timeout = timeout

        if not self.api_key:
            logger.warning(
                "Fabric API key not provided. If needed, set FABRIC_API_KEY variable."
            )

        # Configure retry strategy for httpx
        # Basic limits, retries are handled by transport
        limits = httpx.Limits(max_connections=100, max_keepalive_connections=20)
        # Configure retries directly on the transport

        # New retry strategy with backoff using httpx-retries
        retry_strategy = Retry(
            total=3,  # Number of retries
            backoff_factor=0.3,  # Exponential backoff factor (e.g., 0.3s, 0.6s, 1.2s)
            status_forcelist=[429, 500, 502, 503, 504],  # Status codes to retry on
            allowed_methods=[
                "HEAD",
                "GET",
                "PUT",
                "DELETE",
                "OPTIONS",
                "TRACE",
            ],  # Methods to retry on
        )
        transport = RetryTransport(retry=retry_strategy)

        headers = {"User-Agent": f"FabricMCPClient/v{fabric_mcp_version}"}
        if self.api_key:
            headers[self.FABRIC_API_HEADER] = f"{self.api_key}"

        self.client = httpx.Client(
            base_url=self.base_url,
            headers=headers,
            timeout=self.timeout,
            limits=limits,
            transport=transport,
        )

        logger.info("FabricApiClient initialized for base URL: %s", self.base_url)

    def _request(
        self,
        method: str,
        endpoint: str,
        config: RequestConfig | None = None,
    ) -> httpx.Response:
        """
        Makes a request to the Fabric API.

        Args:
            method: HTTP method (e.g., 'GET', 'POST').
            endpoint: API endpoint path (e.g., '/patterns').
            config: Request configuration containing params, data, headers, etc.

        Returns:
            The httpx.Response object.

        Raises:
            httpx.RequestError: For connection errors, timeouts, etc.
            httpx.HTTPStatusError: For 4xx or 5xx responses.
        """
        if config is None:
            config = RequestConfig()

        effective_request_headers = dict(self.client.headers)
        if config.headers:
            effective_request_headers.update(config.headers)
        log_request_headers = dict(effective_request_headers)

        # Mask API key in logs
        for header_key in self.REDACTED_HEADERS:
            if header_key in log_request_headers:
                log_request_headers[header_key] = "***REDACTED***"

        logger.debug("Request: %s %s", method, endpoint)
        logger.debug("Headers: %s", log_request_headers)
        if config.params:
            logger.debug("Params: %s", config.params)
        if config.json_data:
            logger.debug("JSON Body: %s", config.json_data)
        elif config.data:
            logger.debug("Body: <raw data>")

        try:
            response = self.client.request(
                method=method,
                url=endpoint,
                params=config.params,
                json=config.json_data,
                data=config.data,
                timeout=self.timeout,
                headers=effective_request_headers,
            )
            logger.debug("Response Status: %s", response.status_code)
            response.raise_for_status()
            return response
        except httpx.RequestError as e:
            logger.error("API request failed: %s %s - %s", method, endpoint, e)
            raise
        except httpx.HTTPStatusError as e:
            logger.error(
                "API request failed with status %s: %s %s - %s",
                e.response.status_code,
                method,
                endpoint,
                e,
            )
            raise

    # --- Public API Methods ---

    def get(
        self, endpoint: str, params: dict[str, Any] | None = None, **kwargs: Any
    ) -> httpx.Response:
        """Sends a GET request."""
        config = RequestConfig(params=params, **kwargs)
        return self._request("GET", endpoint, config)

    def post(
        self,
        endpoint: str,
        json_data: dict[str, Any] | None = None,
        data: Any | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Sends a POST request."""
        config = RequestConfig(json_data=json_data, data=data, **kwargs)
        return self._request("POST", endpoint, config)

    def put(
        self,
        endpoint: str,
        json_data: dict[str, Any] | None = None,
        data: Any | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Sends a PUT request."""
        config = RequestConfig(json_data=json_data, data=data, **kwargs)
        return self._request("PUT", endpoint, config)

    def delete(self, endpoint: str, **kwargs: Any) -> httpx.Response:
        """Sends a DELETE request."""
        config = RequestConfig(**kwargs)
        return self._request("DELETE", endpoint, config)

    def close(self):
        """Closes the httpx client and releases resources."""
        self.client.close()
        logger.info("FabricApiClient closed.")
