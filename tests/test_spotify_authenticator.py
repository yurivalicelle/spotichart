"""Tests for SpotifyAuthenticator."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from spotichart.core.spotify_authenticator import SpotifyAuthenticator
from spotichart.utils.exceptions import SpotifyAuthError


@pytest.fixture
def auth_params():
    """Provide authentication parameters."""
    return {
        "client_id": "test_client_id",
        "client_secret": "test_secret",
        "redirect_uri": "http://localhost:8888/callback",
        "scope": "playlist-modify-private",
        "cache_path": Path("/tmp/test_cache.json"),
        "request_timeout": 30,
    }


class TestSpotifyAuthenticatorInit:
    """Tests for SpotifyAuthenticator initialization."""

    def test_init_with_all_params(self, auth_params):
        """Should initialize with all parameters."""
        authenticator = SpotifyAuthenticator(**auth_params)

        assert authenticator.client_id == "test_client_id"
        assert authenticator.client_secret == "test_secret"
        assert authenticator.redirect_uri == "http://localhost:8888/callback"
        assert authenticator.scope == "playlist-modify-private"
        assert authenticator.cache_path == Path("/tmp/test_cache.json")
        assert authenticator.request_timeout == 30

    def test_init_with_minimal_params(self):
        """Should initialize with minimal parameters."""
        authenticator = SpotifyAuthenticator(
            client_id="id",
            client_secret="secret",
            redirect_uri="http://localhost:8888/callback",
            scope="test-scope",
        )

        assert authenticator.client_id == "id"
        assert authenticator.cache_path is None
        assert authenticator.request_timeout == 30

    def test_init_lazy_loading(self, auth_params):
        """Should not authenticate on initialization (lazy loading)."""
        authenticator = SpotifyAuthenticator(**auth_params)

        assert authenticator._sp is None
        assert authenticator._user_id is None


class TestSpotifyAuthenticatorAuthenticate:
    """Tests for authenticate method."""

    @patch("spotichart.core.spotify_authenticator.spotipy.Spotify")
    @patch("spotichart.core.spotify_authenticator.SpotifyOAuth")
    def test_authenticate_success(self, mock_oauth_class, mock_spotify_class, auth_params):
        """Should authenticate successfully."""
        # Setup mocks
        mock_oauth = MagicMock()
        mock_oauth_class.return_value = mock_oauth

        mock_sp = MagicMock()
        mock_sp.me.return_value = {"id": "test_user_123"}
        mock_spotify_class.return_value = mock_sp

        # Create authenticator and authenticate
        authenticator = SpotifyAuthenticator(**auth_params)
        result = authenticator.authenticate()

        # Verify OAuth was created with correct params
        mock_oauth_class.assert_called_once()
        call_kwargs = mock_oauth_class.call_args.kwargs
        assert call_kwargs["client_id"] == "test_client_id"
        assert call_kwargs["client_secret"] == "test_secret"
        assert call_kwargs["redirect_uri"] == "http://localhost:8888/callback"
        assert call_kwargs["scope"] == "playlist-modify-private"
        assert call_kwargs["requests_timeout"] == 30

        # Verify Spotify client was created
        mock_spotify_class.assert_called_once_with(auth_manager=mock_oauth)

        # Verify user info was retrieved
        mock_sp.me.assert_called_once()

        # Verify result
        assert result == mock_sp
        assert authenticator._sp == mock_sp
        assert authenticator._user_id == "test_user_123"

    @patch("spotichart.core.spotify_authenticator.spotipy.Spotify")
    @patch("spotichart.core.spotify_authenticator.SpotifyOAuth")
    def test_authenticate_with_cache_path(self, mock_oauth_class, mock_spotify_class, auth_params):
        """Should use cache path if provided."""
        mock_oauth = MagicMock()
        mock_oauth_class.return_value = mock_oauth

        mock_sp = MagicMock()
        mock_sp.me.return_value = {"id": "user_123"}
        mock_spotify_class.return_value = mock_sp

        authenticator = SpotifyAuthenticator(**auth_params)
        authenticator.authenticate()

        # Verify cache_path was passed as string
        call_kwargs = mock_oauth_class.call_args.kwargs
        assert call_kwargs["cache_path"] == str(Path("/tmp/test_cache.json"))

    @patch("spotichart.core.spotify_authenticator.spotipy.Spotify")
    @patch("spotichart.core.spotify_authenticator.SpotifyOAuth")
    def test_authenticate_without_cache_path(self, mock_oauth_class, mock_spotify_class):
        """Should handle None cache path."""
        mock_oauth = MagicMock()
        mock_oauth_class.return_value = mock_oauth

        mock_sp = MagicMock()
        mock_sp.me.return_value = {"id": "user_123"}
        mock_spotify_class.return_value = mock_sp

        authenticator = SpotifyAuthenticator(
            client_id="id",
            client_secret="secret",
            redirect_uri="http://localhost:8888/callback",
            scope="test",
            cache_path=None,
        )
        authenticator.authenticate()

        # Verify cache_path is None
        call_kwargs = mock_oauth_class.call_args.kwargs
        assert call_kwargs["cache_path"] is None

    @patch("spotichart.core.spotify_authenticator.SpotifyOAuth")
    def test_authenticate_oauth_failure(self, mock_oauth_class, auth_params):
        """Should raise SpotifyAuthError on OAuth failure."""
        mock_oauth_class.side_effect = Exception("OAuth Error")

        authenticator = SpotifyAuthenticator(**auth_params)

        with pytest.raises(SpotifyAuthError, match="Authentication failed: OAuth Error"):
            authenticator.authenticate()

    @patch("spotichart.core.spotify_authenticator.spotipy.Spotify")
    @patch("spotichart.core.spotify_authenticator.SpotifyOAuth")
    def test_authenticate_me_failure(self, mock_oauth_class, mock_spotify_class, auth_params):
        """Should raise SpotifyAuthError on me() failure."""
        mock_oauth = MagicMock()
        mock_oauth_class.return_value = mock_oauth

        mock_sp = MagicMock()
        mock_sp.me.side_effect = Exception("API Error")
        mock_spotify_class.return_value = mock_sp

        authenticator = SpotifyAuthenticator(**auth_params)

        with pytest.raises(SpotifyAuthError, match="Authentication failed: API Error"):
            authenticator.authenticate()

    @patch("spotichart.core.spotify_authenticator.spotipy.Spotify")
    @patch("spotichart.core.spotify_authenticator.SpotifyOAuth")
    def test_authenticate_caches_result(self, mock_oauth_class, mock_spotify_class, auth_params):
        """Should cache authentication result."""
        mock_oauth = MagicMock()
        mock_oauth_class.return_value = mock_oauth

        mock_sp = MagicMock()
        mock_sp.me.return_value = {"id": "user_123"}
        mock_spotify_class.return_value = mock_sp

        authenticator = SpotifyAuthenticator(**auth_params)

        # Authenticate twice
        result1 = authenticator.authenticate()
        result2 = authenticator.authenticate()

        # Should only create OAuth once
        assert mock_oauth_class.call_count == 1
        assert result1 == result2


class TestSpotifyAuthenticatorGetClient:
    """Tests for get_client method."""

    @patch("spotichart.core.spotify_authenticator.spotipy.Spotify")
    @patch("spotichart.core.spotify_authenticator.SpotifyOAuth")
    def test_get_client_authenticates_if_needed(
        self, mock_oauth_class, mock_spotify_class, auth_params
    ):
        """Should authenticate if not already authenticated."""
        mock_oauth = MagicMock()
        mock_oauth_class.return_value = mock_oauth

        mock_sp = MagicMock()
        mock_sp.me.return_value = {"id": "user_123"}
        mock_spotify_class.return_value = mock_sp

        authenticator = SpotifyAuthenticator(**auth_params)

        # Get client (should trigger authentication)
        client = authenticator.get_client()

        assert client == mock_sp
        mock_oauth_class.assert_called_once()

    @patch("spotichart.core.spotify_authenticator.spotipy.Spotify")
    @patch("spotichart.core.spotify_authenticator.SpotifyOAuth")
    def test_get_client_returns_cached(self, mock_oauth_class, mock_spotify_class, auth_params):
        """Should return cached client if already authenticated."""
        mock_oauth = MagicMock()
        mock_oauth_class.return_value = mock_oauth

        mock_sp = MagicMock()
        mock_sp.me.return_value = {"id": "user_123"}
        mock_spotify_class.return_value = mock_sp

        authenticator = SpotifyAuthenticator(**auth_params)

        # Pre-authenticate
        authenticator.authenticate()

        # Get client multiple times
        client1 = authenticator.get_client()
        client2 = authenticator.get_client()

        # Should only authenticate once
        assert mock_oauth_class.call_count == 1
        assert client1 == client2 == mock_sp


class TestSpotifyAuthenticatorGetUserId:
    """Tests for get_user_id method."""

    @patch("spotichart.core.spotify_authenticator.spotipy.Spotify")
    @patch("spotichart.core.spotify_authenticator.SpotifyOAuth")
    def test_get_user_id_authenticates_if_needed(
        self, mock_oauth_class, mock_spotify_class, auth_params
    ):
        """Should authenticate if not already authenticated."""
        mock_oauth = MagicMock()
        mock_oauth_class.return_value = mock_oauth

        mock_sp = MagicMock()
        mock_sp.me.return_value = {"id": "test_user_456"}
        mock_spotify_class.return_value = mock_sp

        authenticator = SpotifyAuthenticator(**auth_params)

        # Get user ID (should trigger authentication)
        user_id = authenticator.get_user_id()

        assert user_id == "test_user_456"
        mock_oauth_class.assert_called_once()

    @patch("spotichart.core.spotify_authenticator.spotipy.Spotify")
    @patch("spotichart.core.spotify_authenticator.SpotifyOAuth")
    def test_get_user_id_returns_cached(self, mock_oauth_class, mock_spotify_class, auth_params):
        """Should return cached user ID if already authenticated."""
        mock_oauth = MagicMock()
        mock_oauth_class.return_value = mock_oauth

        mock_sp = MagicMock()
        mock_sp.me.return_value = {"id": "cached_user"}
        mock_spotify_class.return_value = mock_sp

        authenticator = SpotifyAuthenticator(**auth_params)

        # Pre-authenticate
        authenticator.authenticate()

        # Get user ID multiple times
        user_id1 = authenticator.get_user_id()
        user_id2 = authenticator.get_user_id()

        # Should only authenticate once
        assert mock_oauth_class.call_count == 1
        assert user_id1 == user_id2 == "cached_user"


class TestSpotifyAuthenticatorIntegration:
    """Integration tests for SpotifyAuthenticator."""

    @patch("spotichart.core.spotify_authenticator.spotipy.Spotify")
    @patch("spotichart.core.spotify_authenticator.SpotifyOAuth")
    def test_full_authentication_flow(self, mock_oauth_class, mock_spotify_class, auth_params):
        """Should handle full authentication flow correctly."""
        mock_oauth = MagicMock()
        mock_oauth_class.return_value = mock_oauth

        mock_sp = MagicMock()
        mock_sp.me.return_value = {"id": "integration_user"}
        mock_spotify_class.return_value = mock_sp

        authenticator = SpotifyAuthenticator(**auth_params)

        # Verify initial state
        assert authenticator._sp is None
        assert authenticator._user_id is None

        # Get client
        client = authenticator.get_client()
        assert client == mock_sp

        # Get user ID
        user_id = authenticator.get_user_id()
        assert user_id == "integration_user"

        # Verify only authenticated once
        assert mock_oauth_class.call_count == 1
        assert mock_sp.me.call_count == 1
