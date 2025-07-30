"""CLI commands for the MontyCloud DAY2 CLI."""

from day2_cli.commands.assessment import assessment
from day2_cli.commands.auth import auth
from day2_cli.commands.tenant import tenant

__all__ = ["auth", "tenant", "assessment"]
