from __future__ import annotations

import rich_click as click
from rich.console import Console

console = Console()


@click.group()
def plugin() -> None:
    """Manage plugins. TODO"""
    pass
