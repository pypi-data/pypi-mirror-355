"""Cost commands for the MontyCloud DAY2 CLI."""

from typing import Optional

import click
from rich.console import Console

from day2 import Session
from day2.exceptions import Day2Error
from day2_cli.utils.formatters import format_error
from day2_cli.utils.output_formatter import format_item_output

console = Console()


def get_tenant_id(session: Session, tenant_id: Optional[str]) -> Optional[str]:
    """Get the tenant ID from the provided value or session default.

    Args:
        session: The session object
        tenant_id: The provided tenant ID or None

    Returns:
        The tenant ID to use or None if not available
    """
    if tenant_id:
        return tenant_id

    tenant_id = session.tenant_id
    if not tenant_id:
        console.print(
            "[red]Error: No tenant ID provided and no default tenant configured.[/red]"
        )
        console.print(
            "[yellow]Tip: Configure a default tenant with 'day2 config set tenant-id YOUR_TENANT_ID'[/yellow]"
        )
        return None

    return tenant_id


@click.group()
def cost() -> None:
    """Cost commands."""


@cost.command("get-cost-by-charge-type")
@click.option("--tenant-id", help="ID of the tenant to fetch cost data for")
@click.option(
    "--cloud-provider",
    type=str,
    default="AWS",
    help="Cloud provider (e.g., AWS, Azure). Default is AWS.",
)
@click.option(
    "--start-date",
    type=str,
    required=True,
    help="Start date in YYYY-MM-DD format.",
)
@click.option(
    "--end-date",
    type=str,
    required=True,
    help="End date in YYYY-MM-DD format.",
)
@click.option(
    "--output",
    type=click.Choice(["table", "json"], case_sensitive=False),
    help="Output format (table or json)",
)
def get_cost_by_charge_type(
    tenant_id: Optional[str],
    cloud_provider: str,
    start_date: str,
    end_date: str,
    output: Optional[str] = None,
) -> None:
    """Get cost breakdown by charge type for a tenant.

    TENANT-ID: The ID of the tenant to fetch cost data for.
    """
    try:
        # Get output format from context if set via global option
        ctx = click.get_current_context()
        ctx_output = ctx.obj.get("output_format") if ctx.obj else None
        output_format = output or ctx_output

        session = Session()
        # Get tenant ID from provided value or session default
        tenant_id = get_tenant_id(session, tenant_id)
        if not tenant_id:
            return

        # Fetch cost data
        result = session.cost.get_cost_by_charge_type(
            tenant_id=tenant_id,
            cloud_provider=cloud_provider,
            start_date=start_date,
            end_date=end_date,
        )

        # Convert cost data to dictionary for output
        cost_dict = {
            "total_cost": result.total_cost,
            "usage": result.usage,
            "bundled_discount": result.bundled_discount,
            "credit": result.credit,
            "discount": result.discount,
            "discounted_usage": result.discounted_usage,
            "fee": result.fee,
            "refund": result.refund,
            "ri_fee": result.ri_fee,
            "tax": result.tax,
            "savings_plan_upfront_fee": result.savings_plan_upfront_fee,
            "savings_plan_recurring_fee": result.savings_plan_recurring_fee,
            "savings_plan_covered_usage": result.savings_plan_covered_usage,
            "savings_plan_negation": result.savings_plan_negation,
            "spp_discount": result.spp_discount,
            "distributor_discount": result.distributor_discount,
        }

        # Format and output the cost data
        format_item_output(
            cost_dict, f"Cost Breakdown for Tenant: {tenant_id}", output_format
        )

    except Day2Error as e:
        console.print(format_error(e))
