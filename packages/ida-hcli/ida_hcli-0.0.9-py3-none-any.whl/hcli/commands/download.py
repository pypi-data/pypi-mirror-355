from __future__ import annotations

from typing import Optional

import questionary
import rich_click as click
from rich.console import Console

from hcli.commands.common import safe_ask_async
from hcli.lib.api.common import get_api_client
from hcli.lib.api.download import VirtualFileSystem
from hcli.lib.api.download import download as download_api
from hcli.lib.commands import async_command, auth_command
from hcli.lib.constants import cli

console = Console()


async def traverse_vfs(vfs: VirtualFileSystem, current_path: str = "", version_filter: str = "") -> Optional[str]:
    """Traverse the virtual file system and select a download."""
    while True:
        # Get folders and files at current path
        folders = vfs.get_folders(current_path)
        files = vfs.get_files(current_path)

        # Apply version filter if specified
        if version_filter and not current_path:
            folders = [f for f in folders if version_filter in f]

        # Build choices
        choices = []

        # Add "Go back" option if not at root
        if current_path:
            choices.append("← Go back")

        # Add folders
        for folder in folders:
            choices.append(f"📁 {folder}")

        # Add files
        for file in files:
            display_name = f"{file.name} ({file.os}/{file.arch})"
            choices.append(f"📄 {display_name}")

        if not choices:
            console.print("[red]No items found at this path[/red]")
            return None

        # Show current path
        path_display = f"/{current_path}" if current_path else "/"
        console.print(f"[blue]Current path: {path_display}[/blue]")

        # Get user selection
        selection = await safe_ask_async(
            questionary.select("Select an item to navigate or download:", choices=choices, style=cli.SELECT_STYLE)
        )

        if not selection:
            return None

        # Handle selection
        if selection == "← Go back":
            # Go back one level
            if "/" in current_path:
                current_path = "/".join(current_path.split("/")[:-1])
            else:
                current_path = ""
        elif selection.startswith("📁 "):
            # Navigate into folder
            folder_name = selection[2:]  # Remove "📁 " prefix
            if current_path:
                current_path = f"{current_path}/{folder_name}"
            else:
                current_path = folder_name
        elif selection.startswith("📄 "):
            # File selected - find the corresponding resource
            file_display = selection[2:]  # Remove "📄 " prefix
            for file in files:
                if file_display.startswith(file.name):
                    return file.id
            return None

    return None


@auth_command()
@click.option("-f", "--force", is_flag=True, help="Skip cache")
@click.option("--output-dir", "output_dir", default="./", help="Output path")
@click.option("-v", "--version", "version_filter", help="Version filter (e.g., 9.1)")
@click.argument("slug", required=False)
@async_command
async def download(force: bool, output_dir: str, version_filter: Optional[str], slug: Optional[str]) -> None:
    """Download IDA binaries, SDK, utilities and more."""
    try:
        # Get downloads from API
        console.print("[yellow]Fetching available downloads...[/yellow]")
        resources = await download_api.get_downloads()

        if not resources:
            console.print("[red]No downloads available or unable to fetch downloads[/red]")
            return

        console.print(f"[green]Found {len(resources)} available downloads[/green]")

        # Create virtual file system
        vfs = VirtualFileSystem(resources)

        # If slug is provided, use it directly
        selected_slug: Optional[str]
        if slug:
            selected_slug = slug
        else:
            # Interactive navigation
            selected_slug = await traverse_vfs(vfs, "", version_filter or "")

            if not selected_slug:
                console.print("[yellow]Download cancelled[/yellow]")
                return

        # Get download URL
        console.print(f"[yellow]Getting download URL for: {selected_slug}[/yellow]")
        try:
            download_url = await download_api.get_download(selected_slug)
        except Exception as e:
            console.print(f"[red]Failed to get download URL: {e}[/red]")
            return

        # Ask for download location if not provided via command line
        if output_dir == "./":
            download_path = await safe_ask_async(
                questionary.path("Where do you want to download the file?", default=".")
            )

            if not download_path:
                console.print("[yellow]Download cancelled[/yellow]")
                return

            output_dir = download_path

        # Download the file
        console.print("[yellow]Starting download...[/yellow]")
        client = await get_api_client()

        target_path = await client.download_file(download_url, target_dir=output_dir, force=force, auth=True)

        console.print(f"[green]Download complete! File saved to: {target_path}[/green]")

    except Exception as e:
        console.print(f"[red]Download failed: {e}[/red]")
        raise
