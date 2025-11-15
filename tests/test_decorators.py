"""Tests for Decorator Pattern."""

import time
from unittest.mock import Mock

import pytest

from spotichart.domain.decorators import (
    CachingPlaylistDecorator,
    LoggingPlaylistDecorator,
    MetricsPlaylistDecorator,
    RetryPlaylistDecorator,
)


class TestLoggingPlaylistDecorator:
    """Tests for LoggingPlaylistDecorator."""

    def test_create_logs_operation(self):
        """Test that create operation is logged."""
        mock_ops = Mock()
        mock_ops.create.return_value = {"id": "playlist123"}
        mock_logger = Mock()

        decorator = LoggingPlaylistDecorator(mock_ops, logger_instance=mock_logger)
        result = decorator.create("Test Playlist", "Description", public=True)

        assert result == {"id": "playlist123"}
        assert mock_logger.info.call_count >= 2  # Start and success logs
        mock_ops.create.assert_called_once_with("Test Playlist", "Description", True)

    def test_create_logs_error(self):
        """Test that create errors are logged."""
        mock_ops = Mock()
        mock_ops.create.side_effect = Exception("Create failed")
        mock_logger = Mock()

        decorator = LoggingPlaylistDecorator(mock_ops, logger_instance=mock_logger)

        with pytest.raises(Exception, match="Create failed"):
            decorator.create("Test", "Desc")

        assert mock_logger.error.call_count >= 1

    def test_find_by_name_logs(self):
        """Test that find_by_name is logged."""
        mock_ops = Mock()
        mock_ops.find_by_name.return_value = {"id": "123"}
        mock_logger = Mock()

        decorator = LoggingPlaylistDecorator(mock_ops, logger_instance=mock_logger)
        result = decorator.find_by_name("Test")

        assert result == {"id": "123"}
        assert mock_logger.debug.call_count >= 2

    def test_find_by_name_not_found_logs(self):
        """Test that not found is logged."""
        mock_ops = Mock()
        mock_ops.find_by_name.return_value = None
        mock_logger = Mock()

        decorator = LoggingPlaylistDecorator(mock_ops, logger_instance=mock_logger)
        result = decorator.find_by_name("NotFound")

        assert result is None
        assert mock_logger.debug.call_count >= 2

    def test_clear_logs(self):
        """Test that clear is logged."""
        mock_ops = Mock()
        mock_ops.clear.return_value = True
        mock_logger = Mock()

        decorator = LoggingPlaylistDecorator(mock_ops, logger_instance=mock_logger)
        result = decorator.clear("playlist123")

        assert result is True
        assert mock_logger.info.call_count >= 2

    def test_update_details_logs(self):
        """Test that update_details is logged."""
        mock_ops = Mock()
        mock_logger = Mock()

        decorator = LoggingPlaylistDecorator(mock_ops, logger_instance=mock_logger)
        decorator.update_details("123", "New description")

        assert mock_logger.debug.call_count >= 1

    def test_get_all_logs(self):
        """Test that get_all is logged."""
        mock_ops = Mock()
        mock_ops.get_all.return_value = [{"id": "1"}, {"id": "2"}]
        mock_logger = Mock()

        decorator = LoggingPlaylistDecorator(mock_ops, logger_instance=mock_logger)
        result = decorator.get_all(limit=50)

        assert len(result) == 2
        assert mock_logger.debug.call_count >= 2


class TestMetricsPlaylistDecorator:
    """Tests for MetricsPlaylistDecorator."""

    def test_initial_metrics(self):
        """Test that initial metrics are zero."""
        mock_ops = Mock()
        decorator = MetricsPlaylistDecorator(mock_ops)

        metrics = decorator.get_metrics()

        assert metrics["creates"] == 0
        assert metrics["finds"] == 0
        assert metrics["clears"] == 0
        assert metrics["updates"] == 0
        assert metrics["get_alls"] == 0
        assert metrics["errors"] == 0

    def test_create_increments_metric(self):
        """Test that create increments metric."""
        mock_ops = Mock()
        mock_ops.create.return_value = {"id": "123"}

        decorator = MetricsPlaylistDecorator(mock_ops)
        decorator.create("Test", "Desc")

        metrics = decorator.get_metrics()
        assert metrics["creates"] == 1

    def test_create_error_increments_error_metric(self):
        """Test that create error increments error metric."""
        mock_ops = Mock()
        mock_ops.create.side_effect = Exception("Failed")

        decorator = MetricsPlaylistDecorator(mock_ops)

        with pytest.raises(Exception):
            decorator.create("Test", "Desc")

        metrics = decorator.get_metrics()
        assert metrics["creates"] == 0
        assert metrics["errors"] == 1

    def test_find_by_name_increments_metric(self):
        """Test that find_by_name increments metric."""
        mock_ops = Mock()
        decorator = MetricsPlaylistDecorator(mock_ops)

        decorator.find_by_name("Test")

        metrics = decorator.get_metrics()
        assert metrics["finds"] == 1

    def test_clear_increments_metric(self):
        """Test that clear increments metric."""
        mock_ops = Mock()
        decorator = MetricsPlaylistDecorator(mock_ops)

        decorator.clear("123")

        metrics = decorator.get_metrics()
        assert metrics["clears"] == 1

    def test_clear_error_increments_error_metric(self):
        """Test that clear error increments error metric."""
        mock_ops = Mock()
        mock_ops.clear.side_effect = Exception("Failed")

        decorator = MetricsPlaylistDecorator(mock_ops)

        with pytest.raises(Exception):
            decorator.clear("123")

        metrics = decorator.get_metrics()
        assert metrics["errors"] == 1

    def test_update_details_increments_metric(self):
        """Test that update_details increments metric."""
        mock_ops = Mock()
        decorator = MetricsPlaylistDecorator(mock_ops)

        decorator.update_details("123", "Desc")

        metrics = decorator.get_metrics()
        assert metrics["updates"] == 1

    def test_get_all_increments_metric(self):
        """Test that get_all increments metric."""
        mock_ops = Mock()
        decorator = MetricsPlaylistDecorator(mock_ops)

        decorator.get_all()

        metrics = decorator.get_metrics()
        assert metrics["get_alls"] == 1

    def test_reset_metrics(self):
        """Test resetting metrics."""
        mock_ops = Mock()
        decorator = MetricsPlaylistDecorator(mock_ops)

        decorator.create("Test", "Desc")
        decorator.find_by_name("Test")

        decorator.reset_metrics()

        metrics = decorator.get_metrics()
        assert metrics["creates"] == 0
        assert metrics["finds"] == 0

    def test_get_metrics_returns_copy(self):
        """Test that get_metrics returns a copy."""
        mock_ops = Mock()
        decorator = MetricsPlaylistDecorator(mock_ops)

        metrics1 = decorator.get_metrics()
        metrics1["creates"] = 999

        metrics2 = decorator.get_metrics()
        assert metrics2["creates"] == 0


class TestRetryPlaylistDecorator:
    """Tests for RetryPlaylistDecorator."""

    def test_create_succeeds_first_try(self):
        """Test that successful operation doesn't retry."""
        mock_ops = Mock()
        mock_ops.create.return_value = {"id": "123"}

        decorator = RetryPlaylistDecorator(mock_ops, max_retries=3, delay=0.01)
        result = decorator.create("Test", "Desc")

        assert result == {"id": "123"}
        assert mock_ops.create.call_count == 1

    def test_create_retries_on_failure(self):
        """Test that failed operation retries."""
        mock_ops = Mock()
        mock_ops.create.side_effect = [
            Exception("Fail 1"),
            Exception("Fail 2"),
            {"id": "123"},  # Success on 3rd try
        ]

        decorator = RetryPlaylistDecorator(mock_ops, max_retries=3, delay=0.01)
        result = decorator.create("Test", "Desc")

        assert result == {"id": "123"}
        assert mock_ops.create.call_count == 3

    def test_create_fails_after_max_retries(self):
        """Test that operation fails after max retries."""
        mock_ops = Mock()
        mock_ops.create.side_effect = Exception("Always fails")

        decorator = RetryPlaylistDecorator(mock_ops, max_retries=3, delay=0.01)

        with pytest.raises(Exception, match="Always fails"):
            decorator.create("Test", "Desc")

        assert mock_ops.create.call_count == 3

    def test_exponential_backoff(self):
        """Test that retry uses exponential backoff."""
        mock_ops = Mock()
        mock_ops.create.side_effect = [Exception("Fail 1"), {"id": "123"}]

        decorator = RetryPlaylistDecorator(mock_ops, max_retries=3, delay=0.01)

        start = time.time()
        decorator.create("Test", "Desc")
        duration = time.time() - start

        # Should have at least one delay (0.01 * 1 = 0.01 seconds)
        assert duration >= 0.01

    def test_find_by_name_retries(self):
        """Test that find_by_name retries."""
        mock_ops = Mock()
        mock_ops.find_by_name.side_effect = [Exception("Fail"), {"id": "123"}]

        decorator = RetryPlaylistDecorator(mock_ops, max_retries=2, delay=0.01)
        result = decorator.find_by_name("Test")

        assert result == {"id": "123"}
        assert mock_ops.find_by_name.call_count == 2

    def test_clear_retries(self):
        """Test that clear retries."""
        mock_ops = Mock()
        mock_ops.clear.side_effect = [Exception("Fail"), True]

        decorator = RetryPlaylistDecorator(mock_ops, max_retries=2, delay=0.01)
        result = decorator.clear("123")

        assert result is True
        assert mock_ops.clear.call_count == 2

    def test_update_details_retries(self):
        """Test that update_details retries."""
        mock_ops = Mock()
        mock_ops.update_details.side_effect = [Exception("Fail"), None]

        decorator = RetryPlaylistDecorator(mock_ops, max_retries=2, delay=0.01)
        decorator.update_details("123", "Desc")

        assert mock_ops.update_details.call_count == 2

    def test_get_all_retries(self):
        """Test that get_all retries."""
        mock_ops = Mock()
        mock_ops.get_all.side_effect = [Exception("Fail"), [{"id": "1"}]]

        decorator = RetryPlaylistDecorator(mock_ops, max_retries=2, delay=0.01)
        result = decorator.get_all()

        assert len(result) == 1
        assert mock_ops.get_all.call_count == 2


class TestCachingPlaylistDecorator:
    """Tests for CachingPlaylistDecorator."""

    def test_find_by_name_caches_result(self):
        """Test that find_by_name caches results."""
        mock_ops = Mock()
        mock_ops.find_by_name.return_value = {"id": "123"}

        decorator = CachingPlaylistDecorator(mock_ops, cache_ttl_seconds=60)

        # First call
        result1 = decorator.find_by_name("Test")
        # Second call should use cache
        result2 = decorator.find_by_name("Test")

        assert result1 == result2
        assert mock_ops.find_by_name.call_count == 1  # Only called once

    def test_find_by_name_different_keys(self):
        """Test that different names have different cache keys."""
        mock_ops = Mock()
        mock_ops.find_by_name.return_value = {"id": "123"}

        decorator = CachingPlaylistDecorator(mock_ops)

        decorator.find_by_name("Test1")
        decorator.find_by_name("Test2")

        assert mock_ops.find_by_name.call_count == 2

    def test_cache_ttl_expires(self):
        """Test that cache expires after TTL."""
        mock_ops = Mock()
        mock_ops.find_by_name.return_value = {"id": "123"}

        decorator = CachingPlaylistDecorator(mock_ops, cache_ttl_seconds=0.05)

        decorator.find_by_name("Test")
        time.sleep(0.1)  # Wait for TTL to expire
        decorator.find_by_name("Test")

        assert mock_ops.find_by_name.call_count == 2  # Called twice due to expiry

    def test_get_all_caches_result(self):
        """Test that get_all caches results."""
        mock_ops = Mock()
        mock_ops.get_all.return_value = [{"id": "1"}]

        decorator = CachingPlaylistDecorator(mock_ops)

        result1 = decorator.get_all(limit=50)
        result2 = decorator.get_all(limit=50)

        assert result1 == result2
        assert mock_ops.get_all.call_count == 1

    def test_get_all_different_limits(self):
        """Test that different limits have different cache keys."""
        mock_ops = Mock()
        mock_ops.get_all.return_value = [{"id": "1"}]

        decorator = CachingPlaylistDecorator(mock_ops)

        decorator.get_all(limit=10)
        decorator.get_all(limit=20)

        assert mock_ops.get_all.call_count == 2

    def test_create_invalidates_cache(self):
        """Test that create invalidates cache."""
        mock_ops = Mock()
        mock_ops.find_by_name.return_value = {"id": "123"}
        mock_ops.create.return_value = {"id": "new"}

        decorator = CachingPlaylistDecorator(mock_ops)

        # Populate cache
        decorator.find_by_name("Test")
        assert mock_ops.find_by_name.call_count == 1

        # Create should invalidate
        decorator.create("New", "Desc")

        # Should call again (cache invalidated)
        decorator.find_by_name("Test")
        assert mock_ops.find_by_name.call_count == 2

    def test_clear_invalidates_cache(self):
        """Test that clear invalidates cache."""
        mock_ops = Mock()
        mock_ops.get_all.return_value = [{"id": "1"}]

        decorator = CachingPlaylistDecorator(mock_ops)

        decorator.get_all()
        decorator.clear("123")
        decorator.get_all()

        assert mock_ops.get_all.call_count == 2

    def test_update_details_invalidates_cache(self):
        """Test that update_details invalidates cache."""
        mock_ops = Mock()
        mock_ops.find_by_name.return_value = {"id": "123"}

        decorator = CachingPlaylistDecorator(mock_ops)

        decorator.find_by_name("Test")
        decorator.update_details("123", "New desc")
        decorator.find_by_name("Test")

        assert mock_ops.find_by_name.call_count == 2


class TestDecoratorStacking:
    """Tests for stacking multiple decorators."""

    def test_logging_and_metrics(self):
        """Test stacking logging and metrics decorators."""
        mock_ops = Mock()
        mock_ops.create.return_value = {"id": "123"}
        mock_logger = Mock()

        # Stack decorators: Metrics -> Logging -> Operations
        decorator = MetricsPlaylistDecorator(
            LoggingPlaylistDecorator(mock_ops, logger_instance=mock_logger)
        )

        result = decorator.create("Test", "Desc")

        assert result == {"id": "123"}
        assert decorator.get_metrics()["creates"] == 1
        assert mock_logger.info.call_count >= 2

    def test_retry_and_caching(self):
        """Test stacking retry and caching decorators."""
        mock_ops = Mock()
        mock_ops.find_by_name.return_value = {"id": "123"}

        # Stack: Caching -> Retry -> Operations
        decorator = CachingPlaylistDecorator(
            RetryPlaylistDecorator(mock_ops, max_retries=3, delay=0.01)
        )

        decorator.find_by_name("Test")
        decorator.find_by_name("Test")  # Should use cache

        # Only one call due to caching
        assert mock_ops.find_by_name.call_count == 1

    def test_all_decorators_stacked(self):
        """Test stacking all decorators together."""
        mock_ops = Mock()
        mock_ops.create.return_value = {"id": "123"}
        mock_logger = Mock()

        # Stack: Metrics -> Logging -> Retry -> Caching -> Operations
        decorator = MetricsPlaylistDecorator(
            LoggingPlaylistDecorator(
                RetryPlaylistDecorator(
                    CachingPlaylistDecorator(mock_ops), max_retries=3, delay=0.01
                ),
                logger_instance=mock_logger,
            )
        )

        result = decorator.create("Test", "Desc")

        assert result == {"id": "123"}
        assert decorator.get_metrics()["creates"] == 1
        assert mock_logger.info.call_count >= 2
        assert mock_ops.create.call_count == 1
