"""
Tests for the Loglito client.
"""

import json
import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from loglito import Loglito
from loglito.client import (
    LoglitoError,
    LoglitoConnectionError,
    LoglitoAuthenticationError,
    LoglitoServerError,
)


class TestLoglitoClient:
    """Test suite for the Loglito client."""

    def test_init_with_api_key(self):
        """Test client initialization with API key."""
        client = Loglito(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.base_url == "http://localhost:2044"
        assert client.timeout == 30.0
        assert client.verify_ssl is True

    def test_init_with_custom_config(self):
        """Test client initialization with custom configuration."""
        client = Loglito(
            api_key="test-key",
            base_url="https://api.loglito.io",
            timeout=60.0,
            retries=5,
            verify_ssl=False,
        )
        assert client.api_key == "test-key"
        assert client.base_url == "https://api.loglito.io"
        assert client.timeout == 60.0
        assert client.verify_ssl is False

    def test_init_without_api_key(self):
        """Test that ValueError is raised when no API key is provided."""
        with pytest.raises(ValueError, match="API key is required"):
            Loglito(api_key="")

        with pytest.raises(ValueError, match="API key is required"):
            Loglito(api_key=None)

    def test_headers_set_correctly(self):
        """Test that headers are set correctly."""
        client = Loglito(api_key="test-key")
        headers = client.session.headers
        assert headers["Content-Type"] == "application/json"
        assert headers["api-key"] == "test-key"
        assert "loglito-python" in headers["User-Agent"]

    @patch("loglito.client.requests.Session.post")
    def test_log_simple_message(self, mock_post):
        """Test logging a simple message."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        client = Loglito(api_key="test-key")
        result = client.log("Hello world!")

        assert result is True
        mock_post.assert_called_once()

        # Check the call arguments
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["message"] == "Hello world!"
        assert "log" in kwargs["json"]
        assert "__date" in kwargs["json"]["log"]

    @patch("loglito.client.requests.Session.post")
    def test_log_with_level_and_data(self, mock_post):
        """Test logging with level and data."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        client = Loglito(api_key="test-key")
        result = client.log(
            level="warning",
            message="Login required",
            data={"username": "john", "ip": "192.168.1.1"},
        )

        assert result is True
        mock_post.assert_called_once()

        # Check the call arguments
        args, kwargs = mock_post.call_args
        payload = kwargs["json"]
        assert payload["message"] == "Login required"
        assert payload["level"] == "warning"
        assert payload["log"]["username"] == "john"
        assert payload["log"]["ip"] == "192.168.1.1"
        assert "__date" in payload["log"]

    @patch("loglito.client.requests.Session.post")
    def test_log_with_kwargs(self, mock_post):
        """Test logging with additional keyword arguments."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        client = Loglito(api_key="test-key")
        result = client.log(
            message="User action",
            level="info",
            user_id=123,
            action="file_upload",
            success=True,
        )

        assert result is True
        mock_post.assert_called_once()

        # Check the call arguments
        args, kwargs = mock_post.call_args
        payload = kwargs["json"]
        assert payload["message"] == "User action"
        assert payload["level"] == "info"
        assert payload["log"]["user_id"] == 123
        assert payload["log"]["action"] == "file_upload"
        assert payload["log"]["success"] is True

    @patch("loglito.client.requests.Session.post")
    def test_log_batch(self, mock_post):
        """Test batch logging."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        client = Loglito(api_key="test-key")
        logs = [
            {
                "message": "User login",
                "level": "info",
                "data": {"user_id": 123, "ip": "192.168.1.1"},
            },
            {"message": "Page view", "level": "debug", "data": {"page": "/dashboard"}},
        ]
        result = client.log_batch(logs)

        assert result is True
        mock_post.assert_called_once()

        # Check the call arguments
        args, kwargs = mock_post.call_args
        payload = kwargs["json"]
        assert "logs" in payload
        assert len(payload["logs"]) == 2

        # Check first log
        first_log = payload["logs"][0]
        assert first_log["message"] == "User login"
        assert first_log["level"] == "info"
        assert first_log["log"]["user_id"] == 123
        assert first_log["log"]["ip"] == "192.168.1.1"

        # Check second log
        second_log = payload["logs"][1]
        assert second_log["message"] == "Page view"
        assert second_log["level"] == "debug"
        assert second_log["log"]["page"] == "/dashboard"

    @patch("loglito.client.requests.Session.post")
    def test_authentication_error(self, mock_post):
        """Test authentication error handling."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        mock_post.return_value = mock_response

        client = Loglito(api_key="invalid-key")

        with pytest.raises(LoglitoAuthenticationError):
            client.log("Test message")

    @patch("loglito.client.requests.Session.post")
    def test_server_error(self, mock_post):
        """Test server error handling."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        client = Loglito(api_key="test-key")

        with pytest.raises(LoglitoServerError):
            client.log("Test message")

    @patch("loglito.client.requests.Session.post")
    def test_connection_error(self, mock_post):
        """Test connection error handling."""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")

        client = Loglito(api_key="test-key")

        with pytest.raises(LoglitoConnectionError):
            client.log("Test message")

    @patch("loglito.client.requests.Session.post")
    def test_timeout_error(self, mock_post):
        """Test timeout error handling."""
        mock_post.side_effect = requests.exceptions.Timeout("Request timeout")

        client = Loglito(api_key="test-key")

        with pytest.raises(LoglitoConnectionError):
            client.log("Test message")

    @patch("loglito.client.requests.Session.post")
    def test_log_returns_false_on_exception(self, mock_post):
        """Test that log method returns False when an unexpected exception occurs."""
        mock_post.side_effect = Exception("Unexpected error")

        client = Loglito(api_key="test-key")
        result = client.log("Test message")

        assert result is False

    @patch("loglito.client.requests.Session.post")
    def test_test_connection_success(self, mock_post):
        """Test successful connection test."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        client = Loglito(api_key="test-key")
        result = client.ping()

        assert result is True
        mock_post.assert_called_once()

        # Check that a test log was sent
        args, kwargs = mock_post.call_args
        payload = kwargs["json"]
        assert payload["message"] == "Loglito connection test"
        assert payload["level"] == "info"
        assert payload["log"]["test"] is True

    @patch("loglito.client.requests.Session.post")
    def test_test_connection_failure(self, mock_post):
        """Test failed connection test."""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")

        client = Loglito(api_key="test-key")
        result = client.ping()

        assert result is False

    def test_context_manager(self):
        """Test using the client as a context manager."""
        with Loglito(api_key="test-key") as client:
            assert client.api_key == "test-key"
            mock_session = Mock()
            client.session = mock_session

        # Check that close was called
        mock_session.close.assert_called_once()

    def test_close_method(self):
        """Test the close method."""
        client = Loglito(api_key="test-key")
        mock_session = Mock()
        client.session = mock_session

        client.close()
        mock_session.close.assert_called_once()

    def test_base_url_trailing_slash_removal(self):
        """Test that trailing slashes are removed from base_url."""
        client = Loglito(api_key="test-key", base_url="https://api.loglito.io/")
        assert client.base_url == "https://api.loglito.io"

    @patch("loglito.client.requests.Session.post")
    def test_url_construction(self, mock_post):
        """Test that the URL is constructed correctly."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        client = Loglito(api_key="test-key", base_url="https://api.loglito.io")
        client.log("Test message")

        # Check that the correct URL was called
        args, kwargs = mock_post.call_args
        assert args[0] == "https://api.loglito.io/api/log"

    @patch("loglito.client.requests.Session.post")
    def test_ssl_verification_disabled(self, mock_post):
        """Test that SSL verification can be disabled."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        client = Loglito(api_key="test-key", verify_ssl=False)
        client.log("Test message")

        # Check that verify=False was passed
        args, kwargs = mock_post.call_args
        assert kwargs["verify"] is False

    def test_log_data_structure(self):
        """Test the structure of log data sent to the API."""
        with patch("loglito.client.requests.Session.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            client = Loglito(api_key="test-key")

            # Test with just message
            client.log("Simple message")
            payload = mock_post.call_args[1]["json"]
            assert "log" in payload
            assert "message" in payload
            assert "__date" in payload["log"]

            # Test with message, level, and data
            client.log(
                message="Complex log",
                level="error",
                data={"error_code": 500, "details": "Server error"},
                extra_field="extra_value",
            )
            payload = mock_post.call_args[1]["json"]
            assert payload["message"] == "Complex log"
            assert payload["level"] == "error"
            assert payload["log"]["error_code"] == 500
            assert payload["log"]["details"] == "Server error"
            assert payload["log"]["extra_field"] == "extra_value"
            assert "__date" in payload["log"]

    @patch("loglito.client.requests.Session.post")
    def test_trace_functionality(self, mock_post):
        """Test trace ID functionality."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        client = Loglito(api_key="test-key", immediate_mode=True)

        # Test setting trace and logging
        client.set_trace("trace-123")
        client.log("Test message with trace")

        # Check that trace_id was included
        args, kwargs = mock_post.call_args
        payload = kwargs["json"]
        assert "logs" in payload
        assert len(payload["logs"]) == 1
        log_data = payload["logs"][0]["log"]
        assert "__trace_id" in log_data
        assert log_data["__trace_id"] == "trace-123"

        # Test clearing trace
        mock_post.reset_mock()
        client.clear_trace()
        client.log("Test message without trace")

        # Check that trace_id was not included
        args, kwargs = mock_post.call_args
        payload = kwargs["json"]
        log_data = payload["logs"][0]["log"]
        assert "__trace_id" not in log_data

    @patch("loglito.client.requests.Session.post")
    def test_trace_functionality_batch(self, mock_post):
        """Test trace ID functionality with batch logging."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        client = Loglito(api_key="test-key", immediate_mode=True)

        # Set trace and log batch
        client.set_trace("batch-trace-456")
        logs = [
            {"message": "First log", "level": "info"},
            {"message": "Second log", "level": "debug"},
        ]
        client.log_batch(logs)

        # Check that trace_id was included in both logs
        args, kwargs = mock_post.call_args
        payload = kwargs["json"]
        assert "logs" in payload
        assert len(payload["logs"]) == 2

        for log_item in payload["logs"]:
            log_data = log_item["log"]
            assert "__trace_id" in log_data
            assert log_data["__trace_id"] == "batch-trace-456"

    @patch("loglito.client.requests.Session.post")
    def test_trace_with_different_log_methods(self, mock_post):
        """Test trace ID functionality with different log level methods."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        client = Loglito(api_key="test-key", immediate_mode=True)
        client.set_trace("method-trace-789")

        # Test with info method
        client.info("Info message", {"key": "value"})
        payload = mock_post.call_args[1]["json"]
        log_data = payload["logs"][0]["log"]
        assert log_data["__trace_id"] == "method-trace-789"

        # Test with error method
        mock_post.reset_mock()
        client.error("Error message", {"error": "details"})
        payload = mock_post.call_args[1]["json"]
        log_data = payload["logs"][0]["log"]
        assert log_data["__trace_id"] == "method-trace-789"


class TestLoglitoExceptions:
    """Test suite for Loglito exceptions."""

    def test_loglito_error_inheritance(self):
        """Test that custom exceptions inherit from LoglitoError."""
        assert issubclass(LoglitoConnectionError, LoglitoError)
        assert issubclass(LoglitoAuthenticationError, LoglitoError)
        assert issubclass(LoglitoServerError, LoglitoError)

    def test_exception_messages(self):
        """Test that exceptions can be raised with custom messages."""
        error = LoglitoError("Custom error message")
        assert str(error) == "Custom error message"

        auth_error = LoglitoAuthenticationError("Auth failed")
        assert str(auth_error) == "Auth failed"

        conn_error = LoglitoConnectionError("Connection failed")
        assert str(conn_error) == "Connection failed"

        server_error = LoglitoServerError("Server error")
        assert str(server_error) == "Server error"
