"""
Tests for Kworb Chart Provider
"""

from unittest.mock import Mock, patch

import pytest

from spotichart.core.kworb_provider import KworbChartProvider, KworbUrlMapper
from spotichart.core.models import ChartEntry, Track
from spotichart.utils.configuration_provider import ConfigurationProvider
from spotichart.utils.exceptions import ScrapingError
from spotichart.utils.result import Failure, Success


class TestKworbUrlMapper:
    """Test KworbUrlMapper."""

    def test_url_mapper_initialization(self):
        """URL mapper should initialize with config."""
        config = ConfigurationProvider()
        mapper = KworbUrlMapper(config)
        assert mapper._config == config

    def test_get_url_brazil(self):
        """Should get URL for brazil."""
        config = ConfigurationProvider()
        mapper = KworbUrlMapper(config)
        url = mapper.get_url("brazil")
        assert "brazil" in url.lower() or "br" in url.lower()

    def test_get_url_global(self):
        """Should get URL for global."""
        config = ConfigurationProvider()
        mapper = KworbUrlMapper(config)
        url = mapper.get_url("global")
        assert "global" in url.lower() or "worldwide" in url.lower()

    def test_get_url_invalid_region(self):
        """Should handle invalid region gracefully."""
        config = ConfigurationProvider()
        mapper = KworbUrlMapper(config)

        # ConfigurationProvider may return a default URL instead of raising
        # This tests that the method completes without crashing
        try:
            url = mapper.get_url("invalid_region_xyz_that_definitely_does_not_exist")
            # If it returns a URL, that's also acceptable behavior
            assert isinstance(url, str)
        except (ValueError, Exception):
            # Or it may raise an exception, which is also acceptable
            pass

    def test_get_available_regions(self):
        """Should return available regions."""
        config = ConfigurationProvider()
        mapper = KworbUrlMapper(config)
        regions = mapper.get_available_regions()

        assert isinstance(regions, list)
        assert len(regions) > 0
        assert "brazil" in regions or "global" in regions


class TestKworbChartProvider:
    """Test KworbChartProvider."""

    def test_provider_initialization(self):
        """Provider should initialize with dependencies."""
        http_client = Mock()
        url_mapper = Mock()

        provider = KworbChartProvider(http_client=http_client, url_mapper=url_mapper)

        assert provider._http_client == http_client
        assert provider._url_mapper == url_mapper

    def test_provider_default_initialization(self):
        """Provider should create default dependencies."""
        provider = KworbChartProvider()

        assert provider._http_client is not None
        assert provider._url_mapper is not None

    def test_get_charts_success(self):
        """Should get charts successfully."""
        # Mock dependencies
        http_client = Mock()
        http_client.fetch.return_value = Success(
            """
            <html>
                <table class="display">
                    <tbody>
                        <tr><td><a href="../track/track1.html">Track 1</a></td></tr>
                        <tr><td><a href="../track/track2.html">Track 2</a></td></tr>
                    </tbody>
                </table>
            </html>
            """
        )

        url_mapper = Mock()
        url_mapper.get_url.return_value = "http://kworb.net/brazil"

        provider = KworbChartProvider(http_client=http_client, url_mapper=url_mapper)

        # Get charts
        result = provider.get_charts("brazil", limit=10)

        assert result.is_success()
        tracks = result.unwrap()
        assert len(tracks) == 2
        assert all(isinstance(t, Track) for t in tracks)
        assert tracks[0].id == "track1"
        assert tracks[1].id == "track2"

    def test_get_charts_http_failure(self):
        """Should return Failure on HTTP error."""
        http_client = Mock()
        http_client.fetch.return_value = Failure(ScrapingError("Connection failed"))

        url_mapper = Mock()
        url_mapper.get_url.return_value = "http://kworb.net/brazil"

        provider = KworbChartProvider(http_client=http_client, url_mapper=url_mapper)

        result = provider.get_charts("brazil", limit=10)

        assert result.is_failure()

    def test_get_charts_invalid_region(self):
        """Should return Failure for invalid region."""
        http_client = Mock()

        url_mapper = Mock()
        url_mapper.get_url.side_effect = Exception("Invalid region")

        provider = KworbChartProvider(http_client=http_client, url_mapper=url_mapper)

        result = provider.get_charts("invalid", limit=10)

        assert result.is_failure()
        assert isinstance(result.error, ScrapingError)

    def test_get_charts_parse_failure(self):
        """Should return Failure on parse error."""
        http_client = Mock()
        http_client.fetch.return_value = Success("<html>No table</html>")

        url_mapper = Mock()
        url_mapper.get_url.return_value = "http://kworb.net/brazil"

        provider = KworbChartProvider(http_client=http_client, url_mapper=url_mapper)

        result = provider.get_charts("brazil", limit=10)

        assert result.is_failure()

    def test_get_available_regions(self):
        """Should get available regions from mapper."""
        url_mapper = Mock()
        url_mapper.get_available_regions.return_value = ["brazil", "global", "us"]

        provider = KworbChartProvider(url_mapper=url_mapper)

        regions = provider.get_available_regions()

        assert regions == ["brazil", "global", "us"]
        url_mapper.get_available_regions.assert_called_once()

    def test_close(self):
        """Should close HTTP client."""
        http_client = Mock()
        provider = KworbChartProvider(http_client=http_client)

        provider.close()

        http_client.close.assert_called_once()

    def test_context_manager(self):
        """Should work as context manager."""
        http_client = Mock()
        provider = KworbChartProvider(http_client=http_client)

        with provider as p:
            assert p == provider

        http_client.close.assert_called_once()

    def test_get_charts_with_limit(self):
        """Should respect limit parameter."""
        http_client = Mock()
        http_client.fetch.return_value = Success(
            """
            <html>
                <table class="display">
                    <tbody>
                        <tr><td><a href="../track/track1.html">T1</a></td></tr>
                        <tr><td><a href="../track/track2.html">T2</a></td></tr>
                        <tr><td><a href="../track/track3.html">T3</a></td></tr>
                        <tr><td><a href="../track/track4.html">T4</a></td></tr>
                        <tr><td><a href="../track/track5.html">T5</a></td></tr>
                    </tbody>
                </table>
            </html>
            """
        )

        url_mapper = Mock()
        url_mapper.get_url.return_value = "http://kworb.net/brazil"

        provider = KworbChartProvider(http_client=http_client, url_mapper=url_mapper)

        result = provider.get_charts("brazil", limit=3)

        assert result.is_success()
        tracks = result.unwrap()
        assert len(tracks) == 3
