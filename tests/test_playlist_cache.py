"""Tests for PlaylistCache."""

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from spotichart.core.playlist_cache import PlaylistCache


@pytest.fixture
def temp_cache_file(tmp_path):
    """Create a temporary cache file."""
    cache_file = tmp_path / "playlists.json"
    return cache_file


@pytest.fixture
def cache_with_data(temp_cache_file):
    """Create cache with initial data."""
    initial_data = {
        "test playlist": {
            "playlist": {"id": "p_123", "name": "Test Playlist"},
            "cached_at": datetime.now().isoformat(),
        },
        "another playlist": {
            "playlist": {"id": "p_456", "name": "Another Playlist"},
            "cached_at": datetime.now().isoformat(),
        },
    }
    temp_cache_file.write_text(json.dumps(initial_data))
    return temp_cache_file


class TestPlaylistCacheInit:
    """Tests for PlaylistCache initialization."""

    def test_init_with_file(self, temp_cache_file):
        """Should initialize with cache file."""
        cache = PlaylistCache(cache_file=temp_cache_file, ttl_hours=24)

        assert cache.cache_file == temp_cache_file
        assert cache.ttl == timedelta(hours=24)

    def test_init_without_file(self):
        """Should initialize without cache file (in-memory only)."""
        cache = PlaylistCache(cache_file=None, ttl_hours=12)

        assert cache.cache_file is None
        assert cache.ttl == timedelta(hours=12)

    def test_init_custom_ttl(self, temp_cache_file):
        """Should initialize with custom TTL."""
        cache = PlaylistCache(cache_file=temp_cache_file, ttl_hours=48)

        assert cache.ttl == timedelta(hours=48)


class TestPlaylistCacheLoadFromFile:
    """Tests for loading cache from file."""

    def test_load_existing_cache(self, cache_with_data):
        """Should load existing cache data."""
        cache = PlaylistCache(cache_file=cache_with_data, ttl_hours=24)

        # Should have loaded the data
        playlist = cache.get("test playlist")
        assert playlist is not None
        assert playlist["id"] == "p_123"

    def test_load_nonexistent_file(self, tmp_path):
        """Should handle nonexistent file gracefully."""
        cache_file = tmp_path / "nonexistent.json"
        cache = PlaylistCache(cache_file=cache_file, ttl_hours=24)

        # Should not crash
        assert cache._cache == {}

    def test_load_invalid_json(self, temp_cache_file):
        """Should handle invalid JSON gracefully."""
        temp_cache_file.write_text("invalid json content {{{")

        cache = PlaylistCache(cache_file=temp_cache_file, ttl_hours=24)

        # Should fallback to empty cache
        assert cache._cache == {}

    def test_load_filters_expired_entries(self, temp_cache_file):
        """Should filter out expired cache entries."""
        old_time = (datetime.now() - timedelta(hours=48)).isoformat()
        recent_time = datetime.now().isoformat()

        cache_data = {
            "old playlist": {"playlist": {"id": "old_123"}, "cached_at": old_time},
            "recent playlist": {"playlist": {"id": "recent_123"}, "cached_at": recent_time},
        }
        temp_cache_file.write_text(json.dumps(cache_data))

        cache = PlaylistCache(cache_file=temp_cache_file, ttl_hours=24)

        # Old entry should be filtered out
        assert cache.get("old playlist") is None
        # Recent entry should be loaded
        assert cache.get("recent playlist") is not None

    def test_load_handles_missing_cached_at(self, temp_cache_file):
        """Should handle entries without cached_at field."""
        cache_data = {
            "bad entry": {
                "playlist": {"id": "bad_123"}
                # Missing 'cached_at'
            }
        }
        temp_cache_file.write_text(json.dumps(cache_data))

        # Should not crash
        cache = PlaylistCache(cache_file=temp_cache_file, ttl_hours=24)
        assert cache._cache == {}


class TestPlaylistCacheGet:
    """Tests for get method."""

    def test_get_existing_entry(self):
        """Should retrieve existing cache entry."""
        cache = PlaylistCache(cache_file=None)
        playlist_data = {"id": "p_123", "name": "Test"}
        cache.set("test", playlist_data)

        result = cache.get("test")
        assert result == playlist_data

    def test_get_case_insensitive(self):
        """Should retrieve entry case-insensitively."""
        cache = PlaylistCache(cache_file=None)
        playlist_data = {"id": "p_123"}
        cache.set("Test Playlist", playlist_data)

        # Different case should work
        result = cache.get("test playlist")
        assert result == playlist_data

        result = cache.get("TEST PLAYLIST")
        assert result == playlist_data

    def test_get_with_whitespace(self):
        """Should handle whitespace in playlist names."""
        cache = PlaylistCache(cache_file=None)
        playlist_data = {"id": "p_123"}
        cache.set("  Test Playlist  ", playlist_data)

        result = cache.get("Test Playlist")
        assert result == playlist_data

    def test_get_nonexistent_entry(self):
        """Should return None for nonexistent entry."""
        cache = PlaylistCache(cache_file=None)

        result = cache.get("nonexistent")
        assert result is None


class TestPlaylistCacheSet:
    """Tests for set method."""

    def test_set_new_entry(self):
        """Should add new entry to cache."""
        cache = PlaylistCache(cache_file=None)
        playlist_data = {"id": "p_new", "name": "New"}

        cache.set("new playlist", playlist_data)

        assert cache.get("new playlist") == playlist_data

    def test_set_updates_existing_entry(self):
        """Should update existing entry."""
        cache = PlaylistCache(cache_file=None)

        # Set initial value
        cache.set("test", {"id": "old_id"})

        # Update
        new_data = {"id": "new_id"}
        cache.set("test", new_data)

        assert cache.get("test") == new_data

    def test_set_normalizes_key(self):
        """Should normalize key (lowercase, trim)."""
        cache = PlaylistCache(cache_file=None)
        playlist_data = {"id": "p_123"}

        cache.set("  Test Playlist  ", playlist_data)

        # Should be stored with normalized key
        assert "test playlist" in cache._cache

    def test_set_saves_to_file(self, temp_cache_file):
        """Should save to file if configured."""
        cache = PlaylistCache(cache_file=temp_cache_file)
        playlist_data = {"id": "p_123", "name": "Test"}

        cache.set("test", playlist_data)

        # File should be created and contain data
        assert temp_cache_file.exists()

        with open(temp_cache_file) as f:
            file_data = json.load(f)

        assert "test" in file_data
        assert file_data["test"]["playlist"] == playlist_data

    def test_set_without_file_no_save(self):
        """Should not attempt to save if no file configured."""
        cache = PlaylistCache(cache_file=None)

        # Should not crash
        cache.set("test", {"id": "p_123"})


class TestPlaylistCacheRemove:
    """Tests for remove method."""

    def test_remove_existing_entry(self):
        """Should remove existing entry."""
        cache = PlaylistCache(cache_file=None)
        cache.set("test", {"id": "p_123"})

        cache.remove("test")

        assert cache.get("test") is None

    def test_remove_case_insensitive(self):
        """Should remove entry case-insensitively."""
        cache = PlaylistCache(cache_file=None)
        cache.set("Test Playlist", {"id": "p_123"})

        cache.remove("test playlist")

        assert cache.get("Test Playlist") is None

    def test_remove_nonexistent_entry(self):
        """Should handle removing nonexistent entry gracefully."""
        cache = PlaylistCache(cache_file=None)

        # Should not crash
        cache.remove("nonexistent")

    def test_remove_updates_file(self, temp_cache_file):
        """Should update file after removal."""
        cache = PlaylistCache(cache_file=temp_cache_file)
        cache.set("test", {"id": "p_123"})

        cache.remove("test")

        # File should be updated
        with open(temp_cache_file) as f:
            file_data = json.load(f)

        assert "test" not in file_data


class TestPlaylistCacheClear:
    """Tests for clear method."""

    def test_clear_all_entries(self):
        """Should remove all entries from cache."""
        cache = PlaylistCache(cache_file=None)
        cache.set("test1", {"id": "1"})
        cache.set("test2", {"id": "2"})
        cache.set("test3", {"id": "3"})

        cache.clear()

        assert cache.get("test1") is None
        assert cache.get("test2") is None
        assert cache.get("test3") is None
        assert len(cache._cache) == 0

    def test_clear_updates_file(self, temp_cache_file):
        """Should update file after clearing."""
        cache = PlaylistCache(cache_file=temp_cache_file)
        cache.set("test1", {"id": "1"})
        cache.set("test2", {"id": "2"})

        cache.clear()

        # File should be empty
        with open(temp_cache_file) as f:
            file_data = json.load(f)

        assert file_data == {}


class TestPlaylistCacheContains:
    """Tests for contains method."""

    def test_contains_existing_entry(self):
        """Should return True for existing entry."""
        cache = PlaylistCache(cache_file=None)
        cache.set("test", {"id": "p_123"})

        assert cache.contains("test") is True

    def test_contains_case_insensitive(self):
        """Should check case-insensitively."""
        cache = PlaylistCache(cache_file=None)
        cache.set("Test Playlist", {"id": "p_123"})

        assert cache.contains("test playlist") is True
        assert cache.contains("TEST PLAYLIST") is True

    def test_contains_nonexistent_entry(self):
        """Should return False for nonexistent entry."""
        cache = PlaylistCache(cache_file=None)

        assert cache.contains("nonexistent") is False


class TestPlaylistCacheSaveToFile:
    """Tests for file saving functionality."""

    def test_save_creates_directory(self, tmp_path):
        """Should create parent directories if they don't exist."""
        cache_file = tmp_path / "nested" / "dir" / "cache.json"
        cache = PlaylistCache(cache_file=cache_file)

        cache.set("test", {"id": "p_123"})

        # Directory should be created
        assert cache_file.parent.exists()
        assert cache_file.exists()

    def test_save_formats_json_with_indent(self, temp_cache_file):
        """Should save JSON with indentation for readability."""
        cache = PlaylistCache(cache_file=temp_cache_file)
        cache.set("test", {"id": "p_123"})

        # Read file and check formatting
        content = temp_cache_file.read_text()

        # Should have indentation (not single line)
        assert "\n" in content
        assert "  " in content  # Indentation

    def test_save_handles_write_error(self, tmp_path):
        """Should handle write errors gracefully."""
        cache_file = tmp_path / "readonly" / "cache.json"
        cache = PlaylistCache(cache_file=cache_file)

        # Make parent directory read-only
        cache_file.parent.mkdir()
        cache_file.parent.chmod(0o444)

        try:
            # Should not crash even if write fails
            cache.set("test", {"id": "p_123"})
        finally:
            # Cleanup: restore permissions
            cache_file.parent.chmod(0o755)


class TestPlaylistCacheIntegration:
    """Integration tests for PlaylistCache."""

    def test_full_cache_lifecycle(self, temp_cache_file):
        """Should handle full cache lifecycle."""
        # Create cache and add entries
        cache1 = PlaylistCache(cache_file=temp_cache_file, ttl_hours=24)
        cache1.set("playlist1", {"id": "p_1", "name": "Playlist 1"})
        cache1.set("playlist2", {"id": "p_2", "name": "Playlist 2"})

        # Create new cache instance (should load from file)
        cache2 = PlaylistCache(cache_file=temp_cache_file, ttl_hours=24)

        # Should have loaded data
        assert cache2.get("playlist1") is not None
        assert cache2.get("playlist2") is not None

        # Remove one entry
        cache2.remove("playlist1")

        # Create another instance
        cache3 = PlaylistCache(cache_file=temp_cache_file, ttl_hours=24)

        # Should reflect removal
        assert cache3.get("playlist1") is None
        assert cache3.get("playlist2") is not None

    def test_expired_entry_lifecycle(self, temp_cache_file):
        """Should handle expired entries correctly."""
        # Create entry that's almost expired
        old_time = (datetime.now() - timedelta(hours=23, minutes=30)).isoformat()
        cache_data = {"old playlist": {"playlist": {"id": "old_123"}, "cached_at": old_time}}
        temp_cache_file.write_text(json.dumps(cache_data))

        # Load with TTL of 24 hours (entry should still be valid)
        cache = PlaylistCache(cache_file=temp_cache_file, ttl_hours=24)
        assert cache.get("old playlist") is not None

        # Load with TTL of 23 hours (entry should be expired)
        cache2 = PlaylistCache(cache_file=temp_cache_file, ttl_hours=23)
        assert cache2.get("old playlist") is None
