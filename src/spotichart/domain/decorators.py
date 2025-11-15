"""
Decorator Pattern

Add responsibilities to objects dynamically.
"""

import logging
import time
from typing import Dict, List, Optional

from ..core.interfaces import IPlaylistOperations
from ..utils.exceptions import PlaylistCreationError

logger = logging.getLogger(__name__)


class LoggingPlaylistDecorator(IPlaylistOperations):
    """Decorator that adds logging to playlist operations."""

    def __init__(self, wrapped: IPlaylistOperations, logger_instance: logging.Logger = None):
        """
        Initialize logging decorator.

        Args:
            wrapped: Playlist operations to wrap
            logger_instance: Logger to use (defaults to module logger)
        """
        self._wrapped = wrapped
        self._logger = logger_instance or logger

    def create(self, name: str, description: str, public: bool = False):
        """Create playlist with logging."""
        self._logger.info(f"Creating playlist: {name} (public={public})")
        start = time.time()

        try:
            result = self._wrapped.create(name, description, public)
            duration = time.time() - start
            self._logger.info(f"Playlist created successfully in {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start
            self._logger.error(f"Failed to create playlist after {duration:.2f}s: {e}")
            raise

    def find_by_name(self, name: str):
        """Find playlist by name with logging."""
        self._logger.debug(f"Finding playlist by name: {name}")
        result = self._wrapped.find_by_name(name)

        if result:
            self._logger.debug(f"Found playlist: {result.get('id')}")
        else:
            self._logger.debug(f"Playlist not found: {name}")

        return result

    def clear(self, playlist_id: str):
        """Clear playlist with logging."""
        self._logger.info(f"Clearing playlist: {playlist_id}")
        result = self._wrapped.clear(playlist_id)
        self._logger.info(f"Playlist cleared: {result}")
        return result

    def update_details(self, playlist_id: str, description: str):
        """Update playlist details with logging."""
        self._logger.debug(f"Updating playlist {playlist_id} details")
        return self._wrapped.update_details(playlist_id, description)

    def get_all(self, limit: int = 50):
        """Get all playlists with logging."""
        self._logger.debug(f"Fetching up to {limit} playlists")
        result = self._wrapped.get_all(limit)
        self._logger.debug(f"Retrieved {len(result)} playlists")
        return result


class MetricsPlaylistDecorator(IPlaylistOperations):
    """Decorator that collects metrics from playlist operations."""

    def __init__(self, wrapped: IPlaylistOperations):
        """
        Initialize metrics decorator.

        Args:
            wrapped: Playlist operations to wrap
        """
        self._wrapped = wrapped
        self._metrics: Dict[str, int] = {
            "creates": 0,
            "finds": 0,
            "clears": 0,
            "updates": 0,
            "get_alls": 0,
            "errors": 0,
        }

    def create(self, name: str, description: str, public: bool = False):
        """Create playlist and record metric."""
        try:
            result = self._wrapped.create(name, description, public)
            self._metrics["creates"] += 1
            return result
        except Exception:
            self._metrics["errors"] += 1
            raise

    def find_by_name(self, name: str):
        """Find playlist and record metric."""
        self._metrics["finds"] += 1
        return self._wrapped.find_by_name(name)

    def clear(self, playlist_id: str):
        """Clear playlist and record metric."""
        try:
            result = self._wrapped.clear(playlist_id)
            self._metrics["clears"] += 1
            return result
        except Exception:
            self._metrics["errors"] += 1
            raise

    def update_details(self, playlist_id: str, description: str):
        """Update details and record metric."""
        self._metrics["updates"] += 1
        return self._wrapped.update_details(playlist_id, description)

    def get_all(self, limit: int = 50):
        """Get all and record metric."""
        self._metrics["get_alls"] += 1
        return self._wrapped.get_all(limit)

    def get_metrics(self) -> Dict[str, int]:
        """Get collected metrics."""
        return self._metrics.copy()

    def reset_metrics(self) -> None:
        """Reset all metrics to zero."""
        for key in self._metrics:
            self._metrics[key] = 0


class RetryPlaylistDecorator(IPlaylistOperations):
    """Decorator that adds retry logic to playlist operations."""

    def __init__(self, wrapped: IPlaylistOperations, max_retries: int = 3, delay: float = 1.0):
        """
        Initialize retry decorator.

        Args:
            wrapped: Playlist operations to wrap
            max_retries: Maximum number of retries
            delay: Delay between retries in seconds
        """
        self._wrapped = wrapped
        self._max_retries = max_retries
        self._delay = delay

    def create(self, name: str, description: str, public: bool = False):
        """Create playlist with retry logic."""
        return self._retry_operation(
            lambda: self._wrapped.create(name, description, public), "create"
        )

    def find_by_name(self, name: str):
        """Find playlist with retry logic."""
        return self._retry_operation(lambda: self._wrapped.find_by_name(name), "find_by_name")

    def clear(self, playlist_id: str):
        """Clear playlist with retry logic."""
        return self._retry_operation(lambda: self._wrapped.clear(playlist_id), "clear")

    def update_details(self, playlist_id: str, description: str):
        """Update details with retry logic."""
        return self._retry_operation(
            lambda: self._wrapped.update_details(playlist_id, description), "update_details"
        )

    def get_all(self, limit: int = 50):
        """Get all with retry logic."""
        return self._retry_operation(lambda: self._wrapped.get_all(limit), "get_all")

    def _retry_operation(self, operation, operation_name: str):
        """Execute operation with retry logic."""
        last_error = None

        for attempt in range(1, self._max_retries + 1):
            try:
                return operation()
            except Exception as e:
                last_error = e
                logger.warning(
                    f"{operation_name} failed (attempt {attempt}/{self._max_retries}): {e}"
                )

                if attempt < self._max_retries:
                    time.sleep(self._delay * attempt)  # Exponential backoff

        logger.error(f"{operation_name} failed after {self._max_retries} attempts")
        raise last_error


class CachingPlaylistDecorator(IPlaylistOperations):
    """Decorator that adds caching to playlist operations."""

    def __init__(self, wrapped: IPlaylistOperations, cache_ttl_seconds: int = 300):
        """
        Initialize caching decorator.

        Args:
            wrapped: Playlist operations to wrap
            cache_ttl_seconds: Cache time-to-live in seconds
        """
        self._wrapped = wrapped
        self._cache: Dict[str, tuple] = {}  # {key: (value, timestamp)}
        self._cache_ttl = cache_ttl_seconds

    def create(self, name: str, description: str, public: bool = False):
        """Create playlist and invalidate cache."""
        result = self._wrapped.create(name, description, public)
        self._invalidate_cache()
        return result

    def find_by_name(self, name: str):
        """Find playlist with caching."""
        cache_key = f"find:{name}"

        # Check cache
        if cache_key in self._cache:
            cached_value, cached_time = self._cache[cache_key]
            if time.time() - cached_time < self._cache_ttl:
                logger.debug(f"Cache hit for: {cache_key}")
                return cached_value

        # Cache miss
        result = self._wrapped.find_by_name(name)
        self._cache[cache_key] = (result, time.time())
        return result

    def clear(self, playlist_id: str):
        """Clear playlist and invalidate cache."""
        result = self._wrapped.clear(playlist_id)
        self._invalidate_cache()
        return result

    def update_details(self, playlist_id: str, description: str):
        """Update details and invalidate cache."""
        result = self._wrapped.update_details(playlist_id, description)
        self._invalidate_cache()
        return result

    def get_all(self, limit: int = 50):
        """Get all with caching."""
        cache_key = f"get_all:{limit}"

        # Check cache
        if cache_key in self._cache:
            cached_value, cached_time = self._cache[cache_key]
            if time.time() - cached_time < self._cache_ttl:
                logger.debug(f"Cache hit for: {cache_key}")
                return cached_value

        # Cache miss
        result = self._wrapped.get_all(limit)
        self._cache[cache_key] = (result, time.time())
        return result

    def _invalidate_cache(self) -> None:
        """Invalidate all cache entries."""
        self._cache.clear()
        logger.debug("Cache invalidated")
