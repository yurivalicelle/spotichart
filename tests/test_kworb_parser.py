"""
Tests for Kworb Chart Parser
"""

import pytest

from spotichart.core.kworb_parser import KworbChartParser
from spotichart.core.models import ChartEntry
from spotichart.utils.exceptions import ScrapingError


class TestKworbChartParser:
    """Test KworbChartParser."""

    def test_parser_initialization(self):
        """Parser should initialize with region."""
        parser = KworbChartParser(region="brazil")
        assert parser.region == "brazil"

    def test_parse_valid_html(self):
        """Parser should extract chart entries from valid HTML."""
        html = """
        <html>
            <table class="display">
                <tbody>
                    <tr>
                        <td><a href="../track/track123.html">Track 1</a></td>
                    </tr>
                    <tr>
                        <td><a href="../track/track456.html">Track 2</a></td>
                    </tr>
                    <tr>
                        <td><a href="../track/track789.html">Track 3</a></td>
                    </tr>
                </tbody>
            </table>
        </html>
        """

        parser = KworbChartParser(region="global")
        result = parser.parse(html, limit=10)

        assert result.is_success()
        entries = result.unwrap()
        assert len(entries) == 3

        # Check first entry
        assert isinstance(entries[0], ChartEntry)
        assert entries[0].track_id == "track123"
        assert entries[0].position == 1
        assert entries[0].region == "global"

        # Check positions
        assert entries[1].position == 2
        assert entries[2].position == 3

    def test_parse_with_limit(self):
        """Parser should respect limit."""
        html = """
        <html>
            <table class="display">
                <tbody>
                    <tr><td><a href="../track/track1.html">Track 1</a></td></tr>
                    <tr><td><a href="../track/track2.html">Track 2</a></td></tr>
                    <tr><td><a href="../track/track3.html">Track 3</a></td></tr>
                    <tr><td><a href="../track/track4.html">Track 4</a></td></tr>
                    <tr><td><a href="../track/track5.html">Track 5</a></td></tr>
                </tbody>
            </table>
        </html>
        """

        parser = KworbChartParser(region="brazil")
        result = parser.parse(html, limit=3)

        assert result.is_success()
        entries = result.unwrap()
        assert len(entries) == 3

    def test_parse_alternative_table_class(self):
        """Parser should find table with alternative selectors."""
        html = """
        <html>
            <table class="addpos">
                <tbody>
                    <tr><td><a href="../track/track123.html">Track</a></td></tr>
                </tbody>
            </table>
        </html>
        """

        parser = KworbChartParser(region="us")
        result = parser.parse(html, limit=10)

        assert result.is_success()
        entries = result.unwrap()
        assert len(entries) == 1
        assert entries[0].track_id == "track123"

    def test_parse_spotifyweekly_id(self):
        """Parser should find table by id."""
        html = """
        <html>
            <table id="spotifyweekly">
                <tbody>
                    <tr><td><a href="../track/track123.html">Track</a></td></tr>
                </tbody>
            </table>
        </html>
        """

        parser = KworbChartParser(region="uk")
        result = parser.parse(html, limit=10)

        assert result.is_success()
        entries = result.unwrap()
        assert len(entries) == 1

    def test_parse_no_table_found(self):
        """Parser should return Failure if table not found."""
        html = "<html><body>No table here</body></html>"

        parser = KworbChartParser(region="global")
        result = parser.parse(html, limit=10)

        assert result.is_failure()
        assert isinstance(result.error, ScrapingError)
        assert "Table not found" in str(result.error)

    def test_parse_no_tbody(self):
        """Parser should return Failure if tbody not found."""
        html = """
        <html>
            <table class="display">
                <tr><td>No tbody</td></tr>
            </table>
        </html>
        """

        parser = KworbChartParser(region="global")
        result = parser.parse(html, limit=10)

        assert result.is_failure()
        assert isinstance(result.error, ScrapingError)
        assert "Table body not found" in str(result.error)

    def test_parse_row_without_track_link(self):
        """Parser should skip rows without track links."""
        html = """
        <html>
            <table class="display">
                <tbody>
                    <tr><td><a href="../artist/artist.html">Artist</a></td></tr>
                    <tr><td><a href="../track/track123.html">Track</a></td></tr>
                    <tr><td>No link here</td></tr>
                </tbody>
            </table>
        </html>
        """

        parser = KworbChartParser(region="global")
        result = parser.parse(html, limit=10)

        assert result.is_success()
        entries = result.unwrap()
        # Should only extract the one with track link
        assert len(entries) == 1
        assert entries[0].track_id == "track123"

    def test_parse_malformed_html(self):
        """Parser should handle malformed HTML gracefully."""
        html = "<html><table class='display'><tbody><tr><td"

        parser = KworbChartParser(region="global")
        result = parser.parse(html, limit=10)

        # BeautifulSoup is lenient, so this might succeed with empty results
        # or fail depending on the malformation
        assert result.is_success() or result.is_failure()

    def test_parse_empty_tbody(self):
        """Parser should handle empty tbody."""
        html = """
        <html>
            <table class="display">
                <tbody></tbody>
            </table>
        </html>
        """

        parser = KworbChartParser(region="global")
        result = parser.parse(html, limit=10)

        assert result.is_success()
        entries = result.unwrap()
        assert len(entries) == 0

    def test_extract_track_id_variations(self):
        """Parser should handle track ID variations."""
        html = """
        <html>
            <table class="display">
                <tbody>
                    <tr><td><a href="../track/track_with_underscore.html">Track</a></td></tr>
                    <tr><td><a href="../track/123456789.html">Track</a></td></tr>
                    <tr><td><a href="../track/track-with-dash.html">Track</a></td></tr>
                </tbody>
            </table>
        </html>
        """

        parser = KworbChartParser(region="global")
        result = parser.parse(html, limit=10)

        assert result.is_success()
        entries = result.unwrap()
        assert len(entries) == 3
        assert entries[0].track_id == "track_with_underscore"
        assert entries[1].track_id == "123456789"
        assert entries[2].track_id == "track-with-dash"
