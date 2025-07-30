"""Tests for the CLI auth commands."""

import configparser
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from day2_cli.cli import cli
from day2_cli.commands.auth import auth, clear, configure, whoami


class TestAuthCommands:
    """Test suite for auth CLI commands."""

    @pytest.fixture
    def runner(self):
        """Create a CLI runner."""
        return CliRunner()

    def test_configure_new_api_key(self, runner, tmp_path):
        """Test the auth configure command with a new API key."""
        credentials_file = tmp_path / ".day2" / "credentials"

        with patch("day2_cli.commands.auth.Path.home", return_value=tmp_path):
            # Configure with API key
            result = runner.invoke(auth, ["configure", "--api-key", "test-api-key"])
            assert result.exit_code == 0
            assert "Authentication configured successfully" in result.output
            assert "API key saved to:" in result.output
            assert "Updated: API key" in result.output

            # Verify credentials file
            assert credentials_file.exists()
            config_parser = configparser.ConfigParser()
            config_parser.read(credentials_file)
            assert config_parser["DEFAULT"]["api_key"] == "test-api-key"

    def test_configure_update_api_key(self, runner, tmp_path):
        """Test the auth configure command updating an existing API key."""
        credentials_file = tmp_path / ".day2" / "credentials"

        # Create credentials file with existing API key
        credentials_file.parent.mkdir(parents=True, exist_ok=True)
        config_parser = configparser.ConfigParser()
        config_parser["DEFAULT"] = {"api_key": "existing-api-key"}
        with open(credentials_file, "w", encoding="utf-8") as f:
            config_parser.write(f)

        with patch("day2_cli.commands.auth.Path.home", return_value=tmp_path):
            # Update API key
            result = runner.invoke(auth, ["configure", "--api-key", "new-api-key"])
            assert result.exit_code == 0
            assert "Authentication configured successfully" in result.output
            assert "API key saved to:" in result.output

            # Verify credentials file
            config_parser = configparser.ConfigParser()
            config_parser.read(credentials_file)
            assert config_parser["DEFAULT"]["api_key"] == "new-api-key"

    def test_configure_with_api_secret_key(self, runner, tmp_path):
        """Test the auth configure command with API secret key."""
        credentials_file = tmp_path / ".day2" / "credentials"

        with patch("day2_cli.commands.auth.Path.home", return_value=tmp_path):
            # Configure with API key and API secret key
            result = runner.invoke(
                auth,
                [
                    "configure",
                    "--api-key",
                    "test-api-key",
                    "--api-secret-key",
                    "test-api-secret-key",
                ],
            )
            assert result.exit_code == 0
            assert "Authentication configured successfully" in result.output
            assert "API key saved to:" in result.output
            assert "API secret key saved to:" in result.output
            assert "Updated: API key, API secret key" in result.output

            # Verify credentials file
            config_parser = configparser.ConfigParser()
            config_parser.read(credentials_file)
            assert config_parser["DEFAULT"]["api_key"] == "test-api-key"
            assert config_parser["DEFAULT"]["api_secret_key"] == "test-api-secret-key"

    def test_configure_update_api_secret_key_only(self, runner, tmp_path):
        """Test the auth configure command updating only the API secret key."""
        credentials_file = tmp_path / ".day2" / "credentials"

        # Create credentials file with existing API key
        credentials_file.parent.mkdir(parents=True, exist_ok=True)
        config_parser = configparser.ConfigParser()
        config_parser["DEFAULT"] = {"api_key": "existing-api-key"}
        with open(credentials_file, "w", encoding="utf-8") as f:
            config_parser.write(f)

        with patch("day2_cli.commands.auth.Path.home", return_value=tmp_path):
            # Update only API secret key
            result = runner.invoke(
                auth, ["configure", "--api-secret-key", "new-api-secret-key"]
            )
            assert result.exit_code == 0
            assert "Authentication configured successfully" in result.output
            assert "API secret key saved to:" in result.output
            assert "Updated: API secret key" in result.output

            # Verify credentials file
            config_parser = configparser.ConfigParser()
            config_parser.read(credentials_file)
            assert config_parser["DEFAULT"]["api_key"] == "existing-api-key"
            assert config_parser["DEFAULT"]["api_secret_key"] == "new-api-secret-key"

    def test_configure_prompt_for_api_key(self, runner, tmp_path):
        """Test the auth configure command prompting for API key."""
        credentials_file = tmp_path / ".day2" / "credentials"

        with patch("day2_cli.commands.auth.Path.home", return_value=tmp_path):
            # Configure without providing API key (should prompt)
            result = runner.invoke(auth, ["configure"], input="prompted-api-key\n")
            assert result.exit_code == 0
            assert "Your MontyCloud Day2 API key" in result.output
            assert "Authentication configured successfully" in result.output
            assert "API key: prompted-api-key" in result.output
            assert "API key saved to:" in result.output

            # Verify credentials file
            config_parser = configparser.ConfigParser()
            config_parser.read(credentials_file)
            assert config_parser["DEFAULT"]["api_key"] == "prompted-api-key"

    def test_whoami_authenticated(self, runner, tmp_path):
        """Test the auth whoami command when authenticated."""
        mock_session = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.api_key = "test-api-key-1234"
        mock_credentials.secret_key = "test-api-secret-key-5678"
        mock_session.credentials = mock_credentials

        with patch("day2_cli.commands.auth.Session", return_value=mock_session):
            result = runner.invoke(auth, ["whoami"])
            assert result.exit_code == 0
            assert "Authenticated successfully" in result.output
            assert "Using API key: ********1234" in result.output
            assert "Using API secret key: ********************5678" in result.output

    def test_whoami_not_authenticated(self, runner, tmp_path):
        """Test the auth whoami command when not authenticated."""
        with patch(
            "day2_cli.commands.auth.Session", side_effect=ValueError("No API key found")
        ):
            result = runner.invoke(auth, ["whoami"])
            assert result.exit_code == 0
            assert "Authentication error: No API key found" in result.output

    def test_clear_confirmed(self, runner, tmp_path):
        """Test the auth clear command with confirmation."""
        credentials_file = tmp_path / ".day2" / "credentials"

        # Create credentials file
        credentials_file.parent.mkdir(parents=True, exist_ok=True)
        credentials_file.touch()

        with patch("day2_cli.commands.auth.Path.home", return_value=tmp_path):
            # Clear credentials with confirmation
            result = runner.invoke(auth, ["clear"], input="y\n")
            assert result.exit_code == 0
            assert "Are you sure" in result.output
            assert "Credentials cleared successfully" in result.output
            assert not credentials_file.exists()

    def test_clear_cancelled(self, runner, tmp_path):
        """Test the auth clear command when cancelled."""
        credentials_file = tmp_path / ".day2" / "credentials"

        # Create credentials file
        credentials_file.parent.mkdir(parents=True, exist_ok=True)
        credentials_file.touch()

        with patch("day2_cli.commands.auth.Path.home", return_value=tmp_path):
            # Clear credentials but cancel
            result = runner.invoke(auth, ["clear"], input="n\n")
            # Click returns exit code 1 when confirmation is aborted
            assert result.exit_code == 1
            assert "Are you sure" in result.output
            assert "Aborted" in result.output
            assert credentials_file.exists()

    def test_auth_integration(self, runner, tmp_path):
        """Test that auth commands are properly integrated with the CLI."""
        # Test that auth command group is available
        result = runner.invoke(cli, ["auth", "--help"])
        assert result.exit_code == 0
        assert "Authentication commands" in result.output
        assert "configure" in result.output
        assert "whoami" in result.output
        assert "clear" in result.output
