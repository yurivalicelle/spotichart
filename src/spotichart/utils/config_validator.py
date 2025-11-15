class ConfigValidator:
    @staticmethod
    def validate_spotify_credentials(client_id: str, client_secret: str):
        if not client_id:
            return False, "Spotify client_id is missing."
        if not client_secret:
            return False, "Spotify client_secret is missing."
        return True, None

    @staticmethod
    def validate_redirect_uri(uri: str):
        if not uri:
            return False, "Redirect_uri is missing."
        return True, None

    @staticmethod
    def validate_numeric(name: str, value, min_value=None):
        if not isinstance(value, (int, float)):
            return False, f"{name} must be a number."
        if min_value is not None and value < min_value:
            return False, f"{name} must be at least {min_value}."
        return True, None

    @staticmethod
    def validate_all(config: dict):
        errors = []
        
        # Simplified validation logic
        if not config.get('SPOTIFY_CLIENT_ID') or not config.get('SPOTIFY_CLIENT_SECRET'):
            errors.append("Spotify credentials are required.")
            
        return not errors, errors
