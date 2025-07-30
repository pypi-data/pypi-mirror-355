"""Tests for the CLI config commands."""

import configparser
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from day2_cli.cli import cli
from day2_cli.commands.config import config, ensure_config_dir, load_config, save_config


class TestConfigUtils:
    """Test suite for config utility functions."""

    def test_ensure_config_dir(self, tmp_path):
        """Test that ensure_config_dir creates the config directory."""
        with patch(
            "day2_cli.commands.config.CONFIG_PATH", tmp_path / ".day2" / "config"
        ):
            ensure_config_dir()
            assert (tmp_path / ".day2").exists()
            assert (tmp_path / ".day2").is_dir()

    def test_load_config_not_exists(self, tmp_path):
        """Test that load_config returns empty dict when file doesn't exist."""
        with patch("day2_cli.commands.config.CONFIG_PATH", tmp_path / "nonexistent"):
            config_data = load_config()
            assert config_data == {}

    def test_load_config_exists(self, tmp_path):
        """Test that load_config loads config from file when it exists."""
        config_file = tmp_path / "config"
        config_data = {"tenant_id": "test-tenant", "timeout": 300}
        config_parser = configparser.ConfigParser()
        config_parser["DEFAULT"] = {k: str(v) for k, v in config_data.items()}
        with open(config_file, "w", encoding="utf-8") as f:
            config_parser.write(f)

        with patch("day2_cli.commands.config.CONFIG_PATH", config_file):
            loaded_data = load_config()
            assert loaded_data["tenant_id"] == config_data["tenant_id"]
            assert loaded_data["timeout"] == str(config_data["timeout"])

    def test_load_config_invalid_ini(self, tmp_path):
        """Test that load_config returns empty dict when file has invalid INI format."""
        config_file = tmp_path / "config"
        with open(config_file, "w", encoding="utf-8") as f:
            f.write("invalid ini content")

        with patch("day2_cli.commands.config.CONFIG_PATH", config_file):
            loaded_data = load_config()
            assert loaded_data == {}

    def test_save_config(self, tmp_path):
        """Test that save_config saves config to file."""
        config_file = tmp_path / ".day2" / "config"
        config_data = {"tenant_id": "test-tenant", "timeout": 300}

        with patch("day2_cli.commands.config.CONFIG_PATH", config_file):
            save_config(config_data)
            assert config_file.exists()
            config_parser = configparser.ConfigParser()
            config_parser.read(config_file)
            loaded_data = dict(config_parser["DEFAULT"])
            assert loaded_data["tenant_id"] == config_data["tenant_id"]
            assert loaded_data["timeout"] == str(config_data["timeout"])


class TestConfigCommands:
    """Test suite for config CLI commands."""

    @pytest.fixture
    def runner(self):
        """Create a CLI runner."""
        return CliRunner()

    def test_config_set(self, runner, tmp_path):
        """Test the config set command."""
        config_file = tmp_path / ".day2" / "config"

        with patch("day2_cli.commands.config.CONFIG_PATH", config_file):
            # Set tenant-id
            result = runner.invoke(config, ["set", "tenant-id", "test-tenant"])
            assert result.exit_code == 0
            assert "Configuration 'tenant-id' set to 'test-tenant'" in result.output

            # Verify config file
            config_parser = configparser.ConfigParser()
            config_parser.read(config_file)
            assert config_parser["DEFAULT"]["tenant_id"] == "test-tenant"

            # Set timeout (integer value)
            result = runner.invoke(config, ["set", "timeout", "300"])
            assert result.exit_code == 0
            assert "Configuration 'timeout' set to '300'" in result.output

            # Verify config file
            config_parser = configparser.ConfigParser()
            config_parser.read(config_file)
            assert config_parser["DEFAULT"]["timeout"] == "300"  # String in INI format
            assert (
                config_parser["DEFAULT"]["tenant_id"] == "test-tenant"
            )  # Previous value preserved

    def test_config_set_invalid_key(self, runner, tmp_path):
        """Test the config set command with an invalid key."""
        config_file = tmp_path / ".day2" / "config"

        with patch("day2_cli.commands.config.CONFIG_PATH", config_file):
            result = runner.invoke(config, ["set", "invalid-key", "value"])
            assert result.exit_code == 0
            assert "Error: Unknown configuration key 'invalid-key'" in result.output
            assert "Available keys:" in result.output

    def test_config_set_invalid_value_type(self, runner, tmp_path):
        """Test the config set command with an invalid value type."""
        config_file = tmp_path / ".day2" / "config"

        with patch("day2_cli.commands.config.CONFIG_PATH", config_file):
            # Try to set timeout to a non-integer
            result = runner.invoke(config, ["set", "timeout", "not-a-number"])
            assert result.exit_code == 0
            assert "Error: 'timeout' must be an integer" in result.output

    def test_config_get(self, runner, tmp_path):
        """Test the config get command."""
        config_file = tmp_path / ".day2" / "config"
        config_data = {"tenant_id": "test-tenant", "timeout": 300}

        # Create config file
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_parser = configparser.ConfigParser()
        config_parser["DEFAULT"] = {k: str(v) for k, v in config_data.items()}
        with open(config_file, "w", encoding="utf-8") as f:
            config_parser.write(f)

        with patch("day2_cli.commands.config.CONFIG_PATH", config_file):
            # Get tenant-id
            result = runner.invoke(config, ["get", "tenant-id"])
            assert result.exit_code == 0
            assert "tenant-id = test-tenant" in result.output

            # Get timeout
            result = runner.invoke(config, ["get", "timeout"])
            assert result.exit_code == 0
            assert "timeout = 300" in result.output

    def test_config_get_default(self, runner, tmp_path):
        """Test the config get command with default values."""
        config_file = tmp_path / ".day2" / "config"

        with patch("day2_cli.commands.config.CONFIG_PATH", config_file):
            # Get base-url (not in config, should show default)
            result = runner.invoke(config, ["get", "base-url"])
            assert result.exit_code == 0
            assert (
                "base-url = https://api.montycloud.com/day2/api (default)"
                in result.output
            )

    def test_config_get_invalid_key(self, runner, tmp_path):
        """Test the config get command with an invalid key."""
        config_file = tmp_path / ".day2" / "config"

        with patch("day2_cli.commands.config.CONFIG_PATH", config_file):
            result = runner.invoke(config, ["get", "invalid-key"])
            assert result.exit_code == 0
            assert "Error: Unknown configuration key 'invalid-key'" in result.output
            assert "Available keys:" in result.output

    def test_config_list(self, runner, tmp_path):
        """Test the config list command."""
        config_file = tmp_path / ".day2" / "config"
        config_data = {"tenant_id": "test-tenant", "timeout": 300}

        # Create config file
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_parser = configparser.ConfigParser()
        config_parser["DEFAULT"] = {k: str(v) for k, v in config_data.items()}
        with open(config_file, "w", encoding="utf-8") as f:
            config_parser.write(f)

        with patch("day2_cli.commands.config.CONFIG_PATH", config_file):
            result = runner.invoke(config, ["list"])
            assert result.exit_code == 0
            assert "Configuration" in result.output
            assert "tenant-id" in result.output
            assert "test-tenant" in result.output
            assert "timeout" in result.output
            assert "300" in result.output
            assert "User config" in result.output
            assert "Default" in result.output  # For default values

    def test_config_reset(self, runner, tmp_path):
        """Test the config reset command."""
        config_file = tmp_path / ".day2" / "config"
        config_data = {"tenant_id": "test-tenant", "timeout": 300}

        # Create config file
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_parser = configparser.ConfigParser()
        config_parser["DEFAULT"] = {k: str(v) for k, v in config_data.items()}
        with open(config_file, "w", encoding="utf-8") as f:
            config_parser.write(f)

        with patch("day2_cli.commands.config.CONFIG_PATH", config_file):
            result = runner.invoke(config, ["reset"])
            assert result.exit_code == 0
            assert "Configuration reset to defaults" in result.output
            assert not config_file.exists()

    def test_config_reset_no_file(self, runner, tmp_path):
        """Test the config reset command when no config file exists."""
        config_file = tmp_path / ".day2" / "config"

        with patch("day2_cli.commands.config.CONFIG_PATH", config_file):
            result = runner.invoke(config, ["reset"])
            assert result.exit_code == 0
            assert "No configuration file found" in result.output

    def test_config_integration(self, runner, tmp_path):
        """Test that config commands are properly integrated with the CLI."""
        with patch(
            "day2_cli.commands.config.CONFIG_PATH", tmp_path / ".day2" / "config"
        ):
            # Test that config command group is available
            result = runner.invoke(cli, ["config", "--help"])
            assert result.exit_code == 0
            assert "Configuration commands" in result.output
            assert "set" in result.output
            assert "get" in result.output
            assert "list" in result.output
            assert "reset" in result.output
