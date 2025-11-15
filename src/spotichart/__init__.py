"""
Spotichart

A professional Python application for creating Spotify playlists from Kworb charts.
"""

__version__ = "2.0.0"

from .core.spotify_client import SpotifyClient
from .core.scraper import KworbScraper
from .config import Config

__all__ = ['SpotifyClient', 'KworbScraper', 'Config']
