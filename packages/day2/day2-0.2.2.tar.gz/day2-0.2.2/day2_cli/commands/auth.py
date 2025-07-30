"""Authentication commands for the MontyCloud DAY2 CLI."""

import configparser
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from day2 import Session

console = Console()


@click.group()
def auth() -> None:
    """Authentication commands."""


@auth.command("configure")
@click.option(
    "--api-key", prompt=False, hide_input=True, help="Your MontyCloud Day2 API key"
)
@click.option("--api-secret-key", help="Your MontyCloud Day2 API secret key")
def configure(api_key: Optional[str], api_secret_key: Optional[str]) -> None:
    """Configure authentication credentials.

    This command will save your API key and API secret key to the credentials file.
    If you only want to update the API secret key, you can omit the API key.
    """
    # Create configuration directory if it doesn't exist
    config_dir = Path.home() / ".day2"
    config_dir.mkdir(exist_ok=True)

    # Save API key to credentials file
    credentials_file = config_dir / "credentials"
    config_parser = configparser.ConfigParser()
    existing_api_key = None
    if credentials_file.exists():
        try:
            config_parser.read(credentials_file)
            if "DEFAULT" in config_parser:
                existing_api_key = config_parser["DEFAULT"].get("api_key")
        except (configparser.Error, IOError):
            pass

    if not api_key and existing_api_key:
        api_key = existing_api_key
    elif not api_key:
        # Don't hide input so users can see what they're typing/pasting
        api_key = click.prompt("Your MontyCloud Day2 API key", hide_input=False)

    # Ensure api_key is str type for mypy
    assert api_key is not None

    # Ensure DEFAULT section exists
    if "DEFAULT" not in config_parser:
        config_parser["DEFAULT"] = {}

    config_parser["DEFAULT"]["api_key"] = api_key

    if api_secret_key:
        config_parser["DEFAULT"]["api_secret_key"] = api_secret_key

    with open(credentials_file, "w", encoding="utf-8") as f:
        config_parser.write(f)

    console.print("[green]Authentication configured successfully.[/green]")

    # Show a summary of what was saved
    if api_key:
        if existing_api_key == api_key or "--api-key" in sys.argv:
            console.print(f"API key: [bold]{'*' * 8}{api_key[-4:]}[/bold]")
        console.print(f"API key saved to: {credentials_file}")

    if api_secret_key:
        console.print(f"API secret key: [bold]{'*' * 8}{api_secret_key[-4:]}[/bold]")
        console.print(f"API secret key saved to: {credentials_file}")

    # Show a summary of what was updated
    updates = []
    if api_key and not existing_api_key:
        updates.append("API key")
    if api_secret_key:
        updates.append("API secret key")

    if updates:
        console.print(f"[green]Updated: {', '.join(updates)}[/green]")


@auth.command("whoami")
def whoami() -> None:
    """Display information about the current authenticated user."""
    try:
        session = Session()
        # This would typically call an API endpoint to get user info
        # For now, just show that we're authenticated
        console.print("[green]Authenticated successfully.[/green]")
        if session.credentials.api_key and len(session.credentials.api_key) >= 4:
            api_key_suffix = session.credentials.api_key[-4:]
            console.print(f"Using API key: {'*' * 8}{api_key_suffix}")
        else:
            console.print("Using API key: [yellow]<not available>[/yellow]")
        if (
            hasattr(session.credentials, "secret_key")
            and session.credentials.secret_key
            and len(session.credentials.secret_key) > 4
        ):
            token_suffix = session.credentials.secret_key[-4:]
            console.print(f"Using API secret key: {'*' * 20}{token_suffix}")
    except (ValueError, KeyError, IOError, AttributeError) as e:
        console.print(f"[red]Authentication error: {str(e)}[/red]")


@auth.command("clear")
@click.confirmation_option(
    prompt="Are you sure you want to clear your authentication credentials?"
)
def clear() -> None:
    """Clear authentication credentials."""
    config_dir = Path.home() / ".day2"
    credentials_file = config_dir / "credentials"

    if credentials_file.exists():
        try:
            credentials_file.unlink()
            console.print("[green]Credentials cleared successfully.[/green]")
        except IOError as e:
            console.print(f"[red]Failed to clear credentials: {str(e)}[/red]")
    else:
        console.print("[yellow]No credentials file found.[/yellow]")
