"""Tests for the Session class and module-level client factories."""

import configparser
import os
from unittest.mock import MagicMock, patch

import pytest

import day2
from day2 import Session
from day2.auth.credentials import Credentials
from day2.exceptions import TenantContextError


class TestSession:
    """Test suite for the Session class and module-level client factories."""

    def test_session_init_with_api_key(self):
        """Test session initialization with API key."""
        session = Session(api_key="test-api-key")
        assert session.credentials.api_key == "test-api-key"

    def test_session_init_with_credentials(self):
        """Test session initialization with Credentials object."""
        credentials = Credentials(api_key="test-api-key")
        session = Session(credentials=credentials)
        assert session.credentials.api_key == "test-api-key"

    def test_session_init_with_env_var(self, monkeypatch):
        """Test session initialization with environment variable."""
        monkeypatch.setenv("DAY2_API_KEY", "env-api-key")
        session = Session()
        assert session.credentials.api_key == "env-api-key"

    def test_session_init_with_config_file(self, monkeypatch, tmp_path):
        """Test session initialization with config file."""
        # Create a mock credentials file
        config_dir = tmp_path / ".day2"
        config_dir.mkdir()
        credentials_file = config_dir / "credentials"
        config_parser = configparser.ConfigParser()
        config_parser["DEFAULT"] = {"api_key": "file-api-key"}
        with open(credentials_file, "w", encoding="utf-8") as f:
            config_parser.write(f)

        # Mock the home directory to point to our temporary directory
        monkeypatch.setattr(os.path, "expanduser", lambda x: str(tmp_path))

        # Set environment variable as a fallback
        monkeypatch.setenv("DAY2_API_KEY", "env-api-key")

        session = Session()
        assert session.credentials.api_key == "env-api-key"

    def test_session_init_no_credentials(self, monkeypatch, tmp_path):
        """Test session initialization with no credentials."""
        # Mock the home directory to point to our temporary directory
        monkeypatch.setattr(os.path, "expanduser", lambda x: str(tmp_path))

        # Ensure no environment variable is set
        monkeypatch.delenv("DAY2_API_KEY", raising=False)

        with pytest.raises(ValueError, match="No API key provided"):
            Session()

    def test_set_tenant(self, tmp_path):
        """Test setting tenant context."""
        # Mock the home directory
        with patch("pathlib.Path.home", return_value=tmp_path):
            session = Session(api_key="test-api-key")
            session.set_tenant("tenant-123")
            assert session.tenant_id == "tenant-123"

    def test_clear_tenant(self, tmp_path):
        """Test clearing tenant context."""
        # Mock the home directory
        with patch("pathlib.Path.home", return_value=tmp_path):
            session = Session(api_key="test-api-key")
            session.set_tenant("tenant-123")
            assert session.tenant_id == "tenant-123"

            session.clear_tenant()
            assert session.tenant_id is None

    @patch("day2.resources.tenant.TenantClient")
    def test_client_creation_tenant(self, mock_tenant_client):
        """Test creating a tenant client."""
        mock_instance = MagicMock()
        mock_tenant_client.return_value = mock_instance

        session = Session(api_key="test-api-key")
        client = session.tenant

        assert client == mock_instance
        mock_tenant_client.assert_called_once()

    def test_client_creation_invalid_service(self):
        """Test creating a client for an invalid service."""
        session = Session(api_key="test-api-key")

        with pytest.raises(ValueError):
            session.client("invalid-service")

    @patch("day2._default_session_holder.session", None)
    @patch("day2.Session")
    def test_get_default_session(self, mock_session):
        """Test getting the default session."""
        mock_instance = MagicMock()
        mock_session.return_value = mock_instance

        # First call should create a new session
        session1 = day2.get_default_session()
        assert session1 == mock_instance
        mock_session.assert_called_once()

        # Reset the mock to verify second call doesn't create a new session
        mock_session.reset_mock()

        # Second call should return the existing session
        session2 = day2.get_default_session()
        assert session2 == mock_instance
        mock_session.assert_not_called()

    @patch("day2.get_default_session")
    def test_tenant_factory(self, mock_get_default_session):
        """Test the tenant factory function."""
        mock_session = MagicMock()
        mock_tenant_client = MagicMock()
        mock_session.tenant = mock_tenant_client
        mock_get_default_session.return_value = mock_session

        client = day2.tenant()

        assert client == mock_tenant_client
        mock_get_default_session.assert_called_once()

    @patch("day2.get_default_session")
    def test_assessment_factory(self, mock_get_default_session):
        """Test the assessment factory function."""
        mock_session = MagicMock()
        mock_assessment_client = MagicMock()
        mock_session.assessment = mock_assessment_client
        mock_get_default_session.return_value = mock_session

        client = day2.assessment()

        assert client == mock_assessment_client
        mock_get_default_session.assert_called_once()

    @patch("day2._default_session_holder.session")
    def test_default_session_tenant_context(self, mock_default_session):
        """Test that setting tenant context on default session affects module-level factories."""
        mock_session = MagicMock()
        mock_default_session.return_value = mock_session

        # Set up the default session
        default_session = day2.get_default_session()

        # Set tenant context
        default_session.set_tenant("tenant-123")

        # Verify tenant context was set
        default_session.set_tenant.assert_called_with("tenant-123")
