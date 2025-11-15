"""Tests for the KworbScraper."""

import pytest
from unittest.mock import patch, MagicMock
import requests
from spotichart.core.scraper import KworbScraper, ScrapingError

@pytest.fixture
def mock_requests_get():
    """Fixture to mock requests.get."""
    with patch('requests.Session.get') as mock_get:
        yield mock_get

@pytest.fixture
def scraper():
    """Provides a KworbScraper instance."""
    # Use short timeouts for tests to avoid waiting
    return KworbScraper(timeout=1, max_retries=2)

# A sample HTML structure mimicking the Kworb table
SAMPLE_HTML = """
<html>
<body>
  <table class="display">
    <tbody>
      <tr><td><a href="../track/track_id_1.html">Track 1</a></td></tr>
      <tr><td><a href="../track/track_id_2.html">Track 2</a></td></tr>
      <tr><td><a href="../track/track_id_3.html">Track 3</a></td></tr>
    </tbody>
  </table>
</body>
</html>
"""

class TestKworbScraperFetch:
    """Tests the network-related fetching logic."""

    def test_fetch_page_success(self, scraper, mock_requests_get):
        """Should return page content on a successful request."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content.decode.return_value = "<html>Success</html>"
        mock_requests_get.return_value = mock_response

        content = scraper._fetch_page("http://example.com")

        assert content == "<html>Success</html>"
        mock_requests_get.assert_called_once_with("http://example.com", timeout=1)

    def test_fetch_page_retry_and_fail(self, scraper, mock_requests_get):
        """Should retry fetching and then raise ScrapingError."""
        mock_requests_get.side_effect = requests.RequestException("Connection error")
        
        with patch('time.sleep'), pytest.raises(ScrapingError, match="Failed to fetch http://example.com"):
            scraper._fetch_page("http://example.com")
        
        # Should be called `max_retries` times (which is 2 for this test scraper)
        assert mock_requests_get.call_count == 2

    def test_fetch_page_retry_and_succeed(self, scraper, mock_requests_get):
        """Should succeed on a retry attempt."""
        success_response = MagicMock()
        success_response.content.decode.return_value = "Success"
        
        mock_requests_get.side_effect = [requests.RequestException("Fail"), success_response]

        with patch('time.sleep'):
            content = scraper._fetch_page("http://example.com")
            assert content == "Success"
            assert mock_requests_get.call_count == 2

class TestKworbScraperParse:
    """Tests the HTML parsing logic."""

    def test_parse_table_success(self, scraper):
        """Should correctly parse a valid HTML table and extract track IDs."""
        tracks = scraper._parse_table(SAMPLE_HTML, limit=3)
        
        assert len(tracks) == 3
        assert tracks[0]['track'] == 'track_id_1'
        assert tracks[1]['track'] == 'track_id_2'
        assert tracks[2]['track'] == 'track_id_3'

    def test_parse_table_with_limit(self, scraper):
        """Should respect the limit parameter."""
        tracks = scraper._parse_table(SAMPLE_HTML, limit=1)
        
        assert len(tracks) == 1
        assert tracks[0]['track'] == 'track_id_1'

    def test_parse_table_not_found(self, scraper):
        """Should raise ScrapingError if the table cannot be found."""
        html_no_table = "<html><body><p>No table here</p></body></html>"
        
        with pytest.raises(ScrapingError, match="Table not found"):
            scraper._parse_table(html_no_table, limit=10)

    def test_parse_table_no_tbody(self, scraper):
        """Should raise ScrapingError if the table has no body."""
        html_no_tbody = '<html><body><table class="display"></table></body></html>'
        
        with pytest.raises(ScrapingError, match="Table body not found"):
            scraper._parse_table(html_no_tbody, limit=10)

class TestKworbScraperEndToEnd:
    """Tests the main `scrape` and `scrape_region` methods."""

    def test_scrape_success(self, scraper, mock_requests_get):
        """The main scrape method should orchestrate fetching and parsing."""
        mock_response = MagicMock()
        mock_response.content.decode.return_value = SAMPLE_HTML
        mock_requests_get.return_value = mock_response
        
        tracks = scraper.scrape("http://example.com", limit=2)
        
        assert len(tracks) == 2
        assert tracks[0]['track'] == 'track_id_1'
        mock_requests_get.assert_called_once()

    def test_scrape_region_success(self, scraper, mock_requests_get):
        """scrape_region should call scrape with the correct URL."""
        mock_response = MagicMock()
        mock_response.content.decode.return_value = SAMPLE_HTML
        mock_requests_get.return_value = mock_response

        # Mock the _config instance in the scraper module
        with patch('spotichart.core.scraper._config') as mock_config:
            mock_config.get_kworb_url.return_value = "http://test.url/global"
            tracks = scraper.scrape_region('global', limit=3)

            assert len(tracks) == 3
            mock_config.get_kworb_url.assert_called_once_with('global')
            mock_requests_get.assert_called_once_with("http://test.url/global", timeout=1)

    def test_context_manager(self):
        """Should be usable as a context manager."""
        with KworbScraper() as s:
            # Mock the close method to check if it's called
            s.close = MagicMock()
            assert isinstance(s, KworbScraper)
        
        s.close.assert_called_once()
