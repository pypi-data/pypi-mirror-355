"""Tests for the TenantClient class."""

from unittest.mock import MagicMock, patch

import pytest

from day2.models.tenant import GetTenantOutput, ListAccountsOutput, ListTenantsOutput
from day2.resources.tenant import TenantClient
from day2.session import Session


@pytest.fixture
def mock_session():
    """Create a mock session for testing."""
    session = MagicMock(spec=Session)
    # Add required attributes for BaseClient
    session._config = MagicMock()
    session._config.api_url = "https://api.example.com"
    session._config.api_version = "v1"
    return session


def test_list_tenants(mock_session):
    """Test listing tenants."""
    # Mock response data
    mock_response = {
        "Tenants": [
            {
                "ID": "tenant-123",
                "Name": "Test Tenant",
                "Owner": "test@example.com",
                "Feature": "FULL",
                "CreatedBy": "admin@example.com",
                "CreatedAt": "2023-01-01T00:00:00Z",
                "ModifiedBy": "admin@example.com",
                "ModifiedAt": "2023-01-01T00:00:00Z",
            }
        ],
        "PageSize": 10,
        "TotalCount": 1,
        "NextPageToken": None,
    }

    # Set up the mock
    with patch.object(
        TenantClient, "_make_request", return_value=mock_response
    ) as mock_make_request:
        # Execute
        client = TenantClient(mock_session)
        result = client.list_tenants(page_size=10)

        # Verify
        mock_make_request.assert_called_once_with(
            "GET", "tenants", params={"PageSize": 10}
        )

    # Verify the result
    assert isinstance(result, ListTenantsOutput)
    assert len(result.tenants) == 1
    assert result.tenants[0].id == "tenant-123"
    assert result.tenants[0].name == "Test Tenant"
    assert result.next_page_token is None


def test_get_tenant(mock_session):
    """Test getting a tenant."""
    # Setup
    tenant_id = "tenant-123"
    mock_response = {
        "ID": "tenant-123",
        "Name": "Test Tenant",
        "Description": "Test description",
        "Owner": "test@example.com",
        "ParentTenantId": None,
        "Feature": "FULL",
        "CategoryId": None,
        "CreatedBy": "admin@example.com",
        "CreatedAt": "2023-01-01T00:00:00Z",
        "ModifiedBy": "admin@example.com",
        "ModifiedAt": "2023-01-01T00:00:00Z",
    }

    # Set up the mock
    with patch.object(
        TenantClient, "_make_request", return_value=mock_response
    ) as mock_make_request:
        # Execute
        client = TenantClient(mock_session)
        result = client.get_tenant(tenant_id)

        # Verify
        mock_make_request.assert_called_once_with("GET", f"tenants/{tenant_id}")

    # Verify the result
    assert isinstance(result, GetTenantOutput)
    assert result.id == "tenant-123"
    assert result.name == "Test Tenant"
    assert result.description == "Test description"


def test_list_accounts_by_tenant(mock_session):
    """Test listing accounts by tenant."""
    # Setup
    tenant_id = "tenant-123"
    mock_response = {
        "Accounts": [
            {
                "Number": "123456789",
                "Name": "Test Account",
                "Status": "CONNECTED",
                "Type": "MANAGEMENT",
                "PermissionModel": "Audit",
                "OnboardedDate": "2023-01-01",
            },
            {
                "Number": "987654321",
                "Name": "Another Account",
                "Status": "PENDING",
                "Type": "MEMBER",
                "PermissionModel": "Basic",
                "OnboardedDate": "2023-02-01",
            },
        ],
        "HasMore": False,
        "PageNumber": 1,
    }

    # Set up the mock
    with patch.object(
        TenantClient, "_make_request", return_value=mock_response
    ) as mock_make_request:
        # Execute
        client = TenantClient(mock_session)

        result = client.list_accounts(tenant_id=tenant_id)
        # Verify
        mock_make_request.assert_called_once_with(
            "GET",
            f"tenants/{tenant_id}/accounts",
            params={"PageSize": 10, "PageNumber": 1},
        )
    # Verify the result
    assert isinstance(result, ListAccountsOutput)
    assert len(result.accounts) == 2

    account1 = result.accounts[0]
    assert account1.number == "123456789"
    assert account1.name == "Test Account"
    assert account1.status == "CONNECTED"
    assert account1.type == "MANAGEMENT"
    assert account1.permission_model == "Audit"
    assert account1.onboarded_date == "2023-01-01"

    account2 = result.accounts[1]
    assert account2.number == "987654321"
    assert account2.name == "Another Account"
    assert account2.status == "PENDING"
    assert account2.type == "MEMBER"
    assert account2.permission_model == "Basic"
    assert account2.onboarded_date == "2023-02-01"


def test_list_accounts_by_tenant_with_params(mock_session):
    """Test listing accounts by tenant with pagination parameters."""
    # Setup
    tenant_id = "tenant-123"
    page_size = 5
    page_number = 1
    mock_response = {
        "Accounts": [
            {
                "Number": "123456789",
                "Name": "Test Account",
                "Status": "CONNECTED",
                "Type": "MANAGEMENT",
                "PermissionModel": "Audit",
                "OnboardedDate": "2023-01-01",
            },
            {
                "Number": "987654321",
                "Name": "Another Account",
                "Status": "PENDING",
                "Type": "MEMBER",
                "PermissionModel": "Basic",
                "OnboardedDate": "2023-02-01",
            },
        ],
        "HasMore": False,
        "PageNumber": page_number,
    }

    # Set up the mock
    with patch.object(
        TenantClient, "_make_request", return_value=mock_response
    ) as mock_make_request:
        # Execute
        client = TenantClient(mock_session)

        result = client.list_accounts(
            tenant_id=tenant_id, page_size=page_size, page_number=page_number
        )

        # Verify
        mock_make_request.assert_called_once_with(
            "GET",
            f"tenants/{tenant_id}/accounts",
            params={"PageSize": page_size, "PageNumber": page_number},
        )

    # Verify the result
    assert isinstance(result, ListAccountsOutput)
    assert len(result.accounts) == 2
    assert result.page_number == page_number
    assert result.has_more is False

    account1 = result.accounts[0]
    assert account1.number == "123456789"
    assert account1.name == "Test Account"
    assert account1.status == "CONNECTED"
    assert account1.type == "MANAGEMENT"
    assert account1.permission_model == "Audit"
    assert account1.onboarded_date == "2023-01-01"

    account2 = result.accounts[1]
    assert account2.number == "987654321"
    assert account2.name == "Another Account"
    assert account2.status == "PENDING"
    assert account2.type == "MEMBER"
    assert account2.permission_model == "Basic"
    assert account2.onboarded_date == "2023-02-01"
