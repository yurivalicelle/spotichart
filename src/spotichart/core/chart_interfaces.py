"""
Chart Provider Interfaces

Abstractions for scraping music charts following Open/Closed Principle.
"""

from abc import ABC, abstractmethod
from typing import List

from ..utils.result import Result
from .models import ChartEntry, Track


class IHttpClient(ABC):
    """Interface for HTTP client operations."""

    @abstractmethod
    def fetch(self, url: str, timeout: int = 30) -> Result[str, Exception]:
        """
        Fetch content from URL.

        Args:
            url: URL to fetch
            timeout: Request timeout in seconds

        Returns:
            Result with HTML content or error
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the HTTP client and release resources."""
        pass


class IChartParser(ABC):
    """Interface for parsing chart HTML."""

    @abstractmethod
    def parse(self, html: str, limit: int) -> Result[List[ChartEntry], Exception]:
        """
        Parse HTML content to extract chart entries.

        Args:
            html: HTML content
            limit: Maximum number of entries to extract

        Returns:
            Result with list of chart entries or error
        """
        pass


class IChartProvider(ABC):
    """Interface for chart data providers (Open/Closed Principle)."""

    @abstractmethod
    def get_charts(self, region: str, limit: int = 1000) -> Result[List[Track], Exception]:
        """
        Get chart tracks for a specific region.

        Args:
            region: Region name (e.g., 'brazil', 'global', 'us')
            limit: Maximum number of tracks to retrieve

        Returns:
            Result with list of tracks or error
        """
        pass

    @abstractmethod
    def get_available_regions(self) -> List[str]:
        """
        Get list of available regions for this provider.

        Returns:
            List of region names
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Release resources held by the provider."""
        pass


class IRegionUrlMapper(ABC):
    """Interface for mapping regions to URLs."""

    @abstractmethod
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
        pass

    @abstractmethod
    def get_available_regions(self) -> List[str]:
        """Get list of available regions."""
        pass
