from __future__ import annotations

import rich_click as click
from rich.console import Console

from hcli.lib.commands import async_command
from hcli.lib.ida import accept_eula, get_ida_path

console = Console()


@click.option("-i", "--install-dir", "install_dir", required=True, help="Install dir")
@click.option("-a", "--accept-eula", "eula", is_flag=True, help="Accept EULA", default=True)
@click.argument("installer", required=True)
@click.command()
@async_command
async def install(install_dir: str, eula: bool, installer: str) -> None:
    """Download IDA binaries, SDK, utilities and more."""
    try:
        # Download the file
        console.print(f"[yellow]Installing {installer}...[/yellow]")
        from hcli.lib.ida import install_ida

        await install_ida(installer, install_dir)

        if eula:
            accept_eula(get_ida_path(install_dir))
        console.print("[green]Installation complete![/green]")

    except Exception as e:
        console.print(f"[red]Download failed: {e}[/red]")
        raise
