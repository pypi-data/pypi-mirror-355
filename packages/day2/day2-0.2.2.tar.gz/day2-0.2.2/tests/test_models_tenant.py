"""Tests for the tenant models."""

from day2.models.tenant import (
    Account,
    ListAccountsOutput,
    ListTenantsOutput,
    TenantDetails,
)


def test_tenant_details_parse():
    """Test parsing a TenantDetails from a dictionary."""
    data = {
        "ID": "tenant-123",
        "Name": "Test Tenant",
        "Description": "Test description",
        "Owner": "test@example.com",
        "Feature": "FULL",
        "CreatedBy": "admin@example.com",
        "CreatedAt": "2023-01-01T00:00:00Z",
        "ModifiedBy": "admin@example.com",
        "ModifiedAt": "2023-01-01T00:00:00Z",
    }

    tenant = TenantDetails.model_validate(data)

    assert tenant.id == "tenant-123"
    assert tenant.name == "Test Tenant"
    assert tenant.description == "Test description"
    assert tenant.owner == "test@example.com"
    assert tenant.feature == "FULL"
    assert tenant.created_by == "admin@example.com"
    assert tenant.modified_by == "admin@example.com"


def test_list_tenants_output_parse():
    """Test parsing a ListTenantsOutput from a dictionary."""
    data = {
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
        "NextPageToken": None,
    }

    list_output = ListTenantsOutput.model_validate(data)

    assert len(list_output.tenants) == 1
    assert list_output.next_page_token is None

    tenant = list_output.tenants[0]
    assert tenant.id == "tenant-123"
    assert tenant.name == "Test Tenant"
    assert tenant.owner == "test@example.com"
    assert tenant.feature == "FULL"


def test_get_tenant_output_parse():
    """Test parsing a GetTenantOutput from a dictionary."""
    data = {
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

    output = TenantDetails.model_validate(data)

    assert output.id == "tenant-123"
    assert output.name == "Test Tenant"
    assert output.description == "Test description"
    assert output.owner == "test@example.com"
    assert output.parent_tenant_id is None
    assert output.feature == "FULL"
    assert output.category_id is None
    assert output.created_by == "admin@example.com"
    assert output.modified_by == "admin@example.com"


def test_list_accounts_by_tenant_output_parse():
    """Test parsing a ListAccountsOutput from a dictionary."""
    data = {
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
        "PageNumber": 1,
        "HasMore": False,
    }

    output = ListAccountsOutput.model_validate(data)

    assert len(output.accounts) == 2

    account1 = output.accounts[0]
    assert account1.number == "123456789"
    assert account1.name == "Test Account"
    assert account1.status == "CONNECTED"
    assert account1.type == "MANAGEMENT"
    assert account1.permission_model == "Audit"
    assert account1.onboarded_date == "2023-01-01"

    account2 = output.accounts[1]
    assert account2.number == "987654321"
    assert account2.name == "Another Account"
    assert account2.status == "PENDING"
    assert account2.type == "MEMBER"
    assert account2.permission_model == "Basic"
    assert account2.onboarded_date == "2023-02-01"

    assert output.has_more is False
    assert output.page_number == 1


def test_details_parse():
    """Test parsing an Account object from a dictionary."""
    data = {
        "Number": "123456789",
        "Name": "Test Account",
        "Status": "CONNECTED",
        "Type": "MANAGEMENT",
        "PermissionModel": "Audit",
        "OnboardedDate": "2023-01-01",
    }

    account = Account.model_validate(data)

    assert account.number == "123456789"
    assert account.name == "Test Account"
    assert account.status == "CONNECTED"
    assert account.type == "MANAGEMENT"
    assert account.permission_model == "Audit"
    assert account.onboarded_date == "2023-01-01"
