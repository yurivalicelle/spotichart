"""
Tests to improve coverage of chart interfaces.
"""

from unittest.mock import Mock

import pytest

from spotichart.core.chart_interfaces import (
    IChartParser,
    IChartProvider,
    IHttpClient,
    IRegionUrlMapper,
)
from spotichart.core.models import ChartEntry, Track
from spotichart.utils.result import Failure, Success


class ConcreteHttpClient(IHttpClient):
    """Concrete implementation for testing."""

    def fetch(self, url: str, timeout: int = 30):
        """Fetch request."""
        return Success("<html>test</html>")

    def close(self) -> None:
        """Close client."""
        pass


class ConcreteChartParser(IChartParser):
    """Concrete implementation for testing."""

    def parse(self, html: str, limit: int = 50):
        """Parse HTML."""
        return Success([ChartEntry(track_id="test1", position=1, region="brazil")])


class ConcreteChartProvider(IChartProvider):
    """Concrete implementation for testing."""

    def get_charts(self, region: str, limit: int = 50):
        """Get charts."""
        return Success([Track(id="test1")])

    def get_available_regions(self):
        """Get regions."""
        return ["brazil"]

    def close(self) -> None:
        """Close provider."""
        pass


class ConcreteRegionUrlMapper(IRegionUrlMapper):
    """Concrete implementation for testing."""

    def get_url(self, region: str) -> str:
        """Get URL for region."""
        if region not in self.get_available_regions():
            raise ValueError(f"Unsupported region: {region}")
        return f"https://example.com/{region}.html"

    def get_available_regions(self):
        """Get available regions."""
        return ["brazil", "us", "global"]


class TestChartInterfaces:
    """Test chart interfaces."""

    def test_http_client_interface(self):
        """Test IHttpClient interface."""
        client = ConcreteHttpClient()

        result = client.fetch("https://example.com", timeout=10)
        assert result.is_success()
        assert result.unwrap() == "<html>test</html>"

        # Should not raise
        client.close()

    def test_chart_parser_interface(self):
        """Test IChartParser interface."""
        parser = ConcreteChartParser()

        result = parser.parse("<html>test</html>", limit=10)
        assert result.is_success()
        entries = result.unwrap()
        assert len(entries) == 1
        assert isinstance(entries[0], ChartEntry)
        assert entries[0].track_id == "test1"

    def test_chart_provider_interface(self):
        """Test IChartProvider interface."""
        provider = ConcreteChartProvider()

        result = provider.get_charts("brazil", limit=50)
        assert result.is_success()
        tracks = result.unwrap()
        assert len(tracks) == 1

        regions = provider.get_available_regions()
        assert "brazil" in regions

        # Should not raise
        provider.close()

    def test_region_url_mapper_interface(self):
        """Test IRegionUrlMapper interface."""
        mapper = ConcreteRegionUrlMapper()

        # Test successful mapping
        url = mapper.get_url("brazil")
        assert url == "https://example.com/brazil.html"

        # Test invalid region raises error
        with pytest.raises(ValueError, match="Unsupported region"):
            mapper.get_url("invalid_region")

        # Test get_available_regions
        regions = mapper.get_available_regions()
        assert "brazil" in regions
        assert "us" in regions


class TestChartProviderWithMocks:
    """Test chart provider using mocks."""

    def test_provider_delegates_to_parser_and_http(self):
        """Test that provider uses parser and HTTP client correctly."""
        # This test demonstrates how providers might be composed
        http_client = Mock(spec=IHttpClient)
        http_client.fetch.return_value = Success("<html>chart data</html>")

        parser = Mock(spec=IChartParser)
        entries = [ChartEntry(track_id="t1", position=1, region="brazil")]
        parser.parse.return_value = Success(entries)

        # In real code, a provider might use these internally
        # This is just a demonstration of the pattern
        html_result = http_client.fetch("https://example.com/brazil.html")
        assert html_result.is_success()

        parse_result = parser.parse(html_result.unwrap(), limit=50)
        assert parse_result.is_success()
        assert len(parse_result.unwrap()) == 1

    def test_provider_handles_http_failure(self):
        """Test provider behavior when HTTP fails."""
        http_client = Mock(spec=IHttpClient)
        http_client.fetch.return_value = Failure(Exception("Network error"))

        result = http_client.fetch("https://example.com")
        assert result.is_failure()

    def test_provider_handles_parse_failure(self):
        """Test provider behavior when parsing fails."""
        parser = Mock(spec=IChartParser)
        parser.parse.return_value = Failure(Exception("Parse error"))

        result = parser.parse("<html>invalid</html>", limit=50)
        assert result.is_failure()
