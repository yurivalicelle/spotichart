"""
Kworb Chart Provider Implementation

Provides chart data from Kworb.net following Open/Closed Principle.
"""

import logging
from typing import Dict, List

from ..utils.configuration_provider import ConfigurationProvider
from ..utils.exceptions import ScrapingError
from ..utils.result import Failure, Result, Success
from .chart_interfaces import IChartProvider, IHttpClient, IRegionUrlMapper
from .http_client import RetryHttpClient
from .kworb_parser import KworbChartParser
from .models import Track

logger = logging.getLogger(__name__)


class KworbUrlMapper(IRegionUrlMapper):
    """Maps region names to Kworb.net URLs."""

    def __init__(self, config: ConfigurationProvider):
        """
        Initialize URL mapper.

        Args:
            config: Configuration provider with region URLs
        """
        self._config = config

    def get_url(self, region: str) -> str:
        """
        Get URL for a specific region.

        Args:
            region: Region name

        Returns:
            URL string

        Raises:
            ValueError: If region is not supported
        """
        try:
            return self._config.get_kworb_url(region)
        except Exception as e:
            raise ValueError(f"Unsupported region: {region}") from e

    def get_available_regions(self) -> List[str]:
        """Get list of available regions."""
        return self._config.get_available_regions()


class KworbChartProvider(IChartProvider):
    """
    Chart provider for Kworb.net.

    Follows Open/Closed Principle - extensible without modification.
    """

    def __init__(
        self,
        http_client: IHttpClient = None,
        url_mapper: IRegionUrlMapper = None,
    ):
        """
        Initialize Kworb chart provider.

        Args:
            http_client: HTTP client for fetching pages
            url_mapper: Mapper for region URLs
        """
        self._http_client = http_client or RetryHttpClient()
        self._url_mapper = url_mapper or KworbUrlMapper(ConfigurationProvider())

    def get_charts(self, region: str, limit: int = 1000) -> Result[List[Track], Exception]:
        """
        Get chart tracks for a specific region.

        Args:
            region: Region name (e.g., 'brazil', 'global', 'us')
            limit: Maximum number of tracks to retrieve

        Returns:
            Result with list of tracks or error
        """
        logger.info(f"Fetching {region} charts from Kworb (limit: {limit})")

        try:
            # Get URL for region
            url = self._url_mapper.get_url(region)

            # Fetch HTML
            html_result = self._http_client.fetch(url)
            if html_result.is_failure():
                return html_result

            html = html_result.unwrap()

            # Parse HTML
            parser = KworbChartParser(region=region)
            entries_result = parser.parse(html, limit)

            if entries_result.is_failure():
                return entries_result

            # Convert entries to tracks
            entries = entries_result.unwrap()
            tracks = [entry.to_track() for entry in entries]

            logger.info(f"Successfully retrieved {len(tracks)} tracks from {region}")
            return Success(tracks)

        except ValueError as e:
            # Region not supported
            error_msg = str(e)
            logger.error(error_msg)
            return Failure(ScrapingError(error_msg))

        except Exception as e:
            error_msg = f"Failed to fetch charts: {str(e)}"
            logger.error(error_msg)
            return Failure(ScrapingError(error_msg))

    def get_available_regions(self) -> List[str]:
        """Get list of available regions for this provider."""
        return self._url_mapper.get_available_regions()

    def close(self) -> None:
        """Release resources held by the provider."""
        self._http_client.close()
        logger.debug("Kworb chart provider closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
