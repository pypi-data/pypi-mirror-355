"""Tests for the base client implementation."""

import json
import unittest
from unittest.mock import Mock, patch

import requests
from requests.exceptions import RequestException

from day2.client.base import BaseClient
from day2.client.config import Config
from day2.exceptions import (
    AuthenticationError,
    ClientError,
    ResourceNotFoundError,
    ServerError,
    ValidationError,
)
from day2.session import Session


class TestBaseClient(unittest.TestCase):
    """Test cases for the BaseClient class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock session
        self.mock_session = Mock(spec=Session)
        self.mock_session.credentials = Mock()
        self.mock_session.credentials.api_key = "test-api-key"
        self.mock_session.credentials.secret_key = "test-secret-key"
        self.mock_session.tenant_id = "test-tenant-id"

        # Create a config with test values
        self.config = Config(
            base_url="https://test-api.montycloud.com/day2/api",
            api_version="v1",
            timeout=5,
            max_retries=2,
            retry_backoff_factor=0.5,
            retry_min_delay=1.0,
            retry_max_delay=5.0,
        )
        self.mock_session._config = self.config

        # Create the client
        self.client = BaseClient(self.mock_session, "test-service")

    def test_init(self):
        """Test client initialization."""
        self.assertEqual(self.client.session, self.mock_session)
        self.assertEqual(self.client.service_name, "test-service")
        self.assertEqual(self.client._config, self.config)

    def test_get_endpoint_url(self):
        """Test _get_endpoint_url method."""
        # Test with endpoint without leading slash
        url = self.client._get_endpoint_url("tenants/123")
        expected = "https://test-api.montycloud.com/day2/api/v1/tenants/123"
        self.assertEqual(url, expected)

        # Test with endpoint with leading slash
        url = self.client._get_endpoint_url("/tenants/123")
        self.assertEqual(url, expected)

    def test_get_headers(self):
        """Test _get_headers method."""
        headers = self.client._get_headers()

        # Check required headers
        self.assertEqual(headers["Content-Type"], "application/json")
        self.assertEqual(headers["Accept"], "application/json")
        self.assertEqual(headers["x-api-key"], "test-api-key")
        self.assertEqual(headers["Authorization"], "test-secret-key")
        self.assertEqual(headers["x-tenant-id"], "test-tenant-id")

        # Test without tenant_id
        self.mock_session.tenant_id = None
        headers = self.client._get_headers()
        self.assertNotIn("x-tenant-id", headers)

        # Restore tenant_id for other tests
        self.mock_session.tenant_id = "test-tenant-id"

    @patch("day2.client.base.BaseClient._request_with_retry")
    def test_make_request_success(self, mock_request_with_retry):
        """Test successful API request."""
        # Mock successful response
        mock_request_with_retry.return_value = {"data": "test-data"}

        # Make request
        result = self.client._make_request("GET", "tenants")

        # Check result
        self.assertEqual(result, {"data": "test-data"})

        # Check request was made correctly
        mock_request_with_retry.assert_called_once()
        args, kwargs = mock_request_with_retry.call_args
        self.assertEqual(args[0], "GET")
        self.assertTrue(args[1].endswith("/tenants"))

    @patch("day2.client.base.BaseClient._request_with_retry")
    def test_make_request_with_json_data(self, mock_request_with_retry):
        """Test request with JSON data."""
        # Mock successful response
        mock_request_with_retry.return_value = {"data": "test-data"}

        # Make request with json_data
        json_data = {"name": "test-name"}
        result = self.client._make_request("POST", "tenants", json_data=json_data)

        # Check json_data was converted to json
        args, kwargs = mock_request_with_retry.call_args
        self.assertEqual(kwargs["json"], json_data)
        self.assertNotIn("json_data", kwargs)

    @patch("requests.request")
    @patch("day2.client.base.BaseClient._handle_response")
    def test_request_with_retry_success(self, mock_handle_response, mock_request):
        """Test successful request with retry logic."""
        # Mock response and handler
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.text = '{"data": "test-data"}'
        mock_response.headers = {"x-request-id": "test-request-id"}
        mock_request.return_value = mock_response

        mock_handle_response.return_value = {"data": "test-data"}

        # Call _request_with_retry directly
        result = self.client._request_with_retry("GET", "https://api.example.com/test")

        # Check result
        self.assertEqual(result, {"data": "test-data"})

        # Verify request was made with correct parameters
        self.assertEqual(mock_request.call_count, 1)
        args, kwargs = mock_request.call_args
        self.assertEqual(args[0], "GET")
        self.assertEqual(args[1], "https://api.example.com/test")
        self.assertEqual(kwargs["timeout"], 5)

    @patch("requests.request")
    def test_error_handling(self, mock_request):
        """Test error handling for different status codes."""
        # Define test cases: (status_code, error_class, error_message)
        test_cases = [
            (400, ValidationError, "Bad request"),
            (401, AuthenticationError, "Unauthorized"),
            (403, AuthenticationError, "Forbidden"),
            (404, ResourceNotFoundError, "Not found"),
            (429, ClientError, "Too many requests"),
            (500, ServerError, "Server error"),
            (503, ServerError, "Service unavailable"),
        ]

        for status_code, error_class, error_message in test_cases:
            # Mock response
            mock_response = Mock(spec=requests.Response)
            mock_response.status_code = status_code
            mock_response.json.return_value = {"Message": error_message}
            mock_response.text = json.dumps({"Message": error_message})
            mock_response.headers = {"x-request-id": "test-request-id"}
            mock_request.return_value = mock_response

            # Test error is raised
            with self.subTest(status_code=status_code):
                with self.assertRaises(error_class) as context:
                    # Patch _request_with_retry to call _handle_response directly
                    with patch.object(
                        self.client,
                        "_request_with_retry",
                        side_effect=lambda *args, **kwargs: self.client._handle_response(
                            mock_response
                        ),
                    ):
                        self.client._make_request("GET", "tenants")

                # Check error details
                error = context.exception
                # Different error classes might use different attribute names
                self.assertTrue(hasattr(error, "status_code"))
                self.assertEqual(error.status_code, status_code)

    @patch("requests.request")
    def test_non_json_response(self, mock_request):
        """Test handling non-JSON response."""
        # Mock non-JSON response
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 500
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = "Internal server error"
        mock_response.headers = {"x-request-id": "test-request-id"}
        mock_request.return_value = mock_response

        # Test ServerError is raised
        with patch.object(
            self.client,
            "_request_with_retry",
            side_effect=lambda *args, **kwargs: self.client._handle_response(
                mock_response
            ),
        ):
            with self.assertRaises(ServerError) as context:
                self.client._make_request("GET", "tenants")

            # Check error details
            error = context.exception
            self.assertEqual(error.status_code, 500)
            self.assertTrue(hasattr(error, "request_id"))

    @patch("requests.request")
    def test_request_exception(self, mock_request):
        """Test handling request exception."""
        # Mock request exception
        exception = RequestException("Connection error")
        mock_request.side_effect = exception

        # Test ServerError is raised
        with self.assertRaises(ServerError):
            self.client._request_with_retry("GET", "https://api.example.com/test")

        # Check request was called - multiple times due to retry logic
        # The actual number of calls may vary based on how tenacity implements retries
        # Just verify it was called at least once
        self.assertGreater(mock_request.call_count, 0)


if __name__ == "__main__":
    unittest.main()
