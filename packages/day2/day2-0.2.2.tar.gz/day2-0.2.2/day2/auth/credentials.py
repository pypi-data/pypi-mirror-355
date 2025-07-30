"""Credential management for the MontyCloud SDK."""

import configparser
import os
from pathlib import Path
from typing import Optional


class Credentials:
    """Manages API keys and other authentication credentials."""

    def __init__(
        self, api_key: Optional[str] = None, api_secret_key: Optional[str] = None
    ):
        """Initialize credentials.

        Args:
            api_key: API key for authentication. If not provided, will attempt to load
                from environment variables or configuration file.
            api_secret_key: API secret key for authentication. If not provided, will attempt to load
                from environment variables or configuration file.
        """
        self.api_key = api_key or self._load_from_env() or self._load_from_config()
        self.secret_key = (
            api_secret_key
            or self._load_token_from_env()
            or self._load_token_from_config()
        )

        if not self.api_key:
            raise ValueError(
                "No API key provided. Please provide an API key via the constructor, "
                "environment variable DAY2_API_KEY, or configuration file."
            )

    def _load_from_env(self) -> Optional[str]:
        """Load API key from environment variables.

        Returns:
            API key if found in environment variables, None otherwise.
        """
        return os.environ.get("DAY2_API_KEY")

    def _load_token_from_env(self) -> Optional[str]:
        """Load API secret key from environment variables.

        Returns:
            API secret key if found in environment variables, None otherwise.
        """
        return os.environ.get("DAY2_API_SECRET_KEY")

    def _load_from_config(self) -> Optional[str]:
        """Load API key from credentials file.

        Returns:
            API key if found in credentials file, None otherwise.
        """
        config_dir = Path.home() / ".day2"
        credentials_file = config_dir / "credentials"

        if not credentials_file.exists():
            return None

        try:
            config_parser = configparser.ConfigParser()
            config_parser.read(credentials_file)
            return config_parser.get("DEFAULT", "api_key", fallback=None)
        except (configparser.Error, IOError):
            return None

    def _load_token_from_config(self) -> Optional[str]:
        """Load API secret key from credentials file.

        Returns:
            API secret key if found in credentials file, None otherwise.
        """
        config_dir = Path.home() / ".day2"
        credentials_file = config_dir / "credentials"

        if not credentials_file.exists():
            return None

        try:
            config_parser = configparser.ConfigParser()
            config_parser.read(credentials_file)
            return config_parser.get("DEFAULT", "api_secret_key", fallback=None)
        except (configparser.Error, IOError):
            return None

    def save_to_config(self) -> None:
        """Save credentials to credentials file."""
        if not self.api_key:
            return

        config_dir = Path.home() / ".day2"
        config_dir.mkdir(exist_ok=True)

        credentials_file = config_dir / "credentials"

        # Load existing credentials if they exist
        config_parser = configparser.ConfigParser()
        if credentials_file.exists():
            config_parser.read(credentials_file)

        # Ensure the DEFAULT section exists
        if "DEFAULT" not in config_parser:
            config_parser["DEFAULT"] = {}

        # Update config with API key
        config_parser["DEFAULT"]["api_key"] = self.api_key

        # Update config with API secret key if available
        if self.secret_key:
            config_parser["DEFAULT"]["api_secret_key"] = self.secret_key

        # Save credentials
        with open(credentials_file, "w", encoding="utf-8") as f:
            config_parser.write(f)
