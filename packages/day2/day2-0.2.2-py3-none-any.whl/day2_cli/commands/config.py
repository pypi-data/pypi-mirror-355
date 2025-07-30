"""Configuration commands for the MontyCloud DAY2 CLI."""

import configparser
import json
from pathlib import Path
from typing import Any, Dict, Optional

import click
from rich.console import Console
from rich.table import Table

from day2.client.config import Config

console = Console()

# Configuration file path
CONFIG_PATH = Path.home() / ".day2" / "config"


def ensure_config_dir() -> None:
    """Ensure the config directory exists."""
    config_dir = CONFIG_PATH.parent
    config_dir.mkdir(parents=True, exist_ok=True)


def load_config() -> Dict[str, Any]:
    """Load configuration from file.

    Returns:
        Dict[str, Any]: Configuration data
    """
    if not CONFIG_PATH.exists():
        return {}

    try:
        config_parser = configparser.ConfigParser()
        config_parser.read(CONFIG_PATH)

        # Get values from DEFAULT section
        if "DEFAULT" in config_parser:
            return dict(config_parser["DEFAULT"])
        return {}
    except (configparser.Error, IOError):
        console.print("[yellow]Warning: Could not read configuration file.[/yellow]")
        return {}


def save_config(config_data: Dict[str, Any]) -> None:
    """Save configuration to file.

    Args:
        config_data (Dict[str, Any]): Configuration data to save
    """
    ensure_config_dir()

    try:
        config_parser = configparser.ConfigParser()

        # Load existing config if it exists
        if CONFIG_PATH.exists():
            config_parser.read(CONFIG_PATH)

        # Ensure DEFAULT section exists
        if "DEFAULT" not in config_parser:
            config_parser["DEFAULT"] = {}

        # Update config with new data
        for key, value in config_data.items():
            config_parser["DEFAULT"][key] = str(value)

        # Write to file
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            config_parser.write(f)
    except IOError:
        console.print("[red]Error: Could not save configuration file.[/red]")


@click.group()
def config() -> None:
    """Configuration commands."""


@config.command("set")
@click.argument("key")
@click.argument("value")
def set_config(key: str, value: str) -> None:
    """Set a configuration value.

    KEY: Name of the configuration option to set.
    VALUE: Value to set for the configuration option.

    Available keys:
      tenant-id: Default tenant ID
      base-url: Base URL for the API
      api-version: API version
      timeout: Request timeout in seconds
      max-retries: Maximum number of retries
      output-format: Output format (table or json)
    """
    # Convert CLI key names to config keys
    key_mapping = {
        "tenant-id": "tenant_id",
        "base-url": "base_url",
        "api-version": "api_version",
        "timeout": "timeout",
        "max-retries": "max_retries",
        "retry-backoff": "retry_backoff_factor",
        "output-format": "output_format",
    }

    if key not in key_mapping:
        console.print(f"[red]Error: Unknown configuration key '{key}'.[/red]")
        console.print(
            "[yellow]Available keys: tenant-id, base-url, api-version, timeout, max-retries, retry-backoff, output-format[/yellow]"
        )
        return

    config_key = key_mapping[key]
    config_data = load_config()

    # Convert value to the appropriate type
    if config_key in ["timeout", "max_retries"]:
        try:
            config_data[config_key] = int(value)
        except ValueError:
            console.print(f"[red]Error: '{key}' must be an integer.[/red]")
            return
    elif config_key in ["retry_backoff_factor"]:
        try:
            config_data[config_key] = float(value)
        except ValueError:
            console.print(f"[red]Error: '{key}' must be a number.[/red]")
            return
    elif config_key == "output_format":
        if value.lower() not in ["table", "json"]:
            console.print(f"[red]Error: '{key}' must be 'table' or 'json'.[/red]")
            return
        config_data[config_key] = value.lower()
    else:
        config_data[config_key] = value

    save_config(config_data)
    console.print(f"[green]Configuration '{key}' set to '{value}'.[/green]")


@config.command("get")
@click.argument("key", required=False)
@click.option(
    "--output",
    type=click.Choice(["table", "json"], case_sensitive=False),
    help="Output format (table or json)",
)
def get_config(key: Optional[str] = None, output: Optional[str] = None) -> None:
    """Get a configuration value.

    KEY: Name of the configuration option to get. If not provided, lists all configuration values.
    """
    # Convert CLI key names to config keys
    key_mapping = {
        "tenant-id": "tenant_id",
        "base-url": "base_url",
        "api-version": "api_version",
        "timeout": "timeout",
        "max-retries": "max_retries",
        "retry-backoff": "retry_backoff_factor",
        "output-format": "output_format",
    }

    # Get output format from context if set via global option
    ctx = click.get_current_context()
    ctx_output = ctx.obj.get("output_format") if ctx.obj else None

    # Load the config data
    config_data = load_config()

    # Check for output format in this order:
    # 1. Explicitly provided via --output option
    # 2. Set in the context (via global --output option)
    # 3. Set in the config file
    # 4. Default from Config class
    config_output = config_data.get("output_format")
    output_format = output or ctx_output or config_output or Config().output_format

    if not key:
        # If no key provided, show all configuration
        list_config(output=output_format)
        return

    if key not in key_mapping:
        error_msg = f"Error: Unknown configuration key '{key}'."
        available_keys = "Available keys: tenant-id, base-url, api-version, timeout, max-retries, retry-backoff, output-format"

        if output_format.lower() == "json":
            error_data = {
                "error": error_msg,
                "available_keys": available_keys.split(": ")[1].split(", "),
            }
            console.print(json.dumps(error_data, indent=2))
        else:
            console.print(f"[red]{error_msg}[/red]")
            console.print(f"[yellow]{available_keys}[/yellow]")
        return

    config_key = key_mapping[key]
    value = config_data.get(config_key)
    is_default = False

    if value is None:
        # Get default value from Config class
        default_config = Config()
        value = getattr(default_config, config_key, None)
        is_default = True

    if output_format.lower() == "json":
        result = {"key": key, "value": value, "is_default": is_default}
        console.print(json.dumps(result, indent=2))
    else:
        if is_default:
            console.print(f"{key} = {value} [yellow](default)[/yellow]")
        else:
            console.print(f"{key} = {value}")


@config.command("list")
@click.option(
    "--output",
    type=click.Choice(["table", "json"], case_sensitive=False),
    help="Output format (table or json)",
)
def list_config(output: Optional[str] = None) -> None:
    """List all configuration values."""
    # Get output format from context if set via global option
    ctx = click.get_current_context()
    ctx_output = ctx.obj.get("output_format") if ctx.obj else None

    # Load the config data
    config_data = load_config()

    # Check for output format in this order:
    # 1. Explicitly provided via --output option
    # 2. Set in the context (via global --output option)
    # 3. Set in the config file
    # 4. Default from Config class
    config_output = config_data.get("output_format")
    output_format = output or ctx_output or config_output or Config().output_format

    default_config = Config()

    # Reverse key mapping for display
    key_display = {
        "tenant_id": "tenant-id",
        "base_url": "base-url",
        "api_version": "api-version",
        "timeout": "timeout",
        "max_retries": "max-retries",
        "retry_backoff_factor": "retry-backoff",
        "output_format": "output-format",
    }

    # Build configuration items list
    config_items = []
    for config_key, display_key in key_display.items():
        value = config_data.get(config_key)
        if value is not None:
            config_items.append(
                {"key": display_key, "value": str(value), "source": "User config"}
            )
        else:
            default_value = getattr(default_config, config_key, None)
            if default_value is not None:
                config_items.append(
                    {
                        "key": display_key,
                        "value": str(default_value),
                        "source": "Default",
                    }
                )

    # Output based on format
    if output_format.lower() == "json":
        console.print(json.dumps(config_items, indent=2))
    else:
        table = Table(title="Configuration")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="green")
        table.add_column("Source", style="yellow")

        for item in config_items:
            table.add_row(item["key"], item["value"], item["source"])

        console.print(table)


@config.command("reset")
def reset_config() -> None:
    """Reset configuration to defaults."""
    if CONFIG_PATH.exists():
        try:
            CONFIG_PATH.unlink()
            console.print("[green]Configuration reset to defaults.[/green]")
        except IOError:
            console.print("[red]Error: Could not delete configuration file.[/red]")
    else:
        console.print(
            "[yellow]No configuration file found. Already using defaults.[/yellow]"
        )
