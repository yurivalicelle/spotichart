"""
Web Scraper Module

Handles scraping of music charts from Kworb.net.
"""

import logging
import os
from typing import List, Dict, Optional
import time
import requests
from bs4 import BeautifulSoup
from ..utils.exceptions import ScrapingError
from ..utils.configuration_provider import ConfigurationProvider

logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 2

# Initialize configuration provider
_config = ConfigurationProvider()


class KworbScraper:
    """Scraper for Kworb.net music charts."""

    def __init__(self, timeout: Optional[int] = None, max_retries: Optional[int] = None):
        """
        Initialize Kworb scraper.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.timeout = timeout or DEFAULT_REQUEST_TIMEOUT
        self.max_retries = max_retries or DEFAULT_MAX_RETRIES
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                         '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def _fetch_page(self, url: str) -> str:
        """
        Fetch page content with retry logic.

        Args:
            url: URL to fetch

        Returns:
            HTML content

        Raises:
            ScrapingError: If fetching fails after retries
        """
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"Fetching URL (attempt {attempt}/{self.max_retries}): {url}")
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response.content.decode('utf-8')

            except requests.RequestException as e:
                last_error = e
                logger.warning(f"Attempt {attempt} failed: {str(e)}")

                if attempt < self.max_retries:
                    sleep_time = DEFAULT_RETRY_DELAY * attempt
                    logger.info(f"Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)

        logger.error(f"Failed to fetch URL after {self.max_retries} attempts")
        raise ScrapingError(f"Failed to fetch {url}: {str(last_error)}") from last_error

    def _parse_table(self, html: str, limit: int) -> List[Dict[str, str]]:
        """
        Parse HTML table and extract track information.

        Args:
            html: HTML content
            limit: Maximum number of tracks to extract

        Returns:
            List of track dictionaries

        Raises:
            ScrapingError: If table parsing fails
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Try multiple selectors to find the table
            table = None
            selectors = [
                {'class': 'display'},
                {'class': 'addpos'},
                {'id': 'spotifyweekly'},
                {'class': 'data'},
                {'class': 'chart'}
            ]

            for selector in selectors:
                table = soup.find('table', selector)
                if table:
                    logger.debug(f"Found table with selector: {selector}")
                    break

            if not table:
                raise ScrapingError("Table not found - site structure may have changed")

            # Extract data
            tracks = []
            tbody = table.find('tbody')

            if not tbody:
                raise ScrapingError("Table body not found")

            rows = tbody.find_all('tr', limit=limit)
            logger.info(f"Found {len(rows)} rows in table")

            for row in rows:
                cells = row.find_all('a')
                track_id = None

                for cell in cells:
                    href = cell.attrs.get('href', '')
                    if href.startswith('../track'):
                        track_id = href.replace('../track/', '').replace('.html', '').strip()
                        break

                if track_id:
                    tracks.append({'track': track_id})

            logger.info(f"Extracted {len(tracks)} tracks")
            return tracks

        except Exception as e:
            logger.error(f"Table parsing error: {str(e)}")
            raise ScrapingError(f"Failed to parse table: {str(e)}") from e

    def scrape(self, url: str, limit: int = 1000) -> List[Dict[str, str]]:
        """
        Scrape top songs from Kworb URL.

        Args:
            url: Kworb URL to scrape
            limit: Maximum number of songs to extract

        Returns:
            List of dictionaries containing track information

        Raises:
            ScrapingError: If scraping fails
        """
        logger.info(f"Starting scraping: {url}")

        try:
            html = self._fetch_page(url)
            tracks = self._parse_table(html, limit)

            logger.info(f"Successfully scraped {len(tracks)} tracks from {url}")
            return tracks

        except ScrapingError:
            raise
        except Exception as e:
            logger.error(f"Unexpected scraping error: {str(e)}")
            raise ScrapingError(f"Scraping failed: {str(e)}") from e

    def scrape_region(self, region: str = 'brazil', limit: int = 1000) -> List[Dict[str, str]]:
        """
        Scrape tracks for a specific region.

        Args:
            region: Region name ('brazil', 'global', 'us', 'uk')
            limit: Maximum number of tracks

        Returns:
            List of track dictionaries

        Raises:
            ScrapingError: If scraping fails
        """
        url = _config.get_kworb_url(region)
        logger.info(f"Scraping {region} charts")
        return self.scrape(url, limit)

    def close(self):
        """Close the session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
