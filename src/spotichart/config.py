"""
Configuration Module

Centralizes all configuration settings for the Spotichart.
Loads environment variables and provides default values.
"""

import os
from typing import List
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """Application configuration class."""

    # Application Info
    APP_NAME = "Spotichart"
    APP_VERSION = "2.0.0"

    # Spotify API Configuration
    SPOTIFY_CLIENT_ID: str = os.getenv('SPOTIFY_CLIENT_ID', '')
    SPOTIFY_CLIENT_SECRET: str = os.getenv('SPOTIFY_CLIENT_SECRET', '')
    REDIRECT_URI: str = os.getenv('REDIRECT_URI', 'http://localhost:8888/callback')
    SPOTIFY_SCOPE: str = 'playlist-modify-private playlist-modify-public'

    # Kworb URLs
    KWORB_URLS: dict = {
        'brazil': 'https://kworb.net/spotify/country/br_weekly_totals.html',
        'global': 'https://kworb.net/spotify/country/global_weekly_totals.html',
        'us': 'https://kworb.net/spotify/country/us_weekly_totals.html',
        'uk': 'https://kworb.net/spotify/country/gb_weekly_totals.html',
    }

    # Application Settings
    DEFAULT_PLAYLIST_LIMIT: int = int(os.getenv('PLAYLIST_LIMIT', '1000'))
    REQUEST_TIMEOUT: int = int(os.getenv('REQUEST_TIMEOUT', '30'))
    SPOTIFY_BATCH_SIZE: int = 100  # Maximum tracks to add per API call
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 2  # seconds

    # Logging Configuration
    LOG_DIR = Path(__file__).parent.parent.parent / 'logs'
    LOG_FILE: str = str(LOG_DIR / 'spotichart.log')
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5

    # Flask Configuration (if used)
    FLASK_SECRET_KEY: str = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_DEBUG: bool = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    FLASK_HOST: str = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT: int = int(os.getenv('FLASK_PORT', '5000'))

    # Cache Configuration
    CACHE_ENABLED: bool = os.getenv('CACHE_ENABLED', 'True').lower() == 'true'
    CACHE_DIR = Path(__file__).parent.parent.parent / '.cache'

    @classmethod
    def validate(cls) -> bool:
        """
        Validate that required configuration values are present.

        Uses ConfigValidator to delegate validation logic (SRP).

        Returns:
            True if configuration is valid, False otherwise
        """
        from .utils.config_validator import ConfigValidator

        config_dict = {
            'SPOTIFY_CLIENT_ID': cls.SPOTIFY_CLIENT_ID,
            'SPOTIFY_CLIENT_SECRET': cls.SPOTIFY_CLIENT_SECRET,
            'REDIRECT_URI': cls.REDIRECT_URI,
            'DEFAULT_PLAYLIST_LIMIT': cls.DEFAULT_PLAYLIST_LIMIT,
            'REQUEST_TIMEOUT': cls.REQUEST_TIMEOUT,
        }

        is_valid, errors = ConfigValidator.validate_all(config_dict)

        if not is_valid:
            for error in errors:
                print(f"Configuration error: {error}")

        return is_valid

    @classmethod
    def get_kworb_url(cls, region: str = 'brazil') -> str:
        """
        Get Kworb URL for specific region.

        Args:
            region: Region identifier ('brazil', 'global', 'us', 'uk')

        Returns:
            URL for the specified region
        """
        return cls.KWORB_URLS.get(region.lower(), cls.KWORB_URLS['brazil'])

    @classmethod
    def get_available_regions(cls) -> List[str]:
        """
        Get list of available regions.

        Returns:
            List of region names
        """
        return list(cls.KWORB_URLS.keys())

    @classmethod
    def setup_directories(cls) -> None:
        """
        Create necessary directories if they don't exist.

        Uses DirectoryManager to delegate filesystem operations (SRP).
        """
        from .utils.directory_manager import DirectoryManager

        # Create log directory
        DirectoryManager.ensure_directory_exists(cls.LOG_DIR, create=True)

        # Handle cache directory - remove if it's a file
        if cls.CACHE_DIR.exists() and cls.CACHE_DIR.is_file():
            # Rename old cache file to .spotify_cache
            backup_path = cls.CACHE_DIR.parent / '.spotify_cache'
            if not backup_path.exists():
                cls.CACHE_DIR.rename(backup_path)
            else:
                cls.CACHE_DIR.unlink()

        # Create cache directory
        DirectoryManager.ensure_directory_exists(cls.CACHE_DIR, create=True)
