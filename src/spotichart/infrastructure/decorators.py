"""
Service Decorators (Decorator Pattern)

Decorators that add cross-cutting concerns to services without modifying them.
Implements Open/Closed Principle and Decorator Pattern.
"""

import logging
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar, cast

from ..core.interfaces import IPlaylistOperations
from ..utils.result import Failure, Result

T = TypeVar("T")
logger = logging.getLogger(__name__)


# ============================================================================
# LOGGING DECORATOR
# ============================================================================


class LoggingPlaylistOperationsDecorator(IPlaylistOperations):
    """
    Decorator that adds logging to playlist operations.

    Logs method calls, parameters, duration, and results.
    """

    def __init__(self, wrapped: IPlaylistOperations, logger_instance: logging.Logger = None):
        """
        Initialize decorator.

        Args:
            wrapped: The service to wrap
            logger_instance: Optional logger (defaults to module logger)
        """
        self._wrapped = wrapped
        self._logger = logger_instance or logger

    def create(self, name: str, description: str = "", public: bool = False) -> Dict:
        """Create playlist with logging."""
        self._logger.info(f"Creating playlist: '{name}' (public={public})")
        start = time.time()
        try:
            result = self._wrapped.create(name, description, public)
            duration = time.time() - start
            self._logger.info(
                f"Playlist created successfully in {duration:.2f}s: {result.get('id', 'unknown')}"
            )
            return result
        except Exception as e:
            duration = time.time() - start
            self._logger.error(f"Failed to create playlist after {duration:.2f}s: {e}")
            raise

    def get_all(self, limit: int = 50) -> list:
        """Get all playlists with logging."""
        self._logger.debug(f"Fetching up to {limit} playlists")
        start = time.time()
        try:
            result = self._wrapped.get_all(limit)
            duration = time.time() - start
            self._logger.debug(f"Fetched {len(result)} playlists in {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start
            self._logger.error(f"Failed to fetch playlists after {duration:.2f}s: {e}")
            raise

    def find_by_name(self, name: str) -> Optional[Dict]:
        """Find playlist by name with logging."""
        self._logger.debug(f"Searching for playlist: '{name}'")
        start = time.time()
        try:
            result = self._wrapped.find_by_name(name)
            duration = time.time() - start
            if result:
                self._logger.debug(f"Found playlist '{name}' in {duration:.2f}s")
            else:
                self._logger.debug(f"Playlist '{name}' not found (searched in {duration:.2f}s)")
            return result
        except Exception as e:
            duration = time.time() - start
            self._logger.error(f"Error searching for playlist after {duration:.2f}s: {e}")
            raise

    def update_details(
        self, playlist_id: str, description: Optional[str] = None, name: Optional[str] = None
    ) -> None:
        """Update playlist details with logging."""
        self._logger.info(f"Updating playlist {playlist_id}")
        start = time.time()
        try:
            self._wrapped.update_details(playlist_id, description, name)
            duration = time.time() - start
            self._logger.info(f"Playlist updated successfully in {duration:.2f}s")
        except Exception as e:
            duration = time.time() - start
            self._logger.error(f"Failed to update playlist after {duration:.2f}s: {e}")
            raise

    def clear(self, playlist_id: str) -> None:
        """Clear playlist with logging."""
        self._logger.info(f"Clearing playlist {playlist_id}")
        start = time.time()
        try:
            self._wrapped.clear(playlist_id)
            duration = time.time() - start
            self._logger.info(f"Playlist cleared successfully in {duration:.2f}s")
        except Exception as e:
            duration = time.time() - start
            self._logger.error(f"Failed to clear playlist after {duration:.2f}s: {e}")
            raise


# ============================================================================
# RETRY DECORATOR
# ============================================================================


class RetryPlaylistOperationsDecorator(IPlaylistOperations):
    """
    Decorator that adds retry logic to playlist operations.

    Retries failed operations with exponential backoff.
    """

    def __init__(
        self,
        wrapped: IPlaylistOperations,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 10.0,
        exponential_base: float = 2.0,
    ):
        """
        Initialize decorator.

        Args:
            wrapped: The service to wrap
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
        """
        self._wrapped = wrapped
        self._max_retries = max_retries
        self._base_delay = base_delay
        self._max_delay = max_delay
        self._exponential_base = exponential_base

    def _retry_operation(self, operation: Callable[[], T], operation_name: str) -> T:
        """
        Execute operation with retry logic.

        Args:
            operation: Function to execute
            operation_name: Name for logging

        Returns:
            Result of operation

        Raises:
            Last exception if all retries fail
        """
        last_exception = None

        for attempt in range(self._max_retries):
            try:
                return operation()
            except Exception as e:
                last_exception = e
                if attempt < self._max_retries - 1:
                    delay = min(
                        self._base_delay * (self._exponential_base**attempt), self._max_delay
                    )
                    logger.warning(
                        f"{operation_name} failed (attempt {attempt + 1}/{self._max_retries}): "
                        f"{e}. Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        f"{operation_name} failed after {self._max_retries} attempts: {e}"
                    )

        raise last_exception  # type: ignore

    def create(self, name: str, description: str = "", public: bool = False) -> Dict:
        """Create playlist with retry."""
        return self._retry_operation(
            lambda: self._wrapped.create(name, description, public), "Create playlist"
        )

    def get_all(self, limit: int = 50) -> list:
        """Get all playlists with retry."""
        return self._retry_operation(lambda: self._wrapped.get_all(limit), "Get all playlists")

    def find_by_name(self, name: str) -> Optional[Dict]:
        """Find playlist by name with retry."""
        return self._retry_operation(
            lambda: self._wrapped.find_by_name(name), f"Find playlist '{name}'"
        )

    def update_details(
        self, playlist_id: str, description: Optional[str] = None, name: Optional[str] = None
    ) -> None:
        """Update playlist details with retry."""
        self._retry_operation(
            lambda: self._wrapped.update_details(playlist_id, description, name),
            "Update playlist details",
        )

    def clear(self, playlist_id: str) -> None:
        """Clear playlist with retry."""
        self._retry_operation(lambda: self._wrapped.clear(playlist_id), "Clear playlist")


# ============================================================================
# METRICS DECORATOR
# ============================================================================


class MetricsPlaylistOperationsDecorator(IPlaylistOperations):
    """
    Decorator that collects metrics about playlist operations.

    Tracks operation counts, success/failure rates, and durations.
    """

    def __init__(self, wrapped: IPlaylistOperations):
        """
        Initialize decorator.

        Args:
            wrapped: The service to wrap
        """
        self._wrapped = wrapped
        self._metrics: Dict[str, Dict[str, Any]] = {
            "create": {"calls": 0, "successes": 0, "failures": 0, "total_duration": 0.0},
            "get_all": {"calls": 0, "successes": 0, "failures": 0, "total_duration": 0.0},
            "find_by_name": {"calls": 0, "successes": 0, "failures": 0, "total_duration": 0.0},
            "update_details": {"calls": 0, "successes": 0, "failures": 0, "total_duration": 0.0},
            "clear": {"calls": 0, "successes": 0, "failures": 0, "total_duration": 0.0},
        }

    def _track_operation(self, operation: Callable[[], T], operation_name: str) -> T:
        """
        Execute operation and track metrics.

        Args:
            operation: Function to execute
            operation_name: Metric key

        Returns:
            Result of operation

        Raises:
            Any exception from operation
        """
        self._metrics[operation_name]["calls"] += 1
        start = time.time()

        try:
            result = operation()
            self._metrics[operation_name]["successes"] += 1
            return result
        except Exception as e:
            self._metrics[operation_name]["failures"] += 1
            raise
        finally:
            duration = time.time() - start
            self._metrics[operation_name]["total_duration"] += duration

    def create(self, name: str, description: str = "", public: bool = False) -> Dict:
        """Create playlist with metrics."""
        return self._track_operation(
            lambda: self._wrapped.create(name, description, public), "create"
        )

    def get_all(self, limit: int = 50) -> list:
        """Get all playlists with metrics."""
        return self._track_operation(lambda: self._wrapped.get_all(limit), "get_all")

    def find_by_name(self, name: str) -> Optional[Dict]:
        """Find playlist by name with metrics."""
        return self._track_operation(lambda: self._wrapped.find_by_name(name), "find_by_name")

    def update_details(
        self, playlist_id: str, description: Optional[str] = None, name: Optional[str] = None
    ) -> None:
        """Update playlist details with metrics."""
        self._track_operation(
            lambda: self._wrapped.update_details(playlist_id, description, name), "update_details"
        )

    def clear(self, playlist_id: str) -> None:
        """Clear playlist with metrics."""
        self._track_operation(lambda: self._wrapped.clear(playlist_id), "clear")

    def get_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get collected metrics.

        Returns:
            Dictionary with metrics for each operation
        """
        # Calculate average durations
        metrics_with_averages = {}
        for operation, data in self._metrics.items():
            metrics_with_averages[operation] = {
                **data,
                "average_duration": (
                    data["total_duration"] / data["calls"] if data["calls"] > 0 else 0.0
                ),
                "success_rate": (
                    data["successes"] / data["calls"] if data["calls"] > 0 else 0.0
                ),
            }

        return metrics_with_averages

    def reset_metrics(self) -> None:
        """Reset all metrics to zero."""
        for operation in self._metrics:
            self._metrics[operation] = {
                "calls": 0,
                "successes": 0,
                "failures": 0,
                "total_duration": 0.0,
            }


# ============================================================================
# CACHING DECORATOR
# ============================================================================


class CachingPlaylistOperationsDecorator(IPlaylistOperations):
    """
    Decorator that adds caching to read operations.

    Caches results to reduce API calls.
    """

    def __init__(self, wrapped: IPlaylistOperations, ttl_seconds: float = 300.0):
        """
        Initialize decorator.

        Args:
            wrapped: The service to wrap
            ttl_seconds: Time-to-live for cache entries
        """
        self._wrapped = wrapped
        self._ttl = ttl_seconds
        self._cache: Dict[str, tuple[Any, float]] = {}

    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached value if not expired."""
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < self._ttl:
                logger.debug(f"Cache hit for: {key}")
                return value
            else:
                logger.debug(f"Cache expired for: {key}")
                del self._cache[key]
        return None

    def _set_cache(self, key: str, value: Any) -> None:
        """Set cached value with timestamp."""
        self._cache[key] = (value, time.time())
        logger.debug(f"Cached: {key}")

    def _invalidate_cache(self) -> None:
        """Invalidate all cache entries."""
        self._cache.clear()
        logger.debug("Cache invalidated")

    def create(self, name: str, description: str = "", public: bool = False) -> Dict:
        """Create playlist (invalidates cache)."""
        result = self._wrapped.create(name, description, public)
        self._invalidate_cache()  # Invalidate cache since playlists changed
        return result

    def get_all(self, limit: int = 50) -> list:
        """Get all playlists (cached)."""
        cache_key = f"get_all_{limit}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        result = self._wrapped.get_all(limit)
        self._set_cache(cache_key, result)
        return result

    def find_by_name(self, name: str) -> Optional[Dict]:
        """Find playlist by name (cached)."""
        cache_key = f"find_by_name_{name}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        result = self._wrapped.find_by_name(name)
        self._set_cache(cache_key, result)
        return result

    def update_details(
        self, playlist_id: str, description: Optional[str] = None, name: Optional[str] = None
    ) -> None:
        """Update playlist details (invalidates cache)."""
        self._wrapped.update_details(playlist_id, description, name)
        self._invalidate_cache()

    def clear(self, playlist_id: str) -> None:
        """Clear playlist (invalidates cache)."""
        self._wrapped.clear(playlist_id)
        self._invalidate_cache()

    def clear_cache(self) -> None:
        """Manually clear cache."""
        self._invalidate_cache()
