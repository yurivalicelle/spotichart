"""
Tests for Repository Pattern
"""

import pytest
from unittest.mock import Mock

from spotichart.core.playlist_cache import PlaylistCache
from spotichart.core.repositories import CachedPlaylistRepository


class TestCachedPlaylistRepository:
    """Test CachedPlaylistRepository."""

    def test_initialization(self):
        """Repository should initialize with dependencies."""
        playlist_reader = Mock()
        cache = Mock()

        repo = CachedPlaylistRepository(playlist_reader=playlist_reader, cache=cache)

        assert repo._reader == playlist_reader
        assert repo._cache == cache

    def test_initialization_default_cache(self):
        """Repository should create default cache if not provided."""
        playlist_reader = Mock()

        repo = CachedPlaylistRepository(playlist_reader=playlist_reader)

        assert repo._reader == playlist_reader
        assert isinstance(repo._cache, PlaylistCache)

    def test_find_by_name_cache_hit(self):
        """find_by_name should return cached playlist."""
        playlist_reader = Mock()
        cache = Mock()
        cache.get.return_value = {"id": "cached_id", "name": "My Playlist"}

        repo = CachedPlaylistRepository(playlist_reader=playlist_reader, cache=cache)

        result = repo.find_by_name("My Playlist")

        assert result is not None
        assert result["id"] == "cached_id"
        assert result["name"] == "My Playlist"
        # Should not fetch from reader
        playlist_reader.current_user_playlists.assert_not_called()

    def test_find_by_name_cache_miss(self):
        """find_by_name should fetch from API on cache miss."""
        playlist_reader = Mock()
        playlist_reader.current_user_playlists.return_value = {
            "items": [
                {"id": "pl1", "name": "Other Playlist"},
                {"id": "pl2", "name": "My Playlist"},
            ],
            "next": None,
        }
        playlist_reader.next.return_value = None

        cache = Mock()
        cache.get.return_value = None

        repo = CachedPlaylistRepository(playlist_reader=playlist_reader, cache=cache)

        result = repo.find_by_name("My Playlist")

        assert result is not None
        assert result["id"] == "pl2"
        assert result["name"] == "My Playlist"

        # Should cache the result
        cache.set.assert_called_with("My Playlist", result)

    def test_find_by_name_not_found(self):
        """find_by_name should return None if not found."""
        playlist_reader = Mock()
        playlist_reader.current_user_playlists.return_value = {
            "items": [{"id": "pl1", "name": "Other Playlist"}],
            "next": None,
        }

        cache = Mock()
        cache.get.return_value = None

        repo = CachedPlaylistRepository(playlist_reader=playlist_reader, cache=cache)

        result = repo.find_by_name("Nonexistent")

        assert result is None

    def test_find_by_name_pagination(self):
        """find_by_name should handle pagination."""
        playlist_reader = Mock()
        first_page = {
            "items": [{"id": "pl1", "name": "Playlist 1"}],
            "next": "url",
        }
        second_page = {
            "items": [{"id": "pl2", "name": "Target Playlist"}],
            "next": None,
        }

        playlist_reader.current_user_playlists.return_value = first_page
        playlist_reader.next.side_effect = [second_page, None]

        cache = Mock()
        cache.get.return_value = None

        repo = CachedPlaylistRepository(playlist_reader=playlist_reader, cache=cache)

        result = repo.find_by_name("Target Playlist")

        assert result is not None
        assert result["id"] == "pl2"

    def test_find_by_id_from_cache(self):
        """find_by_id should search in cached playlists."""
        playlist_reader = Mock()
        cache = Mock()

        repo = CachedPlaylistRepository(playlist_reader=playlist_reader, cache=cache)

        # Populate cache by calling get_all
        playlist_reader.current_user_playlists.return_value = {
            "items": [
                {"id": "pl1", "name": "Playlist 1"},
                {"id": "pl2", "name": "Playlist 2"},
            ],
            "next": None,
        }
        repo.get_all()

        # Now find by id
        result = repo.find_by_id("pl2")

        assert result is not None
        assert result["id"] == "pl2"
        assert result["name"] == "Playlist 2"

    def test_find_by_id_not_found(self):
        """find_by_id should return None if not found."""
        playlist_reader = Mock()
        playlist_reader.current_user_playlists.return_value = {
            "items": [{"id": "pl1", "name": "Playlist 1"}],
            "next": None,
        }

        cache = Mock()

        repo = CachedPlaylistRepository(playlist_reader=playlist_reader, cache=cache)

        result = repo.find_by_id("nonexistent")

        assert result is None

    def test_save(self):
        """save should cache playlist."""
        playlist_reader = Mock()
        cache = Mock()

        repo = CachedPlaylistRepository(playlist_reader=playlist_reader, cache=cache)

        playlist = {"id": "pl1", "name": "My Playlist"}
        repo.save(playlist)

        cache.set.assert_called_once_with("My Playlist", playlist)

    def test_save_invalidates_cache(self):
        """save should invalidate all playlists cache."""
        playlist_reader = Mock()
        cache = Mock()

        repo = CachedPlaylistRepository(playlist_reader=playlist_reader, cache=cache)

        # Populate cache
        playlist_reader.current_user_playlists.return_value = {
            "items": [{"id": "pl1", "name": "Playlist 1"}],
            "next": None,
        }
        repo.get_all()

        # Save should invalidate
        repo.save({"id": "pl2", "name": "New Playlist"})

        # Next get_all should fetch again
        playlist_reader.current_user_playlists.return_value = {
            "items": [
                {"id": "pl1", "name": "Playlist 1"},
                {"id": "pl2", "name": "New Playlist"},
            ],
            "next": None,
        }

        result = repo.get_all()
        assert len(result) == 2

    def test_get_all(self):
        """get_all should fetch playlists."""
        playlist_reader = Mock()
        playlist_reader.current_user_playlists.return_value = {
            "items": [
                {"id": "pl1", "name": "Playlist 1"},
                {"id": "pl2", "name": "Playlist 2"},
            ],
            "next": None,
        }

        cache = Mock()

        repo = CachedPlaylistRepository(playlist_reader=playlist_reader, cache=cache)

        result = repo.get_all()

        assert len(result) == 2
        assert result[0]["id"] == "pl1"
        assert result[1]["id"] == "pl2"

        # Should cache individual playlists
        assert cache.set.call_count == 2

    def test_get_all_cached(self):
        """get_all should return cached results."""
        playlist_reader = Mock()
        playlist_reader.current_user_playlists.return_value = {
            "items": [{"id": "pl1", "name": "Playlist 1"}],
            "next": None,
        }

        cache = Mock()

        repo = CachedPlaylistRepository(playlist_reader=playlist_reader, cache=cache)

        # First call
        result1 = repo.get_all()

        # Second call should use cache
        result2 = repo.get_all()

        assert result1 == result2
        # Should only call API once
        playlist_reader.current_user_playlists.assert_called_once()

    def test_get_all_with_limit(self):
        """get_all should respect limit."""
        playlist_reader = Mock()
        playlist_reader.current_user_playlists.return_value = {
            "items": [
                {"id": f"pl{i}", "name": f"Playlist {i}"} for i in range(1, 101)
            ],
            "next": None,
        }

        cache = Mock()

        repo = CachedPlaylistRepository(playlist_reader=playlist_reader, cache=cache)

        result = repo.get_all(limit=50)

        assert len(result) == 50

    def test_clear_cache(self):
        """clear_cache should clear all cached data."""
        playlist_reader = Mock()

        repo = CachedPlaylistRepository(playlist_reader=playlist_reader)

        # Populate cache
        playlist_reader.current_user_playlists.return_value = {
            "items": [{"id": "pl1", "name": "Playlist 1"}],
            "next": None,
        }
        repo.get_all()

        # Clear cache
        repo.clear_cache()

        # Next call should fetch again
        result = repo.get_all()
        assert playlist_reader.current_user_playlists.call_count == 2
