"""
Logging Configuration Module

Sets up advanced logging with rotation and formatting.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(
    log_level: str = None, log_file: str = None, console: bool = True
) -> logging.Logger:
    """
    Configure application logging with rotation.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (default: logs/spotichart.log)
        console: Whether to also log to console

    Returns:
        Configured logger instance
    """
    # Default configuration values
    default_log_level = os.getenv("LOG_LEVEL", "INFO")
    default_log_dir = Path(__file__).parent.parent.parent / "logs"
    default_log_file = str(default_log_dir / "spotichart.log")
    default_max_bytes = 10485760  # 10MB
    default_backup_count = 5

    # Ensure log directory exists
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    else:
        default_log_dir.mkdir(parents=True, exist_ok=True)

    # Get log level
    level = getattr(logging, (log_level or default_log_level).upper(), logging.INFO)

    # Create logger
    logger = logging.getLogger("spotichart")
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatters
    detailed_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    simple_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
    )

    # File handler with rotation
    if log_file or default_log_file:
        file_path = log_file or default_log_file
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=default_max_bytes,
            backupCount=default_backup_count,
            encoding="utf-8",
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
    return logging.getLogger(f"spotichart.{name}")
