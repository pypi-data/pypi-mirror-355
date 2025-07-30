"""Tests for the cost models."""

import pytest

from day2.models.cost import GetCostByChargeTypeOutput


def test_get_cost_by_charge_type_output_parse():
    """Test parsing a GetCostByChargeTypeOutput from a dictionary."""
    data = {
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

    cost_output = GetCostByChargeTypeOutput.model_validate(data)

    assert cost_output.total_cost == 1200.50
    assert cost_output.usage == 750.00
    assert cost_output.bundled_discount == 50.00
    assert cost_output.credit == 20.00
    assert cost_output.discount == 30.00
    assert cost_output.discounted_usage == 700.00
    assert cost_output.fee == 10.00
    assert cost_output.refund == 5.00
    assert cost_output.ri_fee == 15.00
    assert cost_output.tax == 25.00
    assert cost_output.savings_plan_upfront_fee == 100.00
    assert cost_output.savings_plan_recurring_fee == 50.00
    assert cost_output.savings_plan_covered_usage == 600.00
    assert cost_output.savings_plan_negation == 0.00
    assert cost_output.spp_discount == 10.00
    assert cost_output.distributor_discount == 5.00


def test_get_cost_by_charge_type_output_with_extra_fields():
    """Test parsing a GetCostByChargeTypeOutput with extra fields."""
    data = {
        "TotalCost": 1200.50,
        "Usage": 750.00,
        "BundledDiscount": 50.00,
        "ExtraFieldOne": "Extra Value 1",
        "ExtraFieldTwo": "Extra Value 2",
    }

    cost_output = GetCostByChargeTypeOutput.model_validate(data)

    # Verify known fields
    assert cost_output.total_cost == 1200.50
    assert cost_output.usage == 750.00
    assert cost_output.bundled_discount == 50.00

    # Verify dynamically handled extra fields
    assert hasattr(cost_output, "extra_field_one")
    assert cost_output.extra_field_one == "Extra Value 1"
    assert hasattr(cost_output, "extra_field_two")
    assert cost_output.extra_field_two == "Extra Value 2"


def test_get_cost_by_charge_type_output_no_extra_fields():
    """Test parsing a GetCostByChargeTypeOutput without extra fields."""
    data = {
        "TotalCost": 1000.00,
        "Usage": 500.00,
        "BundledDiscount": 25.00,
    }

    cost_output = GetCostByChargeTypeOutput.model_validate(data)

    # Verify known fields
    assert cost_output.total_cost == 1000.00
    assert cost_output.usage == 500.00
    assert cost_output.bundled_discount == 25.00

    # Verify no extra fields are present
    assert not hasattr(cost_output, "extra_field_one")
    assert not hasattr(cost_output, "extra_field_two")


def test_get_cost_by_charge_type_output_serialization():
    """Test serializing a GetCostByChargeTypeOutput with extra fields."""
    data = {
        "TotalCost": 1200.50,
        "Usage": 750.00,
        "ExtraField": "Extra Value",
    }

    cost_output = GetCostByChargeTypeOutput.model_validate(data)

    # Serialize to dictionary
    serialized_data = cost_output.model_dump(by_alias=True)

    # Verify known fields
    assert serialized_data["TotalCost"] == 1200.50
    assert serialized_data["Usage"] == 750.00

    # Verify extra fields are serialized in snake_case
    assert "extra_field" in serialized_data
    assert serialized_data["extra_field"] == "Extra Value"
