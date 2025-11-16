"""
Tests for Infrastructure Decorators (Decorator Pattern)
"""

import logging
import time
from unittest.mock import Mock

import pytest

from spotichart.infrastructure.decorators import (
    CachingPlaylistOperationsDecorator,
    LoggingPlaylistOperationsDecorator,
    MetricsPlaylistOperationsDecorator,
    RetryPlaylistOperationsDecorator,
)


class TestLoggingPlaylistOperationsDecorator:
    """Test logging decorator."""

    def test_create_logs_success(self, caplog):
        """Test that create operation is logged on success."""
        wrapped = Mock()
        wrapped.create.return_value = {"id": "test_id", "name": "Test"}

        with caplog.at_level(logging.INFO):
            decorator = LoggingPlaylistOperationsDecorator(wrapped)
            result = decorator.create("Test", "Description", True)

        assert result["id"] == "test_id"
        assert "Creating playlist: 'Test'" in caplog.text
        assert "Playlist created successfully" in caplog.text

    def test_create_logs_failure(self, caplog):
        """Test that create operation is logged on failure."""
        wrapped = Mock()
        wrapped.create.side_effect = Exception("API error")

        with caplog.at_level(logging.ERROR):
            decorator = LoggingPlaylistOperationsDecorator(wrapped)
            with pytest.raises(Exception):
                decorator.create("Test", "Description", True)

        assert "Failed to create playlist" in caplog.text

    def test_get_all_logs_debug(self, caplog):
        """Test that get_all logs at debug level."""
        wrapped = Mock()
        wrapped.get_all.return_value = [{"id": "p1"}, {"id": "p2"}]

        with caplog.at_level(logging.DEBUG):
            decorator = LoggingPlaylistOperationsDecorator(wrapped)
            result = decorator.get_all(10)

        assert len(result) == 2
        assert "Fetching up to 10 playlists" in caplog.text
        assert "Fetched 2 playlists" in caplog.text

    def test_find_by_name_logs_found(self, caplog):
        """Test logging when playlist is found."""
        wrapped = Mock()
        wrapped.find_by_name.return_value = {"id": "test_id", "name": "Test"}

        with caplog.at_level(logging.DEBUG):
            decorator = LoggingPlaylistOperationsDecorator(wrapped)
            result = decorator.find_by_name("Test")

        assert result["id"] == "test_id"
        assert "Found playlist 'Test'" in caplog.text

    def test_find_by_name_logs_not_found(self, caplog):
        """Test logging when playlist is not found."""
        wrapped = Mock()
        wrapped.find_by_name.return_value = None

        with caplog.at_level(logging.DEBUG):
            decorator = LoggingPlaylistOperationsDecorator(wrapped)
            result = decorator.find_by_name("Nonexistent")

        assert result is None
        assert "Playlist 'Nonexistent' not found" in caplog.text

    def test_update_details_logs(self, caplog):
        """Test that update_details is logged."""
        wrapped = Mock()

        with caplog.at_level(logging.INFO):
            decorator = LoggingPlaylistOperationsDecorator(wrapped)
            decorator.update_details("test_id", "New description")

        assert "Updating playlist test_id" in caplog.text
        assert "Playlist updated successfully" in caplog.text

    def test_clear_logs(self, caplog):
        """Test that clear is logged."""
        wrapped = Mock()

        with caplog.at_level(logging.INFO):
            decorator = LoggingPlaylistOperationsDecorator(wrapped)
            decorator.clear("test_id")

        assert "Clearing playlist test_id" in caplog.text
        assert "Playlist cleared successfully" in caplog.text

    def test_create_logs_failure_reraises(self, caplog):
        """Test that create re-raises exception after logging."""
        wrapped = Mock()
        wrapped.create.side_effect = ValueError("Invalid input")

        with caplog.at_level(logging.ERROR):
            decorator = LoggingPlaylistOperationsDecorator(wrapped)
            with pytest.raises(ValueError):
                decorator.create("Test")

        assert "Failed to create playlist" in caplog.text

    def test_get_all_logs_failure(self, caplog):
        """Test that get_all logs failures."""
        wrapped = Mock()
        wrapped.get_all.side_effect = Exception("API error")

        with caplog.at_level(logging.ERROR):
            decorator = LoggingPlaylistOperationsDecorator(wrapped)
            with pytest.raises(Exception):
                decorator.get_all(50)

        assert "Failed to fetch playlists" in caplog.text

    def test_find_by_name_logs_error(self, caplog):
        """Test that find_by_name logs errors."""
        wrapped = Mock()
        wrapped.find_by_name.side_effect = Exception("Error")

        with caplog.at_level(logging.ERROR):
            decorator = LoggingPlaylistOperationsDecorator(wrapped)
            with pytest.raises(Exception):
                decorator.find_by_name("Test")

        assert "Error searching for playlist" in caplog.text

    def test_update_details_logs_failure(self, caplog):
        """Test that update_details logs failures."""
        wrapped = Mock()
        wrapped.update_details.side_effect = Exception("Update failed")

        with caplog.at_level(logging.ERROR):
            decorator = LoggingPlaylistOperationsDecorator(wrapped)
            with pytest.raises(Exception):
                decorator.update_details("test_id", "New")

        assert "Failed to update playlist" in caplog.text

    def test_clear_logs_failure(self, caplog):
        """Test that clear logs failures."""
        wrapped = Mock()
        wrapped.clear.side_effect = Exception("Clear failed")

        with caplog.at_level(logging.ERROR):
            decorator = LoggingPlaylistOperationsDecorator(wrapped)
            with pytest.raises(Exception):
                decorator.clear("test_id")

        assert "Failed to clear playlist" in caplog.text


class TestRetryPlaylistOperationsDecorator:
    """Test retry decorator."""

    def test_create_succeeds_first_try(self):
        """Test that successful operation doesn't retry."""
        wrapped = Mock()
        wrapped.create.return_value = {"id": "test_id"}

        decorator = RetryPlaylistOperationsDecorator(wrapped, max_retries=3)
        result = decorator.create("Test")

        assert result["id"] == "test_id"
        assert wrapped.create.call_count == 1

    def test_create_retries_on_failure(self):
        """Test that failed operation retries."""
        wrapped = Mock()
        wrapped.create.side_effect = [
            Exception("Error 1"),
            Exception("Error 2"),
            {"id": "test_id"},
        ]

        decorator = RetryPlaylistOperationsDecorator(
            wrapped, max_retries=3, base_delay=0.01  # Fast retry for testing
        )
        result = decorator.create("Test")

        assert result["id"] == "test_id"
        assert wrapped.create.call_count == 3

    def test_create_fails_after_max_retries(self):
        """Test that operation fails after max retries."""
        wrapped = Mock()
        wrapped.create.side_effect = Exception("Persistent error")

        decorator = RetryPlaylistOperationsDecorator(wrapped, max_retries=2, base_delay=0.01)

        with pytest.raises(Exception, match="Persistent error"):
            decorator.create("Test")

        assert wrapped.create.call_count == 2

    def test_exponential_backoff(self, monkeypatch):
        """Test that retry uses exponential backoff."""
        sleep_calls = []

        def mock_sleep(seconds):
            sleep_calls.append(seconds)

        monkeypatch.setattr(time, "sleep", mock_sleep)

        wrapped = Mock()
        wrapped.create.side_effect = [Exception("E1"), Exception("E2"), {"id": "test"}]

        decorator = RetryPlaylistOperationsDecorator(
            wrapped, max_retries=3, base_delay=1.0, exponential_base=2.0
        )
        decorator.create("Test")

        assert len(sleep_calls) == 2
        assert sleep_calls[0] == 1.0  # 1.0 * 2^0
        assert sleep_calls[1] == 2.0  # 1.0 * 2^1

    def test_max_delay_cap(self, monkeypatch):
        """Test that retry delay is capped at max_delay."""
        sleep_calls = []

        def mock_sleep(seconds):
            sleep_calls.append(seconds)

        monkeypatch.setattr(time, "sleep", mock_sleep)

        wrapped = Mock()
        wrapped.create.side_effect = [Exception("E1"), Exception("E2"), {"id": "test"}]

        decorator = RetryPlaylistOperationsDecorator(
            wrapped, max_retries=3, base_delay=10.0, max_delay=5.0, exponential_base=2.0
        )
        decorator.create("Test")

        # All delays should be capped at 5.0
        assert all(delay <= 5.0 for delay in sleep_calls)

    def test_all_operations_support_retry(self):
        """Test that all operations can be retried."""
        wrapped = Mock()
        wrapped.get_all.side_effect = [Exception("Error"), [{"id": "p1"}]]
        wrapped.find_by_name.side_effect = [Exception("Error"), {"id": "p1"}]
        wrapped.update_details.side_effect = [Exception("Error"), None]
        wrapped.clear.side_effect = [Exception("Error"), None]

        decorator = RetryPlaylistOperationsDecorator(wrapped, max_retries=2, base_delay=0.01)

        assert len(decorator.get_all()) == 1
        assert decorator.find_by_name("Test")["id"] == "p1"
        decorator.update_details("test_id", "New")
        decorator.clear("test_id")

        assert wrapped.get_all.call_count == 2
        assert wrapped.find_by_name.call_count == 2
        assert wrapped.update_details.call_count == 2
        assert wrapped.clear.call_count == 2


class TestMetricsPlaylistOperationsDecorator:
    """Test metrics decorator."""

    def test_tracks_operation_calls(self):
        """Test that operation calls are tracked."""
        wrapped = Mock()
        wrapped.create.return_value = {"id": "test"}

        decorator = MetricsPlaylistOperationsDecorator(wrapped)

        decorator.create("Test")
        decorator.create("Test 2")

        metrics = decorator.get_metrics()
        assert metrics["create"]["calls"] == 2
        assert metrics["get_all"]["calls"] == 0

    def test_tracks_successes(self):
        """Test that successful operations are tracked."""
        wrapped = Mock()
        wrapped.create.return_value = {"id": "test"}

        decorator = MetricsPlaylistOperationsDecorator(wrapped)

        decorator.create("Test")

        metrics = decorator.get_metrics()
        assert metrics["create"]["successes"] == 1
        assert metrics["create"]["failures"] == 0

    def test_tracks_failures(self):
        """Test that failed operations are tracked."""
        wrapped = Mock()
        wrapped.create.side_effect = Exception("Error")

        decorator = MetricsPlaylistOperationsDecorator(wrapped)

        with pytest.raises(Exception):
            decorator.create("Test")

        metrics = decorator.get_metrics()
        assert metrics["create"]["calls"] == 1
        assert metrics["create"]["successes"] == 0
        assert metrics["create"]["failures"] == 1

    def test_tracks_duration(self, monkeypatch):
        """Test that operation duration is tracked."""

        class FakeTime:
            def __init__(self):
                self.current = 0

            def time(self):
                self.current += 0.5
                return self.current

        fake_time = FakeTime()
        monkeypatch.setattr(time, "time", fake_time.time)

        wrapped = Mock()
        wrapped.create.return_value = {"id": "test"}

        decorator = MetricsPlaylistOperationsDecorator(wrapped)

        decorator.create("Test")

        metrics = decorator.get_metrics()
        assert metrics["create"]["total_duration"] == 0.5
        assert metrics["create"]["average_duration"] == 0.5

    def test_calculates_success_rate(self):
        """Test that success rate is calculated."""
        wrapped = Mock()
        wrapped.create.side_effect = [{"id": "1"}, Exception("Error"), {"id": "2"}]

        decorator = MetricsPlaylistOperationsDecorator(wrapped)

        decorator.create("Test 1")
        with pytest.raises(Exception):
            decorator.create("Test 2")
        decorator.create("Test 3")

        metrics = decorator.get_metrics()
        assert metrics["create"]["calls"] == 3
        assert metrics["create"]["successes"] == 2
        assert metrics["create"]["failures"] == 1
        assert metrics["create"]["success_rate"] == pytest.approx(2 / 3)

    def test_reset_metrics(self):
        """Test that metrics can be reset."""
        wrapped = Mock()
        wrapped.create.return_value = {"id": "test"}

        decorator = MetricsPlaylistOperationsDecorator(wrapped)

        decorator.create("Test")
        decorator.reset_metrics()

        metrics = decorator.get_metrics()
        assert metrics["create"]["calls"] == 0
        assert metrics["create"]["successes"] == 0

    def test_all_operations_tracked(self):
        """Test that all operations are tracked."""
        wrapped = Mock()
        wrapped.create.return_value = {"id": "test"}
        wrapped.get_all.return_value = []
        wrapped.find_by_name.return_value = None
        wrapped.update_details.return_value = None
        wrapped.clear.return_value = None

        decorator = MetricsPlaylistOperationsDecorator(wrapped)

        decorator.create("Test")
        decorator.get_all()
        decorator.find_by_name("Test")
        decorator.update_details("test_id")
        decorator.clear("test_id")

        metrics = decorator.get_metrics()
        assert metrics["create"]["calls"] == 1
        assert metrics["get_all"]["calls"] == 1
        assert metrics["find_by_name"]["calls"] == 1
        assert metrics["update_details"]["calls"] == 1
        assert metrics["clear"]["calls"] == 1


class TestCachingPlaylistOperationsDecorator:
    """Test caching decorator."""

    def test_get_all_caches_result(self):
        """Test that get_all caches results."""
        wrapped = Mock()
        wrapped.get_all.return_value = [{"id": "p1"}]

        decorator = CachingPlaylistOperationsDecorator(wrapped, ttl_seconds=10)

        # First call
        result1 = decorator.get_all(50)
        # Second call should use cache
        result2 = decorator.get_all(50)

        assert result1 == result2
        assert wrapped.get_all.call_count == 1

    def test_find_by_name_caches_result(self):
        """Test that find_by_name caches results."""
        wrapped = Mock()
        wrapped.find_by_name.return_value = {"id": "p1", "name": "Test"}

        decorator = CachingPlaylistOperationsDecorator(wrapped, ttl_seconds=10)

        result1 = decorator.find_by_name("Test")
        result2 = decorator.find_by_name("Test")

        assert result1 == result2
        assert wrapped.find_by_name.call_count == 1

    def test_cache_expires(self, monkeypatch):
        """Test that cache entries expire after TTL."""

        class FakeTime:
            def __init__(self):
                self.current = 0

            def time(self):
                return self.current

        fake_time = FakeTime()
        monkeypatch.setattr(time, "time", fake_time.time)

        wrapped = Mock()
        wrapped.get_all.return_value = [{"id": "p1"}]

        decorator = CachingPlaylistOperationsDecorator(wrapped, ttl_seconds=5)

        # First call
        decorator.get_all(50)
        assert wrapped.get_all.call_count == 1

        # Advance time by 3 seconds (within TTL)
        fake_time.current = 3
        decorator.get_all(50)
        assert wrapped.get_all.call_count == 1  # Still cached

        # Advance time by 6 seconds total (past TTL)
        fake_time.current = 6
        decorator.get_all(50)
        assert wrapped.get_all.call_count == 2  # Cache expired, new call

    def test_create_invalidates_cache(self):
        """Test that create invalidates cache."""
        wrapped = Mock()
        wrapped.get_all.return_value = [{"id": "p1"}]
        wrapped.create.return_value = {"id": "p2"}

        decorator = CachingPlaylistOperationsDecorator(wrapped, ttl_seconds=10)

        # Populate cache
        decorator.get_all(50)
        assert wrapped.get_all.call_count == 1

        # Create new playlist (should invalidate cache)
        decorator.create("New")

        # Next get_all should hit the API
        decorator.get_all(50)
        assert wrapped.get_all.call_count == 2

    def test_update_invalidates_cache(self):
        """Test that update invalidates cache."""
        wrapped = Mock()
        wrapped.find_by_name.return_value = {"id": "p1"}

        decorator = CachingPlaylistOperationsDecorator(wrapped, ttl_seconds=10)

        decorator.find_by_name("Test")
        assert wrapped.find_by_name.call_count == 1

        decorator.update_details("p1", "New description")

        decorator.find_by_name("Test")
        assert wrapped.find_by_name.call_count == 2

    def test_clear_invalidates_cache(self):
        """Test that clear invalidates cache."""
        wrapped = Mock()
        wrapped.get_all.return_value = [{"id": "p1"}]

        decorator = CachingPlaylistOperationsDecorator(wrapped, ttl_seconds=10)

        decorator.get_all(50)
        decorator.clear("p1")
        decorator.get_all(50)

        assert wrapped.get_all.call_count == 2

    def test_manual_cache_clear(self):
        """Test manual cache clearing."""
        wrapped = Mock()
        wrapped.get_all.return_value = [{"id": "p1"}]

        decorator = CachingPlaylistOperationsDecorator(wrapped, ttl_seconds=10)

        decorator.get_all(50)
        decorator.clear_cache()
        decorator.get_all(50)

        assert wrapped.get_all.call_count == 2

    def test_different_parameters_different_cache(self):
        """Test that different parameters use different cache entries."""
        wrapped = Mock()
        wrapped.get_all.side_effect = [[{"id": "p1"}], [{"id": "p1"}, {"id": "p2"}]]

        decorator = CachingPlaylistOperationsDecorator(wrapped, ttl_seconds=10)

        result1 = decorator.get_all(50)
        result2 = decorator.get_all(100)

        assert len(result1) == 1
        assert len(result2) == 2
        assert wrapped.get_all.call_count == 2


class TestDecoratorComposition:
    """Test composing multiple decorators."""

    def test_logging_and_retry_composition(self, caplog):
        """Test composing logging and retry decorators."""
        wrapped = Mock()
        wrapped.create.side_effect = [Exception("Error"), {"id": "test"}]

        with caplog.at_level(logging.INFO):
            # Compose: Logging wraps Retry wraps actual service
            retry_decorator = RetryPlaylistOperationsDecorator(
                wrapped, max_retries=2, base_delay=0.01
            )
            logging_decorator = LoggingPlaylistOperationsDecorator(retry_decorator)

            result = logging_decorator.create("Test")

        assert result["id"] == "test"
        assert "Creating playlist" in caplog.text
        assert "Playlist created successfully" in caplog.text

    def test_metrics_and_caching_composition(self):
        """Test composing metrics and caching decorators."""
        wrapped = Mock()
        wrapped.get_all.return_value = [{"id": "p1"}]

        # Compose: Metrics wraps Caching wraps actual service
        caching_decorator = CachingPlaylistOperationsDecorator(wrapped, ttl_seconds=10)
        metrics_decorator = MetricsPlaylistOperationsDecorator(caching_decorator)

        # Call twice
        metrics_decorator.get_all(50)
        metrics_decorator.get_all(50)

        # Metrics should show 2 calls (it doesn't know about caching)
        metrics = metrics_decorator.get_metrics()
        assert metrics["get_all"]["calls"] == 2

        # But wrapped service should only be called once (due to caching)
        assert wrapped.get_all.call_count == 1

    def test_full_decorator_stack(self):
        """Test full decorator stack: Logging -> Retry -> Metrics -> Caching -> Service."""
        wrapped = Mock()
        wrapped.create.return_value = {"id": "test"}

        # Build the stack
        caching = CachingPlaylistOperationsDecorator(wrapped, ttl_seconds=10)
        metrics = MetricsPlaylistOperationsDecorator(caching)
        retry = RetryPlaylistOperationsDecorator(metrics, max_retries=3, base_delay=0.01)
        logging_dec = LoggingPlaylistOperationsDecorator(retry)

        # Use the fully decorated service
        result = logging_dec.create("Test")

        assert result["id"] == "test"

        # All decorators should have been applied
        assert wrapped.create.call_count == 1
        assert metrics.get_metrics()["create"]["calls"] == 1
