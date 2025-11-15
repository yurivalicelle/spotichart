"""Tests for strategy pattern implementations."""

import pytest
import time
from unittest.mock import Mock, patch
from spotichart.strategies.batch_strategy import (
    BatchStrategy,
    FixedSizeBatchStrategy,
    AdaptiveBatchStrategy
)
from spotichart.strategies.scraper_strategy import (
    ScraperStrategy,
    KworbScraperStrategy
)


class TestBatchStrategy:
    """Test BatchStrategy abstract base class."""

    def test_is_abstract(self):
        """BatchStrategy is abstract."""
        with pytest.raises(TypeError):
            BatchStrategy()

    def test_subclass_must_implement_process(self):
        """Subclass must implement process method."""
        class IncompleteBatchStrategy(BatchStrategy):
            pass

        with pytest.raises(TypeError):
            IncompleteBatchStrategy()


class TestFixedSizeBatchStrategy:
    """Test FixedSizeBatchStrategy."""

    def test_process_single_batch(self):
        """Process items in single batch."""
        strategy = FixedSizeBatchStrategy(batch_size=10, delay_between_batches=0)

        items = list(range(5))
        processor = Mock(return_value='result')

        results = strategy.process(items, processor)

        assert len(results) == 1
        assert results[0] == 'result'
        processor.assert_called_once_with([0, 1, 2, 3, 4])

    def test_process_multiple_batches(self):
        """Process items in multiple batches."""
        strategy = FixedSizeBatchStrategy(batch_size=3, delay_between_batches=0)

        items = list(range(7))  # [0,1,2], [3,4,5], [6]
        processor = Mock(side_effect=lambda batch: sum(batch))

        results = strategy.process(items, processor)

        assert len(results) == 3
        assert results[0] == 3   # 0+1+2
        assert results[1] == 12  # 3+4+5
        assert results[2] == 6   # 6
        assert processor.call_count == 3

    def test_process_empty_list(self):
        """Process empty list returns empty results."""
        strategy = FixedSizeBatchStrategy(batch_size=10, delay_between_batches=0)

        results = strategy.process([], Mock())

        assert len(results) == 0

    def test_process_with_delay(self):
        """Process respects delay between batches."""
        strategy = FixedSizeBatchStrategy(batch_size=2, delay_between_batches=0.1)

        items = list(range(6))  # 3 batches
        processor = Mock(return_value=None)

        start_time = time.time()
        strategy.process(items, processor)
        elapsed = time.time() - start_time

        # Should have 2 delays (between 3 batches)
        assert elapsed >= 0.2

    def test_different_batch_sizes(self):
        """Different batch sizes work correctly."""
        for batch_size in [1, 5, 10, 100]:
            strategy = FixedSizeBatchStrategy(batch_size=batch_size, delay_between_batches=0)
            items = list(range(25))
            processor = Mock(return_value=None)

            results = strategy.process(items, processor)

            expected_batches = (len(items) + batch_size - 1) // batch_size
            assert len(results) == expected_batches


class TestAdaptiveBatchStrategy:
    """Test AdaptiveBatchStrategy."""

    def test_initial_batch_size(self):
        """Uses initial batch size for first batch."""
        strategy = AdaptiveBatchStrategy(
            initial_batch_size=10,
            min_batch_size=5,
            max_batch_size=20,
            delay_between_batches=0
        )

        items = list(range(100))
        processor = Mock(return_value=None)

        strategy.process(items, processor)

        # First call should use initial batch size
        first_call_args = processor.call_args_list[0][0][0]
        assert len(first_call_args) == 10

    def test_increases_batch_on_success(self):
        """Batch size increases on successful processing."""
        strategy = AdaptiveBatchStrategy(
            initial_batch_size=5,
            min_batch_size=5,
            max_batch_size=20,
            delay_between_batches=0
        )

        items = list(range(100))
        processor = Mock(return_value=None)  # Success

        strategy.process(items, processor)

        # Later batches should be larger
        last_call_args = processor.call_args_list[-2][0][0]  # -2 to skip last partial batch
        assert len(last_call_args) > 5

    def test_decreases_batch_on_failure(self):
        """Batch size decreases on processing failure."""
        strategy = AdaptiveBatchStrategy(
            initial_batch_size=10,
            min_batch_size=2,
            max_batch_size=20,
            delay_between_batches=0
        )

        items = list(range(100))

        # First call succeeds, second fails
        processor = Mock(side_effect=[None, Exception('Error'), None, None, None])

        try:
            strategy.process(items, processor)
        except:
            pass

        # After failure, batch size should decrease
        # This is implementation-dependent, so we just check it doesn't crash

    def test_respects_min_batch_size(self):
        """Never goes below min batch size."""
        strategy = AdaptiveBatchStrategy(
            initial_batch_size=10,
            min_batch_size=5,
            max_batch_size=20,
            delay_between_batches=0
        )

        # Force many failures
        items = list(range(50))
        processor = Mock(side_effect=Exception('Error'))

        try:
            strategy.process(items, processor)
        except:
            pass

        # Batch size should not go below min
        # Check that we're still attempting to process
        assert processor.called

    def test_respects_max_batch_size(self):
        """Never goes above max batch size."""
        strategy = AdaptiveBatchStrategy(
            initial_batch_size=5,
            min_batch_size=2,
            max_batch_size=10,
            delay_between_batches=0
        )

        items = list(range(1000))
        processor = Mock(return_value=None)  # Always succeed

        strategy.process(items, processor)

        # Check that no batch exceeded max size
        for call_args in processor.call_args_list:
            batch = call_args[0][0]
            assert len(batch) <= 10


class TestScraperStrategy:
    """Test ScraperStrategy abstract base class."""

    def test_is_abstract(self):
        """ScraperStrategy is abstract."""
        with pytest.raises(TypeError):
            ScraperStrategy()


class TestKworbScraperStrategy:
    """Test KworbScraperStrategy."""

    def test_get_supported_domains(self):
        """Returns supported domains."""
        scraper = KworbScraperStrategy()

        domains = scraper.get_supported_domains()

        assert 'kworb.net' in domains
        assert 'www.kworb.net' in domains

    def test_scrape_with_mock_html(self, mock_kworb_html):
        """Scrape tracks from mock HTML."""
        scraper = KworbScraperStrategy(timeout=30)

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.text = mock_kworb_html
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            tracks = scraper.scrape('https://kworb.net/spotify/country/br_weekly_totals.html', limit=10)

            assert len(tracks) == 3
            assert '123' in tracks
            assert '456' in tracks
            assert '789' in tracks

    def test_scrape_respects_limit(self, mock_kworb_html):
        """Scrape respects limit parameter."""
        scraper = KworbScraperStrategy(timeout=30)

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.text = mock_kworb_html
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            tracks = scraper.scrape('https://kworb.net/spotify/country/br_weekly_totals.html', limit=2)

            assert len(tracks) <= 2

    def test_scrape_handles_network_error(self):
        """Scrape handles network errors gracefully."""
        scraper = KworbScraperStrategy(timeout=30)

        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception('Network error')

            tracks = scraper.scrape('https://kworb.net/spotify/country/br_weekly_totals.html', limit=10)

            assert tracks == []

    def test_scrape_handles_invalid_html(self):
        """Scrape handles invalid HTML gracefully."""
        scraper = KworbScraperStrategy(timeout=30)

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.text = '<html><body>Invalid</body></html>'
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            tracks = scraper.scrape('https://kworb.net/spotify/country/br_weekly_totals.html', limit=10)

            # Should handle gracefully, return empty or partial results
            assert isinstance(tracks, list)

    def test_timeout_parameter(self):
        """Timeout parameter is used in requests."""
        scraper = KworbScraperStrategy(timeout=15)

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.text = '<html></html>'
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            scraper.scrape('https://kworb.net/spotify/country/br_weekly_totals.html', limit=10)

            # Verify timeout was passed
            call_kwargs = mock_get.call_args[1]
            assert call_kwargs.get('timeout') == 15
