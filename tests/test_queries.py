"""
Tests for Query Objects (CQRS)
"""

import pytest

from spotichart.application.queries import (
    GetPlaylistByIdQuery,
    GetPlaylistByNameQuery,
    GetPlaylistStatisticsQuery,
    GetPlaylistTracksQuery,
    IQuery,
    ListPlaylistsQuery,
    ListRegionsQuery,
    PreviewChartsQuery,
    SearchPlaylistsQuery,
)


class TestQueryObjects:
    """Test query object creation and immutability."""

    def test_get_playlist_by_id_query(self):
        """Test GetPlaylistByIdQuery creation."""
        query = GetPlaylistByIdQuery(playlist_id="test_id")

        assert isinstance(query, IQuery)
        assert query.playlist_id == "test_id"

        # Test immutability
        with pytest.raises(AttributeError):
            query.playlist_id = "new_id"  # type: ignore

    def test_get_playlist_by_name_query(self):
        """Test GetPlaylistByNameQuery creation."""
        query = GetPlaylistByNameQuery(name="Test Playlist")

        assert isinstance(query, IQuery)
        assert query.name == "Test Playlist"

        # Test immutability
        with pytest.raises(AttributeError):
            query.name = "New Name"  # type: ignore

    def test_list_playlists_query(self):
        """Test ListPlaylistsQuery creation."""
        query = ListPlaylistsQuery(limit=100, offset=50)

        assert isinstance(query, IQuery)
        assert query.limit == 100
        assert query.offset == 50

        # Test defaults
        query_default = ListPlaylistsQuery()
        assert query_default.limit == 50
        assert query_default.offset == 0

    def test_list_regions_query(self):
        """Test ListRegionsQuery creation."""
        query = ListRegionsQuery()

        assert isinstance(query, IQuery)

    def test_preview_charts_query(self):
        """Test PreviewChartsQuery creation."""
        query = PreviewChartsQuery(region="brazil", limit=100)

        assert isinstance(query, IQuery)
        assert query.region == "brazil"
        assert query.limit == 100

        # Test defaults
        query_default = PreviewChartsQuery(region="us")
        assert query_default.region == "us"
        assert query_default.limit == 50

    def test_get_playlist_tracks_query(self):
        """Test GetPlaylistTracksQuery creation."""
        query = GetPlaylistTracksQuery(playlist_id="test_id", limit=200)

        assert isinstance(query, IQuery)
        assert query.playlist_id == "test_id"
        assert query.limit == 200

        # Test defaults
        query_default = GetPlaylistTracksQuery(playlist_id="test_id")
        assert query_default.limit == 100

    def test_search_playlists_query(self):
        """Test SearchPlaylistsQuery creation."""
        query = SearchPlaylistsQuery(search_term="rock", limit=10)

        assert isinstance(query, IQuery)
        assert query.search_term == "rock"
        assert query.limit == 10

        # Test defaults
        query_default = SearchPlaylistsQuery(search_term="test")
        assert query_default.limit == 20

    def test_get_playlist_statistics_query(self):
        """Test GetPlaylistStatisticsQuery creation."""
        query = GetPlaylistStatisticsQuery(playlist_id="test_id")

        assert isinstance(query, IQuery)
        assert query.playlist_id == "test_id"

        # Test immutability
        with pytest.raises(AttributeError):
            query.playlist_id = "new_id"  # type: ignore


class TestQueryEquality:
    """Test query equality and hashing."""

    def test_query_equality(self):
        """Test that queries with same params are equal."""
        query1 = GetPlaylistByIdQuery(playlist_id="test_id")
        query2 = GetPlaylistByIdQuery(playlist_id="test_id")
        query3 = GetPlaylistByIdQuery(playlist_id="other_id")

        assert query1 == query2
        assert query1 != query3

    def test_query_hashing(self):
        """Test that queries can be used as dict keys."""
        query1 = GetPlaylistByIdQuery(playlist_id="test_id")
        query2 = GetPlaylistByIdQuery(playlist_id="test_id")

        cache = {query1: "result"}
        assert cache[query2] == "result"

    def test_different_query_types_not_equal(self):
        """Test that different query types are not equal."""
        query1 = ListPlaylistsQuery(limit=50)
        query2 = ListRegionsQuery()

        assert query1 != query2
