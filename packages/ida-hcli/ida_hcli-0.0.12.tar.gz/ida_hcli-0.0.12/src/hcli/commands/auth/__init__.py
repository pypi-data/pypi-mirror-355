from __future__ import annotations

import rich_click as click
from rich.console import Console

console = Console()


@click.group()
def auth() -> None:
    """Authentication commands."""
    pass


# Subcommands placeholders
from .keys import keys  # noqa: E402

auth.add_command(keys)
