"""
Tests for HTTP Client
"""

import pytest
import requests
from unittest.mock import Mock, patch

from spotichart.core.http_client import RetryHttpClient
from spotichart.utils.exceptions import ScrapingError


class TestRetryHttpClient:
    """Test RetryHttpClient."""

    def test_client_initialization(self):
        """Client should initialize with default values."""
        client = RetryHttpClient()
        assert client.timeout == 30
        assert client.max_retries == 3
        assert client.retry_delay == 2

    def test_client_custom_values(self):
        """Client should accept custom values."""
        client = RetryHttpClient(
            timeout=60, max_retries=5, retry_delay=3, user_agent="TestAgent"
        )
        assert client.timeout == 60
        assert client.max_retries == 5
        assert client.retry_delay == 3
        assert client.session.headers["User-Agent"] == "TestAgent"

    @patch("spotichart.core.http_client.requests.Session.get")
    def test_fetch_success(self, mock_get):
        """Fetch should return Success on successful request."""
        mock_response = Mock()
        mock_response.content = b"<html>test content</html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = RetryHttpClient()
        result = client.fetch("http://example.com")

        assert result.is_success()
        assert result.unwrap() == "<html>test content</html>"
        mock_get.assert_called_once()

    @patch("spotichart.core.http_client.requests.Session.get")
    def test_fetch_with_custom_timeout(self, mock_get):
        """Fetch should use custom timeout."""
        mock_response = Mock()
        mock_response.content = b"test"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = RetryHttpClient(timeout=30)
        result = client.fetch("http://example.com", timeout=60)

        assert result.is_success()
        call_args = mock_get.call_args
        assert call_args[1]["timeout"] == 60

    @patch("spotichart.core.http_client.requests.Session.get")
    @patch("spotichart.core.http_client.time.sleep")
    def test_fetch_retry_on_failure(self, mock_sleep, mock_get):
        """Fetch should retry on failure."""
        # Fail 2 times, then succeed
        mock_get.side_effect = [
            requests.RequestException("First fail"),
            requests.RequestException("Second fail"),
            Mock(content=b"success", raise_for_status=Mock()),
        ]

        client = RetryHttpClient(max_retries=3, retry_delay=1)
        result = client.fetch("http://example.com")

        assert result.is_success()
        assert result.unwrap() == "success"
        assert mock_get.call_count == 3
        assert mock_sleep.call_count == 2  # Slept between retries

    @patch("spotichart.core.http_client.requests.Session.get")
    @patch("spotichart.core.http_client.time.sleep")
    def test_fetch_max_retries_exceeded(self, mock_sleep, mock_get):
        """Fetch should return Failure after max retries."""
        mock_get.side_effect = requests.RequestException("Connection error")

        client = RetryHttpClient(max_retries=3)
        result = client.fetch("http://example.com")

        assert result.is_failure()
        assert isinstance(result.error, ScrapingError)
        assert "Failed to fetch" in str(result.error)
        assert mock_get.call_count == 3

    @patch("spotichart.core.http_client.requests.Session.get")
    @patch("spotichart.core.http_client.time.sleep")
    def test_fetch_exponential_backoff(self, mock_sleep, mock_get):
        """Fetch should use exponential backoff."""
        mock_get.side_effect = [
            requests.RequestException("Fail 1"),
            requests.RequestException("Fail 2"),
            requests.RequestException("Fail 3"),
        ]

        client = RetryHttpClient(max_retries=3, retry_delay=2)
        result = client.fetch("http://example.com")

        assert result.is_failure()
        # Should sleep 2*1, 2*2 seconds
        assert mock_sleep.call_args_list[0][0][0] == 2
        assert mock_sleep.call_args_list[1][0][0] == 4

    def test_close(self):
        """Close should close the session."""
        client = RetryHttpClient()
        with patch.object(client.session, "close") as mock_close:
            client.close()
            mock_close.assert_called_once()

    @patch("spotichart.core.http_client.requests.Session.get")
    def test_http_status_error(self, mock_get):
        """Fetch should handle HTTP status errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404")
        mock_get.return_value = mock_response

        client = RetryHttpClient(max_retries=1)
        result = client.fetch("http://example.com")

        assert result.is_failure()
