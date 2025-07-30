"""Unit tests for fabric_mcp.api_client module."""

import os
from unittest.mock import Mock, patch

import httpx
import pytest

from fabric_mcp.api_client import (
    DEFAULT_BASE_URL,
    DEFAULT_TIMEOUT,
    FabricApiClient,
    RequestConfig,
)


class TestFabricApiClientInitialization:
    """Test cases for FabricApiClient initialization."""

    def test_init_with_defaults(self, monkeypatch: pytest.MonkeyPatch):
        """Test client initialization with default values."""
        # Clear the environment variables that might be set by the mock fixture
        monkeypatch.delenv("FABRIC_BASE_URL", raising=False)
        monkeypatch.delenv("FABRIC_API_KEY", raising=False)

        client = FabricApiClient()

        assert client.base_url == DEFAULT_BASE_URL
        assert client.api_key is None
        assert client.timeout == DEFAULT_TIMEOUT
        assert isinstance(client.client, httpx.Client)

    def test_init_with_parameters(self):
        """Test client initialization with explicit parameters."""
        base_url = "http://example.com:9000"
        api_key = "test-api-key"
        timeout = 60

        client = FabricApiClient(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
        )

        assert client.base_url == base_url
        assert client.api_key == api_key
        assert client.timeout == timeout

    @patch.dict(os.environ, {"FABRIC_BASE_URL": "http://env.example.com:8080"})
    def test_init_with_environment_variables(self):
        """Test client initialization with environment variables."""
        client = FabricApiClient()
        assert client.base_url == "http://env.example.com:8080"

    @patch.dict(os.environ, {"FABRIC_BASE_URL": "http://env.example.com:8080"})
    def test_init_parameters_override_environment(self):
        """Test that explicit parameters override environment variables."""
        explicit_url = "http://explicit.example.com:9000"
        client = FabricApiClient(base_url=explicit_url)
        assert client.base_url == explicit_url

    def test_init_without_api_key_logs_warning(self, caplog: pytest.LogCaptureFixture):
        """Test that initialization without API key logs a warning."""
        FabricApiClient()
        assert "Fabric API key not provided" in caplog.text

    def test_init_with_api_key_no_warning(self, caplog: pytest.LogCaptureFixture):
        """Test that initialization with API key doesn't log a warning."""
        FabricApiClient(api_key="test-key")
        assert "No API key provided" not in caplog.text


class TestFabricApiClientConfiguration:
    """Test cases for FabricApiClient configuration."""

    def test_client_configuration(self):
        """Test that the httpx client is configured correctly."""
        base_url = "http://test.example.com:8080"
        api_key = "test-api-key"
        timeout = 45

        client = FabricApiClient(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
        )

        # Check client configuration
        assert client.client.base_url == base_url
        assert client.client.timeout.read == timeout
        assert client.FABRIC_API_HEADER in client.client.headers
        assert client.client.headers[client.FABRIC_API_HEADER] == api_key

        # Check that transport is configured (without accessing protected members)
        assert hasattr(client.client, "_transport")

    @patch.dict(os.environ, {}, clear=True)
    def test_client_without_api_key_no_header(self):
        """Test that client without API key doesn't set the API header."""
        client = FabricApiClient()
        assert client.FABRIC_API_HEADER not in client.client.headers


class TestFabricApiClientErrorHandling:
    """Test cases for error handling via public methods."""

    @patch("fabric_mcp.api_client.httpx.Client")
    def test_request_handles_request_error(self, mock_client_class: Mock):
        """Test that requests handle httpx.RequestError."""
        mock_client = Mock()
        mock_client.request.side_effect = httpx.RequestError("Connection failed")
        mock_client.headers = {}
        mock_client_class.return_value = mock_client

        client = FabricApiClient()

        with pytest.raises(httpx.RequestError):
            client.get("/test")

    @patch("fabric_mcp.api_client.httpx.Client")
    def test_request_handles_http_status_error(self, mock_client_class: Mock):
        """Test that requests handle httpx.HTTPStatusError."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=Mock(), response=mock_response
        )
        mock_client.request.return_value = mock_response
        mock_client.headers = {}
        mock_client_class.return_value = mock_client

        client = FabricApiClient()

        with pytest.raises(httpx.HTTPStatusError):
            client.get("/test")


class TestFabricApiClientPublicMethods:
    """Test cases for public HTTP methods."""

    @patch("fabric_mcp.api_client.httpx.Client")
    def test_get_method_without_params(self, mock_client_class: Mock):
        """Test GET method without parameters to cover default config creation."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.request.return_value = mock_response
        mock_client.headers = {}
        mock_client_class.return_value = mock_client

        client = FabricApiClient()
        result = client.get("/test")  # No params, should create default RequestConfig

        assert result == mock_response
        call_args = mock_client.request.call_args
        assert call_args[1]["method"] == "GET"
        assert call_args[1]["url"] == "/test"
        assert call_args[1]["params"] is None

    @patch("fabric_mcp.api_client.httpx.Client")
    def test_get_method(self, mock_client_class: Mock):
        """Test GET method."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.request.return_value = mock_response
        mock_client.headers = {}
        mock_client_class.return_value = mock_client

        client = FabricApiClient()
        result = client.get("/test", params={"key": "value"})

        assert result == mock_response
        call_args = mock_client.request.call_args
        assert call_args[1]["method"] == "GET"
        assert call_args[1]["url"] == "/test"
        assert call_args[1]["params"] == {"key": "value"}

    @patch("fabric_mcp.api_client.httpx.Client")
    def test_post_method(self, mock_client_class: Mock):
        """Test POST method."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 201
        mock_client.request.return_value = mock_response
        mock_client.headers = {}
        mock_client_class.return_value = mock_client

        client = FabricApiClient()
        result = client.post("/test", json_data={"key": "value"})

        assert result == mock_response
        call_args = mock_client.request.call_args
        assert call_args[1]["method"] == "POST"
        assert call_args[1]["url"] == "/test"
        assert call_args[1]["json"] == {"key": "value"}

    @patch("fabric_mcp.api_client.httpx.Client")
    def test_post_method_with_headers(self, mock_client_class: Mock):
        """Test POST method with custom headers to cover header update logic."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 201
        mock_client.request.return_value = mock_response
        mock_client.headers = {"Default": "header"}
        mock_client_class.return_value = mock_client

        client = FabricApiClient()
        result = client.post(
            "/test", json_data={"key": "value"}, headers={"Custom": "header"}
        )

        assert result == mock_response
        call_args = mock_client.request.call_args
        # Should have both default and custom headers
        assert "Default" in call_args[1]["headers"]
        assert "Custom" in call_args[1]["headers"]

    @patch("fabric_mcp.api_client.httpx.Client")
    def test_post_method_with_raw_data(self, mock_client_class: Mock):
        """Test POST method with raw data to cover raw data logging."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 201
        mock_client.request.return_value = mock_response
        mock_client.headers = {}
        mock_client_class.return_value = mock_client

        client = FabricApiClient()
        result = client.post("/test", data=b"raw binary data")

        assert result == mock_response
        call_args = mock_client.request.call_args
        assert call_args[1]["data"] == b"raw binary data"

    @patch("fabric_mcp.api_client.httpx.Client")
    def test_post_method_with_api_key_header_masking(self, mock_client_class: Mock):
        """Test that API key headers are masked in logs."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 201
        mock_client.request.return_value = mock_response
        mock_client.headers = {"X-API-Key": "secret-key"}
        mock_client_class.return_value = mock_client

        client = FabricApiClient(api_key="secret-key")

        with patch("fabric_mcp.api_client.logger") as mock_logger:
            result = client.post("/test", json_data={"key": "value"})

            # Check that logger.debug was called and API key was masked
            mock_logger.debug.assert_called()
            debug_calls = mock_logger.debug.call_args_list

            # Find the headers debug call
            headers_call = None
            for call in debug_calls:
                if len(call[0]) > 1 and "Headers:" in str(call[0][0]):
                    headers_call = call
                    break

            assert headers_call is not None
            # The headers should contain the masked value
            headers_str = str(headers_call[0][1])
            assert "***REDACTED***" in headers_str

        assert result == mock_response

    @patch("fabric_mcp.api_client.httpx.Client")
    def test_put_method(self, mock_client_class: Mock):
        """Test PUT method."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.request.return_value = mock_response
        mock_client.headers = {}
        mock_client_class.return_value = mock_client

        client = FabricApiClient()
        result = client.put("/test", json_data={"key": "value"})

        assert result == mock_response
        call_args = mock_client.request.call_args
        assert call_args[1]["method"] == "PUT"

    @patch("fabric_mcp.api_client.httpx.Client")
    def test_delete_method(self, mock_client_class: Mock):
        """Test DELETE method."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 204
        mock_client.request.return_value = mock_response
        mock_client.headers = {}
        mock_client_class.return_value = mock_client

        client = FabricApiClient()
        result = client.delete("/test")

        assert result == mock_response
        call_args = mock_client.request.call_args
        assert call_args[1]["method"] == "DELETE"

    @patch("fabric_mcp.api_client.httpx.Client")
    def test_close_method(self, mock_client_class: Mock):
        """Test close method."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        client = FabricApiClient()
        client.close()

        mock_client.close.assert_called_once()


class TestFabricApiClientConstants:
    """Test cases for class constants."""

    def test_redacted_headers_constant(self):
        """Test that REDACTED_HEADERS constant is properly defined."""
        assert "Authorization" in FabricApiClient.REDACTED_HEADERS
        assert FabricApiClient.FABRIC_API_HEADER in FabricApiClient.REDACTED_HEADERS

    def test_fabric_api_header_constant(self):
        """Test that FABRIC_API_HEADER constant is properly defined."""
        assert FabricApiClient.FABRIC_API_HEADER == "X-API-Key"


class TestRequestConfig:
    """Test cases for RequestConfig dataclass."""

    def test_request_config_defaults(self):
        """Test RequestConfig with default values."""
        config = RequestConfig()
        assert config.params is None
        assert config.json_data is None
        assert config.data is None
        assert config.headers is None

    def test_request_config_with_values(self):
        """Test RequestConfig with explicit values."""
        config = RequestConfig(
            params={"key": "value"},
            json_data={"data": "test"},
            headers={"Custom": "header"},
        )
        assert config.params == {"key": "value"}
        assert config.json_data == {"data": "test"}
        assert config.headers == {"Custom": "header"}
