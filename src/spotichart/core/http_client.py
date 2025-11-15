"""
HTTP Client Implementation

Handles HTTP requests with retry logic.
"""

import logging
import time
from typing import Optional

import requests

from ..utils.exceptions import ScrapingError
from ..utils.result import Failure, Result, Success
from .chart_interfaces import IHttpClient

logger = logging.getLogger(__name__)


class RetryHttpClient(IHttpClient):
    """HTTP client with retry logic and user agent handling."""

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: int = 2,
        user_agent: Optional[str] = None,
    ):
        """
        Initialize HTTP client.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Base delay between retries in seconds
            user_agent: Custom user agent string
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session = requests.Session()

        # Set user agent
        ua = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        self.session.headers.update({"User-Agent": ua})

    def fetch(self, url: str, timeout: Optional[int] = None) -> Result[str, Exception]:
        """
        Fetch content from URL with retry logic.

        Args:
            url: URL to fetch
            timeout: Optional timeout override

        Returns:
            Result with HTML content or error
        """
        timeout_val = timeout if timeout is not None else self.timeout
        last_error: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"Fetching URL (attempt {attempt}/{self.max_retries}): {url}")
                response = self.session.get(url, timeout=timeout_val)
                response.raise_for_status()
                content = response.content.decode("utf-8")
                logger.info(f"Successfully fetched {url}")
                return Success(content)

            except requests.RequestException as e:
                last_error = e
                logger.warning(f"Attempt {attempt} failed: {str(e)}")

                if attempt < self.max_retries:
                    sleep_time = self.retry_delay * attempt
                    logger.info(f"Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)

        error_msg = f"Failed to fetch {url} after {self.max_retries} attempts: {str(last_error)}"
        logger.error(error_msg)
        return Failure(ScrapingError(error_msg))

    def close(self) -> None:
        """Close the HTTP session."""
        self.session.close()
        logger.debug("HTTP client session closed")
