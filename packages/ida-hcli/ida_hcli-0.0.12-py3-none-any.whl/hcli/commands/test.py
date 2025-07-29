from __future__ import annotations

import questionary
import rich_click as click
from rich.console import Console

from hcli.lib.commands import async_command

console = Console()


@click.command(name="test", hidden=True)
@async_command
async def test_command() -> None:
    # Confirm key creation
    if not await questionary.confirm("Do you want to create a new API key [underline]hello[/underline]?").ask_async():
        console.print("[yellow]Key creation cancelled.[/yellow]")
        return
    else:
        console.print("[yellow]All ok.[/yellow]")

    pass
