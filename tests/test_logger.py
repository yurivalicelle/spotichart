"""Tests for the robust logger setup."""

import pytest
import logging
from unittest.mock import patch, MagicMock
from spotichart.utils.logger import setup_logging, get_logger

# Paths to mock
GET_LOGGER_PATH = 'logging.getLogger'
ROTATING_HANDLER_PATH = 'spotichart.utils.logger.RotatingFileHandler'
STREAM_HANDLER_PATH = 'logging.StreamHandler'
FORMATTER_PATH = 'logging.Formatter'

@pytest.fixture
def mock_logger():
    """Fixture to mock the logger object returned by getLogger."""
    with patch(GET_LOGGER_PATH) as mock_get:
        mock_log_instance = MagicMock()
        mock_get.return_value = mock_log_instance
        yield mock_log_instance

@pytest.fixture
def mock_rotating_handler():
    """Fixture to mock the RotatingFileHandler class."""
    with patch(ROTATING_HANDLER_PATH) as mock_handler:
        yield mock_handler

@pytest.fixture
def mock_stream_handler():
    """Fixture to mock the StreamHandler class."""
    with patch(STREAM_HANDLER_PATH) as mock_handler:
        yield mock_handler

class TestLoggerSetup:

    def test_setup_logging_defaults(self, mock_logger, mock_rotating_handler, mock_stream_handler):
        """Should configure logger with default INFO level, file, and console handlers."""
        logger = setup_logging()

        mock_logger.setLevel.assert_called_once_with(logging.INFO)
        assert mock_logger.handlers.clear.called

        mock_rotating_handler.assert_called_once()
        mock_logger.addHandler.assert_any_call(mock_rotating_handler.return_value)

        mock_stream_handler.assert_called_once()
        mock_logger.addHandler.assert_any_call(mock_stream_handler.return_value)

        assert logger.propagate is False
        assert logger is mock_logger

    def test_setup_logging_debug_level(self, mock_logger, mock_rotating_handler, mock_stream_handler):
        """Should set DEBUG level on logger and console handler when specified."""
        setup_logging(log_level='DEBUG')
        
        mock_logger.setLevel.assert_called_once_with(logging.DEBUG)
        mock_stream_handler.return_value.setLevel.assert_called_once_with(logging.DEBUG)

    def test_setup_logging_no_console(self, mock_logger, mock_rotating_handler, mock_stream_handler):
        """Should not add a console handler if console=False."""
        setup_logging(console=False)
        
        mock_stream_handler.assert_not_called()
        # Use assert_any_call to ignore pytest's own handlers
        mock_logger.addHandler.assert_any_call(mock_rotating_handler.return_value)

    def test_setup_logging_no_file(self, mock_logger, mock_rotating_handler, mock_stream_handler):
        """Should still add a file handler since we have a default log file path."""
        # The setup_logging function now always uses a default log file
        # So we can't really test the "no file" scenario the same way
        # This test is essentially redundant now, but we'll keep it for backwards compat
        setup_logging(log_file=None)

        # With the new implementation, rotating handler is always added
        mock_rotating_handler.assert_called_once()
        mock_logger.addHandler.assert_any_call(mock_rotating_handler.return_value)

    @patch(FORMATTER_PATH)
    def test_formatters_are_created(self, mock_formatter, mock_logger, mock_rotating_handler, mock_stream_handler):
        """Should create two different formatters for file and console."""
        setup_logging()
        
        assert mock_formatter.call_count == 2
        
        detailed_format = mock_formatter.call_args_list[0][0][0]
        simple_format = mock_formatter.call_args_list[1][0][0]

        assert '[%(filename)s:%(lineno)d]' in detailed_format
        assert '[%(filename)s:%(lineno)d]' not in simple_format

class TestGetLogger:

    @patch(GET_LOGGER_PATH)
    def test_get_logger_returns_correctly_named_logger(self, mock_get_logger):
        """Should return a logger with the app name as a prefix."""
        get_logger("my_module")
        mock_get_logger.assert_called_once_with("spotichart.my_module")
