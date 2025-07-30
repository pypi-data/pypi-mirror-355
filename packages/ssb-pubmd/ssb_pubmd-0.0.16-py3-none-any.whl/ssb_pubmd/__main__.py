"""Command-line interface."""

import json
import os
from enum import Enum
from pathlib import Path
from typing import cast
from urllib.parse import urlparse

import click

from ssb_pubmd.browser_request_handler import BrowserRequestHandler
from ssb_pubmd.browser_request_handler import CreateContextMethod
from ssb_pubmd.constants import APP_NAME
from ssb_pubmd.constants import CACHE_FILE
from ssb_pubmd.constants import CONFIG_FILE
from ssb_pubmd.markdown_syncer import MarkdownSyncer


class ConfigKey(Enum):
    """Configuration keys for the application."""

    LOGIN_URL = "login_url"
    POST_URL = "post_url"


def get_config_value(config_key: ConfigKey) -> str:
    """Load a configuration value, with precedence environment variable > config file."""
    key = config_key.value

    def get_env_value() -> str:
        """Get value from environment variable, by uppercasing the key and adding prefix."""
        prefix = f"{APP_NAME.upper()}_"
        value = os.getenv(f"{prefix}{key.upper()}")

        return cast(str, value)

    def get_config_file_value() -> str:
        """Get value from the config file."""
        with open(CONFIG_FILE) as f:
            data = json.load(f)

        value = data.get(key)

        return cast(str, value)

    return get_env_value() or get_config_file_value()


def set_config_value(config_key: ConfigKey, value: str) -> None:
    """Set a configuration value in the config file."""
    key = config_key.value

    with open(CONFIG_FILE) as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}

    data[key] = value

    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)


@click.group()
def cli() -> None:
    """Pubmd - a tool to sync markdown and notebook files to a CMS."""
    pass


@cli.command()
def settings() -> None:
    """Set the login and post URL for the CMS."""
    login_url = click.prompt("Enter the login URL", type=str)
    set_config_value(ConfigKey.LOGIN_URL, login_url)

    post_url = click.prompt("Enter the post URL", type=str)
    set_config_value(ConfigKey.POST_URL, post_url)

    click.echo(f"\nSettings stored in:\n{click.format_filename(CONFIG_FILE)}")


@cli.command()
def login() -> None:
    """Log in to the CMS application."""
    login_url = get_config_value(ConfigKey.LOGIN_URL)
    request_handler = BrowserRequestHandler(CACHE_FILE, login_url)

    method = CreateContextMethod.FROM_LOGIN
    with request_handler.new_context(method=method):
        click.echo("Logging in...")

    click.echo(f"\nBrowser context stored in:\n{CACHE_FILE}")


@cli.command()
@click.argument("content_file_path", type=click.Path())
def sync(content_file_path: str) -> None:
    """Sync a markdown or notebook file to the CMS."""
    login_url = get_config_value(ConfigKey.LOGIN_URL)
    request_handler = BrowserRequestHandler(CACHE_FILE, login_url)

    with request_handler.new_context() as context:
        post_url = get_config_value(ConfigKey.POST_URL)
        syncer = MarkdownSyncer(post_url, request_handler)

        syncer.content_file_path = Path(content_file_path)
        response = syncer.sync_content()

        click.echo("Content synced successfully.")

        path = response.body.get("previewPath", "")
        preview = urlparse(login_url)._replace(path=path).geturl()
        if preview:
            page = context.new_page()
            page.goto(preview)
            click.echo(f"Preview opened in new browser: {preview}")
            click.echo("Close the browser tab to finish.")
            page.wait_for_event("close", timeout=0)
        else:
            click.echo("No preview url found in the response.")


if __name__ == "__main__":
    cli()
