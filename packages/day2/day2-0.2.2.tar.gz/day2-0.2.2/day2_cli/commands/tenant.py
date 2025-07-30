"""Tenant commands for the MontyCloud DAY2 CLI."""

import json
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from day2 import Session
from day2.exceptions import Day2Error
from day2_cli.utils.formatters import format_error
from day2_cli.utils.output_formatter import format_item_output, format_list_output

# Table is used by the output_formatter module


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
        # Try to load from config file directly
        config_dir = Path.home() / ".day2"
        config_file = config_dir / "config"
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    tenant_id = config.get("tenant_id")
            except (json.JSONDecodeError, IOError):
                pass

    if not tenant_id:
        console.print(
            "[red]Error: No tenant ID provided and no default tenant configured.[/red]"
        )
        console.print(
            "[yellow]Tip: Configure a default tenant with 'day2 auth configure --tenant-id YOUR_TENANT_ID'[/yellow]"
        )
        return None

    return tenant_id


@click.group()
def tenant() -> None:
    """Tenant commands."""


@tenant.command("list")
@click.option("--page-token", type=str, default=None, help="Page token for pagination")
@click.option("--page-size", type=int, default=10, help="Page size")
@click.option(
    "--output",
    type=click.Choice(["table", "json"], case_sensitive=False),
    help="Output format (table or json)",
)
def list_tenants(page_token: str, page_size: int, output: Optional[str] = None) -> None:
    """List tenants.

    This command lists tenants that the user has access to.
    """
    try:
        # Get output format from context if set via global option
        ctx = click.get_current_context()
        ctx_output = ctx.obj.get("output_format") if ctx.obj else None
        output_format = output or ctx_output

        session = Session()
        result = session.tenant.list_tenants(page_size=page_size, page_token=page_token)

        if not result.tenants:
            console.print("[yellow]No tenants found.[/yellow]")
            return

        # Convert tenant objects to dictionaries for output
        tenant_list = []
        for tenant_item in result.tenants:
            tenant_dict = {
                "id": tenant_item.id,
                "name": tenant_item.name,
                "owner": tenant_item.owner or "N/A",
                "feature": tenant_item.feature,
                "created_by": tenant_item.created_by,
            }
            tenant_list.append(tenant_dict)

        # Define columns for table output
        columns = {
            "id": "ID",
            "name": "Name",
            "owner": "Owner",
            "feature": "Feature",
            "created_by": "Created By",
        }

        # Format and output the tenant list
        format_list_output(tenant_list, "Tenants", columns, output_format)

        if result.next_page_token:
            console.print(
                f"[yellow]More results available. Use --page-token={result.next_page_token} to get the next page.[/yellow]"
            )

    except Day2Error as e:
        console.print(format_error(e))


@tenant.command("get")
@click.argument("tenant-id", required=False)
@click.option(
    "--output",
    type=click.Choice(["table", "json"], case_sensitive=False),
    help="Output format (table or json)",
)
def get_tenant(tenant_id: Optional[str] = None, output: Optional[str] = None) -> None:
    """Get details of a specific tenant.

    TENANT-ID: ID of the tenant to get details for. If not provided, uses the default tenant configured with 'auth configure'.
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

        result = session.tenant.get_tenant(tenant_id)

        # Convert tenant object to dictionary for output
        tenant_dict = {
            "id": result.id,
            "name": result.name,
            "description": result.description or "N/A",
            "owner": result.owner or "N/A",
            "parent_tenant_id": result.parent_tenant_id or "N/A",
            "feature": result.feature,
            "category_id": result.category_id or "N/A",
            "created_by": result.created_by,
            "created_at": str(result.created_at),
            "modified_by": result.modified_by or "N/A",
            "modified_at": str(result.modified_at),
        }

        # Format and output the tenant details
        format_item_output(tenant_dict, f"Tenant: {result.name}", output_format)

    except Day2Error as e:
        console.print(format_error(e))


@tenant.command("list-accounts")
@click.argument("tenant-id", required=False)
@click.option("--page-size", type=int, default=10, help="Page size, Default is 10")
@click.option(
    "--page-number",
    type=int,
    default=1,
    help="Page number for pagination, Default is 1",
)
@click.option(
    "--output",
    type=click.Choice(["table", "json"], case_sensitive=False),
    help="Output format (table or json)",
)
def list_accounts(
    tenant_id: Optional[str] = None,
    page_size: int = 10,
    page_number: int = 1,
    output: Optional[str] = None,
) -> None:
    """List accounts for a specific tenant.

    TENANT-ID: ID of the tenant to list accounts for. If not provided, uses the default tenant configured with 'auth configure'.
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

        result = session.tenant.list_accounts(
            tenant_id=tenant_id, page_size=page_size, page_number=page_number
        )

        if not result.accounts:
            console.print(
                "[yellow]No accounts found for the specified tenant.[/yellow]"
            )
            return

        # Convert account objects to dictionaries for output
        account_list = []
        for account_item in result.accounts:
            account_dict = {
                "number": account_item.number,
                "name": account_item.name,
                "status": account_item.status,
                "type": account_item.type,
                "permission_model": account_item.permission_model,
                "onboarded_date": account_item.onboarded_date,
            }
            account_list.append(account_dict)

        # Define columns for table output
        columns = {
            "number": "Number",
            "name": "Name",
            "status": "Status",
            "type": "Type",
            "permission_model": "Permission Model",
            "onboarded_date": "Onboarded Date",
        }

        # Format and output the account list
        format_list_output(account_list, "Accounts", columns, output_format)

        # Check if there are more accounts
        if result.has_more:
            console.print(
                f"[yellow]More results available. Use --page-number={result.page_number + 1} to get the next page.[/yellow]"
            )

    except Day2Error as e:
        console.print(format_error(e))
