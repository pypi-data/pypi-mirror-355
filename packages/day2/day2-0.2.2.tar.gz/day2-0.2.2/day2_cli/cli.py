"""Main CLI entry point for the MontyCloud DAY2 CLI."""

import sys
from typing import Optional

import click
from rich.console import Console

from day2 import __version__
from day2_cli.commands.assessment import assessment

# Import from day2 package
# Import from day2_cli package
from day2_cli.commands.auth import auth
from day2_cli.commands.config import config
from day2_cli.commands.cost import cost
from day2_cli.commands.tenant import tenant
from day2_cli.utils.formatters import format_error

console = Console()


@click.group()
@click.version_option(package_name="day2")
@click.option(
    "--output",
    type=click.Choice(["table", "json"], case_sensitive=False),
    help="Output format (table or json)",
)
def cli(output: Optional[str] = None) -> None:
    """DAY2 CLI.

    A command-line interface for interacting with the MontyCloud DAY2 API.
    """
    # Store output format in click context for use by subcommands
    if output:
        click.get_current_context().obj = {"output_format": output.lower()}


# Add command groups
cli.add_command(auth)
cli.add_command(config)
cli.add_command(tenant)
cli.add_command(assessment)
cli.add_command(cost)


def main() -> None:
    """Main entry point for the CLI."""
    try:
        cli()
    except (ValueError, KeyError, RuntimeError, IOError) as e:
        console.print(format_error(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
