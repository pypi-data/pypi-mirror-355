"""Tests for the Config class and configuration system."""

import configparser
import os
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from day2 import Session
from day2.client.config import Config


class TestConfig:
    """Test suite for the Config class."""

    def test_config_default_values(self):
        """Test that Config has the expected default values."""
        config = Config()
        assert config.base_url == "https://api.montycloud.com/day2/api"
        assert config.api_version == "v1"
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.retry_backoff_factor == 1.0
        assert config.tenant_id == ""

    def test_config_custom_values(self):
        """Test that Config can be initialized with custom values."""
        config = Config(
            base_url="https://custom-api.example.com",
            api_version="v2",
            timeout=300,
            max_retries=5,
            retry_backoff_factor=2.0,
            tenant_id="tenant-123",
        )
        assert config.base_url == "https://custom-api.example.com"
        assert config.api_version == "v2"
        assert config.timeout == 300
        assert config.max_retries == 5
        assert config.retry_backoff_factor == 2.0
        assert config.tenant_id == "tenant-123"

    def test_config_api_url(self):
        """Test that api_url property returns the correct URL."""
        config = Config(base_url="https://api.example.com", api_version="v2")
        assert config.api_url == "https://api.example.com/v2"

    def test_config_to_dict(self):
        """Test that to_dict method returns a dictionary with all config values."""
        config = Config(
            base_url="https://api.example.com",
            api_version="v2",
            timeout=300,
            max_retries=5,
            retry_backoff_factor=2.0,
            tenant_id="tenant-123",
        )
        config_dict = config.to_dict()
        assert config_dict["base_url"] == "https://api.example.com"
        assert config_dict["api_version"] == "v2"
        assert config_dict["timeout"] == 300
        assert config_dict["max_retries"] == 5
        assert config_dict["retry_backoff_factor"] == 2.0
        assert config_dict["tenant_id"] == "tenant-123"

    def test_config_from_dict(self):
        """Test that from_dict method creates a Config with the expected values."""
        config_dict = {
            "base_url": "https://api.example.com",
            "api_version": "v2",
            "timeout": 300,
            "max_retries": 5,
            "retry_backoff_factor": 2.0,
            "tenant_id": "tenant-123",
        }
        config = Config.from_dict(config_dict)
        assert config.base_url == "https://api.example.com"
        assert config.api_version == "v2"
        assert config.timeout == 300
        assert config.max_retries == 5
        assert config.retry_backoff_factor == 2.0
        assert config.tenant_id == "tenant-123"

    def test_config_from_file_not_exists(self, tmp_path):
        """Test that from_file returns default config when file doesn't exist."""
        with patch("pathlib.Path.home", return_value=tmp_path):
            config = Config.from_file()
            assert config.base_url == "https://api.montycloud.com/day2/api"
            assert config.api_version == "v1"
            assert config.timeout == 30
            assert config.max_retries == 3
            assert config.retry_backoff_factor == 1.0
            assert config.tenant_id == ""

    def test_config_from_file_exists(self, tmp_path):
        """Test that from_file loads config from file when it exists."""
        # Create a mock config file
        config_dir = tmp_path / ".day2"
        config_dir.mkdir()
        config_file = config_dir / "config"
        config_data = {
            "base_url": "https://api.example.com",
            "api_version": "v2",
            "timeout": 300,
            "max_retries": 5,
            "retry_backoff_factor": 2.0,
            "tenant_id": "tenant-123",
        }
        config_parser = configparser.ConfigParser()
        config_parser["DEFAULT"] = {k: str(v) for k, v in config_data.items()}
        with open(config_file, "w", encoding="utf-8") as f:
            config_parser.write(f)

        with patch("pathlib.Path.home", return_value=tmp_path):
            config = Config.from_file()
            assert config.base_url == "https://api.example.com"
            assert config.api_version == "v2"
            assert config.timeout == 300
            assert config.max_retries == 5
            assert config.retry_backoff_factor == 2.0
            assert config.tenant_id == "tenant-123"

    def test_config_from_file_invalid_ini(self, tmp_path):
        """Test that from_file returns default config when file has invalid INI format."""
        # Create a mock config file with invalid INI format
        config_dir = tmp_path / ".day2"
        config_dir.mkdir()
        config_file = config_dir / "config"
        with open(config_file, "w", encoding="utf-8") as f:
            f.write("invalid ini content")

        with patch("pathlib.Path.home", return_value=tmp_path):
            config = Config.from_file()
            assert config.base_url == "https://api.montycloud.com/day2/api"
            assert config.api_version == "v1"
            assert config.timeout == 30
            assert config.max_retries == 3
            assert config.retry_backoff_factor == 1.0
            assert config.tenant_id == ""

    def test_config_from_file_partial_config(self, tmp_path):
        """Test that from_file merges partial config with defaults."""
        # Create a mock config file with only some values
        config_dir = tmp_path / ".day2"
        config_dir.mkdir()
        config_file = config_dir / "config"
        config_data = {
            "base_url": "https://api.example.com",
            "tenant_id": "tenant-123",
        }
        config_parser = configparser.ConfigParser()
        config_parser["DEFAULT"] = {k: str(v) for k, v in config_data.items()}
        with open(config_file, "w", encoding="utf-8") as f:
            config_parser.write(f)

        with patch("pathlib.Path.home", return_value=tmp_path):
            config = Config.from_file()
            assert config.base_url == "https://api.example.com"  # From file
            assert config.api_version == "v1"  # Default
            assert config.timeout == 30  # Default
            assert config.max_retries == 3  # Default
            assert config.retry_backoff_factor == 1.0  # Default
            assert config.tenant_id == "tenant-123"  # From file

    def test_config_from_file_custom_path(self, tmp_path):
        """Test that from_file can load config from a custom path."""
        # Create a mock config file in a custom location
        custom_config_file = tmp_path / "custom-config"
        config_data = {
            "base_url": "https://custom-api.example.com",
            "api_version": "v3",
            "timeout": 500,
            "max_retries": 10,
            "retry_backoff_factor": 3.0,
            "tenant_id": "custom-tenant",
        }
        config_parser = configparser.ConfigParser()
        config_parser["DEFAULT"] = {k: str(v) for k, v in config_data.items()}
        with open(custom_config_file, "w", encoding="utf-8") as f:
            config_parser.write(f)

        config = Config.from_file(custom_config_file)
        assert config.base_url == "https://custom-api.example.com"
        assert config.api_version == "v3"
        assert config.timeout == 500
        assert config.max_retries == 10
        assert config.retry_backoff_factor == 3.0
        assert config.tenant_id == "custom-tenant"


class TestSessionWithConfig:
    """Test suite for Session integration with Config."""

    def test_session_uses_config_tenant_id(self, tmp_path):
        """Test that Session uses tenant_id from Config."""
        # Create a mock config file
        config_dir = tmp_path / ".day2"
        config_dir.mkdir()
        config_file = config_dir / "config"
        config_data = {
            "tenant_id": "config-tenant-123",
        }
        config_parser = configparser.ConfigParser()
        config_parser["DEFAULT"] = {k: str(v) for k, v in config_data.items()}
        with open(config_file, "w", encoding="utf-8") as f:
            config_parser.write(f)

        with patch("pathlib.Path.home", return_value=tmp_path):
            session = Session(api_key="test-api-key")
            assert session.tenant_id == "config-tenant-123"

    def test_session_explicit_tenant_id_overrides_config(self, tmp_path):
        """Test that explicit tenant_id overrides config tenant_id."""
        # Create a mock config file
        config_dir = tmp_path / ".day2"
        config_dir.mkdir()
        config_file = config_dir / "config"
        config_data = {
            "tenant_id": "config-tenant-123",
        }
        config_parser = configparser.ConfigParser()
        config_parser["DEFAULT"] = {k: str(v) for k, v in config_data.items()}
        with open(config_file, "w", encoding="utf-8") as f:
            config_parser.write(f)

        with patch("pathlib.Path.home", return_value=tmp_path):
            session = Session(api_key="test-api-key", tenant_id="explicit-tenant-456")
            assert session.tenant_id == "explicit-tenant-456"

    def test_session_uses_config_timeout(self, tmp_path):
        """Test that Session uses timeout from Config."""
        # Create a mock config file
        config_dir = tmp_path / ".day2"
        config_dir.mkdir()
        config_file = config_dir / "config"
        config_data = {
            "timeout": 300,
        }
        config_parser = configparser.ConfigParser()
        config_parser["DEFAULT"] = {k: str(v) for k, v in config_data.items()}
        with open(config_file, "w", encoding="utf-8") as f:
            config_parser.write(f)

        with patch("pathlib.Path.home", return_value=tmp_path):
            session = Session(api_key="test-api-key")
            assert session._config.timeout == 300

    def test_session_saves_tenant_id_to_config(self, tmp_path):
        """Test that Session.set_tenant saves tenant_id to config file."""
        # Mock the home directory
        with patch("pathlib.Path.home", return_value=tmp_path):
            # Create session and set tenant
            session = Session(api_key="test-api-key")
            session.set_tenant("new-tenant-789")

            # Check that config file was created with the tenant_id
            config_file = tmp_path / ".day2" / "config"
            assert config_file.exists()
            config_parser = configparser.ConfigParser()
            config_parser.read(config_file)
            assert config_parser.get("DEFAULT", "tenant_id") == "new-tenant-789"

    def test_session_clear_tenant_behavior(self, tmp_path):
        """Test the behavior of Session.clear_tenant.

        Note: The current implementation of Session.clear_tenant sets tenant_id to None
        in the session but does not remove it from the config file. This is because
        _save_tenant_to_config has an early return when tenant_id is None.
        """
        # Create a mock config file
        config_dir = tmp_path / ".day2"
        config_dir.mkdir()
        config_file = config_dir / "config"
        config_data = {
            "tenant_id": "config-tenant-123",
            "timeout": 300,
        }
        config_parser = configparser.ConfigParser()
        config_parser["DEFAULT"] = {k: str(v) for k, v in config_data.items()}
        with open(config_file, "w", encoding="utf-8") as f:
            config_parser.write(f)

        with patch("pathlib.Path.home", return_value=tmp_path):
            # Create session and clear tenant
            session = Session(api_key="test-api-key")
            session.clear_tenant()

            # Verify tenant_id is None in the session
            assert session.tenant_id is None

            # Verify config file is unchanged (current behavior)
            config_parser = configparser.ConfigParser()
            config_parser.read(config_file)
            assert (
                config_parser.get("DEFAULT", "tenant_id") == "config-tenant-123"
            )  # Still in config
            assert (
                config_parser.get("DEFAULT", "timeout") == "300"
            )  # Other settings preserved
