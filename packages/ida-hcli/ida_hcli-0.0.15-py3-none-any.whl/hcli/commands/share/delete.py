from __future__ import annotations

from typing import List, Optional

import rich_click as click
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table

from hcli.lib.api.share import SharedFile, share
from hcli.lib.commands import async_command, auth_command

console = Console()


@auth_command(help="Delete shared files by their shortcode.")
@click.argument("shortcodes", nargs=-1, required=True, metavar="SHORTCODE...")
@click.option("-f", "--force", is_flag=True, help="Skip confirmation prompt")
@click.option("--batch", is_flag=True, help="Process multiple shortcodes in batch mode")
@async_command
async def delete(shortcodes: tuple[str, ...], force: bool, batch: bool) -> None:
    """Delete shared files by their shortcodes.

    You can delete single or multiple files:

    \b
    hcli share delete ABC123
    hcli share delete ABC123 DEF456 GHI789
    hcli share delete --batch ABC123 DEF456 GHI789
    """

    if not shortcodes:
        console.print("[red]Error: At least one shortcode must be provided[/red]")
        raise click.Abort()

    # Convert to list for easier processing
    codes_list = list(shortcodes)

    try:
        # Get file information first to show what will be deleted
        files_info: List[Optional[SharedFile]] = []

        with console.status("[bold blue]Getting file information..."):
            for code in codes_list:
                try:
                    file_info = await share.get_file(code)
                    files_info.append(file_info)
                except Exception as e:
                    console.print(f"[red]Warning: Could not get info for {code}: {e}[/red]")
                    # Still allow deletion attempt
                    files_info.append(None)

        # Display files to be deleted
        if len(codes_list) > 1 or batch:
            display_deletion_summary(codes_list, files_info)
        else:
            # Single file
            if files_info[0]:
                file = files_info[0]
                console.print("\n[bold]File to delete:[/bold]")
                console.print(f"  Name: {file.name}")
                console.print(f"  Code: {file.code}")
                console.print(f"  Size: {format_size(file.size)}")
                console.print(f"  ACL: {file.acl_type}")
            else:
                console.print(f"\n[bold]File to delete:[/bold] {codes_list[0]} (info unavailable)")

        # Confirmation
        if not force:
            if len(codes_list) == 1:
                if not Confirm.ask(f"\n[bold red]Delete file {codes_list[0]}?[/bold red]"):
                    console.print("[yellow]Deletion cancelled.[/yellow]")
                    return
            else:
                if not Confirm.ask(f"\n[bold red]Delete {len(codes_list)} files?[/bold red]"):
                    console.print("[yellow]Deletion cancelled.[/yellow]")
                    return

        # Delete files
        success_count = 0
        failed_codes = []

        for code in codes_list:
            try:
                with console.status(f"[bold red]Deleting {code}..."):
                    await share.delete_file(code)
                console.print(f"[green]✓ Deleted: {code}[/green]")
                success_count += 1
            except Exception as e:
                console.print(f"[red]✗ Failed to delete {code}: {e}[/red]")
                failed_codes.append(code)

        # Summary
        console.print("\n[bold]Deletion Summary:[/bold]")
        console.print(f"  [green]✓ Successfully deleted: {success_count}[/green]")

        if failed_codes:
            console.print(f"  [red]✗ Failed to delete: {len(failed_codes)}[/red]")
            console.print(f"    Failed codes: {', '.join(failed_codes)}")

        if success_count == len(codes_list):
            console.print("\n[green]All files deleted successfully![/green]")
        elif success_count == 0:
            console.print("\n[red]No files were deleted.[/red]")
            raise click.Abort()
        else:
            console.print(f"\n[yellow]Partial success: {success_count}/{len(codes_list)} files deleted.[/yellow]")

    except Exception as e:
        console.print(f"[red]Error during deletion: {e}[/red]")
        raise click.Abort()


def display_deletion_summary(codes: List[str], files_info: List) -> None:
    """Display a summary table of files to be deleted."""
    console.print(f"\n[bold]Files to delete ({len(codes)} files):[/bold]")

    table = Table(show_header=True, header_style="bold red")
    table.add_column("Code", style="cyan", width=10)
    table.add_column("Name", style="white", width=30)
    table.add_column("Size", style="green", width=10)
    table.add_column("ACL", style="yellow", width=12)
    table.add_column("Status", style="dim", width=15)

    for i, code in enumerate(codes):
        file_info = files_info[i] if i < len(files_info) else None

        if file_info:
            name = truncate(file_info.name or "unnamed", 30)
            size = format_size(file_info.size)
            acl = file_info.acl_type
            status = "Ready"
        else:
            name = "Unknown"
            size = "Unknown"
            acl = "Unknown"
            status = "Info unavailable"

        table.add_row(code, name, size, acl, status)

    console.print(table)


def format_size(bytes_count: int) -> str:
    """Convert bytes to human-readable format."""
    sizes = ["B", "KB", "MB", "GB", "TB"]
    if bytes_count == 0:
        return "0 B"

    import math

    i = int(math.floor(math.log(bytes_count) / math.log(1024)))
    return f"{bytes_count / math.pow(1024, i):.1f} {sizes[i]}"


def truncate(text: str, max_length: int) -> str:
    """Truncate text with ellipsis if too long."""
    return text[: max_length - 3] + "..." if len(text) > max_length else text
