"""
Kworb Chart Parser Implementation

Parses HTML from Kworb.net to extract chart data.
"""

import logging
from typing import List

from bs4 import BeautifulSoup

from ..utils.exceptions import ScrapingError
from ..utils.result import Failure, Result, Success
from .chart_interfaces import IChartParser
from .models import ChartEntry

logger = logging.getLogger(__name__)


class KworbChartParser(IChartParser):
    """Parser for Kworb.net chart HTML."""

    # Table selectors to try in order
    TABLE_SELECTORS = [
        {"class": "display"},
        {"class": "addpos"},
        {"id": "spotifyweekly"},
        {"class": "data"},
        {"class": "chart"},
    ]

    def __init__(self, region: str = "global"):
        """
        Initialize parser.

        Args:
            region: Region name for chart entries
        """
        self.region = region

    def parse(self, html: str, limit: int) -> Result[List[ChartEntry], Exception]:
        """
        Parse HTML content to extract chart entries.

        Args:
            html: HTML content
            limit: Maximum number of entries to extract

        Returns:
            Result with list of chart entries or error
        """
        try:
            soup = BeautifulSoup(html, "html.parser")

            # Find table
            table = self._find_table(soup)
            if not table:
                error_msg = "Table not found - site structure may have changed"
                logger.error(error_msg)
                return Failure(ScrapingError(error_msg))

            # Extract entries
            entries = self._extract_entries(table, limit)
            logger.info(f"Extracted {len(entries)} chart entries")
            return Success(entries)

        except Exception as e:
            error_msg = f"Failed to parse HTML: {str(e)}"
            logger.error(error_msg)
            return Failure(ScrapingError(error_msg))

    def _find_table(self, soup: BeautifulSoup):
        """Find the chart table using multiple selectors."""
        for selector in self.TABLE_SELECTORS:
            table = soup.find("table", selector)
            if table:
                logger.debug(f"Found table with selector: {selector}")
                return table
        return None

    def _extract_entries(self, table, limit: int) -> List[ChartEntry]:
        """Extract chart entries from table."""
        tbody = table.find("tbody")
        if not tbody:
            raise ScrapingError("Table body not found")

        rows = tbody.find_all("tr", limit=limit)
        logger.info(f"Found {len(rows)} rows in table")

        entries = []
        for position, row in enumerate(rows, start=1):
            track_id = self._extract_track_id(row)
            if track_id:
                entry = ChartEntry(track_id=track_id, position=position, region=self.region)
                entries.append(entry)

        return entries

    def _extract_track_id(self, row) -> str:
        """Extract Spotify track ID from table row."""
        cells = row.find_all("a")

        for cell in cells:
            href = cell.attrs.get("href", "")
            if href.startswith("../track"):
                track_id = href.replace("../track/", "").replace(".html", "").strip()
                return track_id

        return ""
