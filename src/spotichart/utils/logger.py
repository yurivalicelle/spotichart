"""
Logging Configuration Module

Sets up advanced logging with rotation and formatting.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from ..config import Config


def setup_logging(
    log_level: str = None,
    log_file: str = None,
    console: bool = True
) -> logging.Logger:
    """
    Configure application logging with rotation.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (uses Config default if not provided)
        console: Whether to also log to console

    Returns:
        Configured logger instance
    """
    # Ensure log directory exists
    Config.setup_directories()

    # Get log level
    level = getattr(logging, (log_level or Config.LOG_LEVEL).upper(), logging.INFO)

    # Create logger
    logger = logging.getLogger('spotichart')
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )

    # File handler with rotation
    if log_file or Config.LOG_FILE:
        file_path = log_file or Config.LOG_FILE
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=Config.LOG_MAX_BYTES,
            backupCount=Config.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)  # Log everything to file
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    logger.info(f"Logging initialized at {logging.getLevelName(level)} level")

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(f'spotichart.{name}')
