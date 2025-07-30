"""Tests for the CostClient class."""

from unittest.mock import MagicMock, patch

import pytest

from day2.models.cost import GetCostByChargeTypeOutput
from day2.resources.cost import CostClient
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


def test_get_cost_by_charge_type(mock_session):
    """Test fetching cost breakdown by charge type."""
    # Setup
    tenant_id = "tenant-123"
    cloud_provider = "AWS"
    start_date = "2025-04-01"
    end_date = "2025-05-30"
    mock_response = {
        "TotalCost": 1200.50,
        "Usage": 750.00,
        "BundledDiscount": 50.00,
        "Credit": 20.00,
        "Discount": 30.00,
        "DiscountedUsage": 700.00,
        "Fee": 10.00,
        "Refund": 5.00,
        "RIFee": 15.00,
        "Tax": 25.00,
        "SavingsPlanUpfrontFee": 100.00,
        "SavingsPlanRecurringFee": 50.00,
        "SavingsPlanCoveredUsage": 600.00,
        "SavingsPlanNegation": 0.00,
        "SPPDiscount": 10.00,
        "DistributorDiscount": 5.00,
    }

    # Set up the mock
    with patch.object(
        CostClient, "_make_request", return_value=mock_response
    ) as mock_make_request:
        # Execute
        client = CostClient(mock_session)
        result = client.get_cost_by_charge_type(
            tenant_id=tenant_id,
            cloud_provider=cloud_provider,
            start_date=start_date,
            end_date=end_date,
        )

        # Verify the request
        mock_make_request.assert_called_once_with(
            "GET",
            "tenants/tenant-123/cost/cost-by-charge-type",
            params={
                "CloudProvider": cloud_provider,
                "StartDate": start_date,
                "EndDate": end_date,
            },
        )

    # Verify the result
    assert isinstance(result, GetCostByChargeTypeOutput)
    assert result.total_cost == 1200.50
    assert result.usage == 750.00
    assert result.bundled_discount == 50.00
    assert result.credit == 20.00
    assert result.discount == 30.00
    assert result.discounted_usage == 700.00
    assert result.fee == 10.00
    assert result.refund == 5.00
    assert result.ri_fee == 15.00
    assert result.tax == 25.00
    assert result.savings_plan_upfront_fee == 100.00
    assert result.savings_plan_recurring_fee == 50.00
    assert result.savings_plan_covered_usage == 600.00
    assert result.savings_plan_negation == 0.00
    assert result.spp_discount == 10.00
    assert result.distributor_discount == 5.00
