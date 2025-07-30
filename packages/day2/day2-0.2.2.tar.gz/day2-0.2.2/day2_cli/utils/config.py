"""Configuration utilities for the MontyCloud DAY2 CLI."""

import json
from pathlib import Path
from typing import Any, Dict, Optional


def get_config_dir() -> Path:
    """Get the configuration directory.

    Returns:
        Path to the configuration directory.
    """
    config_dir = Path.home() / ".montycloud"
    config_dir.mkdir(exist_ok=True)
    return config_dir


def load_config() -> Dict[str, Any]:
    """Load configuration from the config file.

    Returns:
        Configuration dictionary.
    """
    config_file = get_config_dir() / "config"

    if not config_file.exists():
        return {}

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            result: Dict[str, Any] = json.load(f)
            return result
    except (json.JSONDecodeError, IOError):
        empty_dict: Dict[str, Any] = {}
        return empty_dict


def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to the config file.

    Args:
        config: Configuration dictionary to save.
    """
    config_file = get_config_dir() / "config"

    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f)


def get_config_value(key: str, default: Optional[Any] = None) -> Optional[Any]:
    """Get a value from the configuration.

    Args:
        key: Configuration key to get.
        default: Default value to return if the key is not found.

    Returns:
        Configuration value or default.
    """
    config = load_config()
    return config.get(key, default)


def set_config_value(key: str, value: Any) -> None:
    """Set a value in the configuration.

    Args:
        key: Configuration key to set.
        value: Value to set.
    """
    config = load_config()
    config[key] = value
    save_config(config)


def load_credentials() -> Dict[str, Any]:
    """Load credentials from the credentials file.

    Returns:
        Credentials dictionary.
    """
    credentials_file = get_config_dir() / "credentials"

    if not credentials_file.exists():
        return {}

    try:
        with open(credentials_file, "r", encoding="utf-8") as f:
            result: Dict[str, Any] = json.load(f)
            return result
    except (json.JSONDecodeError, IOError):
        empty_dict: Dict[str, Any] = {}
        return empty_dict


def save_credentials(credentials: Dict[str, Any]) -> None:
    """Save credentials to the credentials file.

    Args:
        credentials: Credentials dictionary to save.
    """
    credentials_file = get_config_dir() / "credentials"

    with open(credentials_file, "w", encoding="utf-8") as f:
        json.dump(credentials, f)


def get_credential_value(key: str, default: Optional[Any] = None) -> Optional[Any]:
    """Get a value from the credentials.

    Args:
        key: Credential key to get.
        default: Default value to return if the key is not found.

    Returns:
        Credential value or default.
    """
    credentials = load_credentials()
    return credentials.get(key, default)


def set_credential_value(key: str, value: Any) -> None:
    """Set a value in the credentials.

    Args:
        key: Credential key to set.
        value: Value to set.
    """
    credentials = load_credentials()
    credentials[key] = value
    save_credentials(credentials)
