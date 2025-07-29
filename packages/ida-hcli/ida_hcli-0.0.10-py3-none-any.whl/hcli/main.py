from __future__ import annotations

from importlib.metadata import entry_points

import rich_click as click
from rich.console import Console

from hcli import __version__
from hcli.commands import register_commands
from hcli.lib.util.version import BackgroundUpdateChecker

console = Console()

# Configure rich-click styling
click.rich_click.USE_RICH_MARKUP = True

# Global update checker instance
update_checker: BackgroundUpdateChecker | None = None


def load_extensions():
    eps = entry_points()
    return [ep.load() for ep in eps.select(group="hcli.extensions")]


def get_help_text():
    """Generate help text with extensions information."""
    base_help = f"[bold blue]HCLI[/bold blue] [dim](v{__version__})[/dim]\n\n[yellow]Hex-Rays Command-line interface for managing IDA installation, licenses and more.[/yellow]"

    # Check for available extensions
    eps = entry_points()
    extension_eps = list(eps.select(group="hcli.extensions"))

    if extension_eps:
        extensions_list = ", ".join([ep.name for ep in extension_eps])
        base_help += f"\n\n[bold green]Extensions:[/bold green] [cyan]{extensions_list}[/cyan]"

    return base_help


@click.group(help=get_help_text())
@click.version_option(package_name="ida-hcli")
@click.pass_context
def cli(_ctx):
    """Main CLI entry point with background update checking."""
    global update_checker

    # Initialize update checker
    update_checker = BackgroundUpdateChecker()

    # Start background check (non-blocking)
    update_checker.start_check()


@cli.result_callback()
@click.pass_context
def handle_command_completion(_ctx, _result, **_kwargs):
    """Handle command completion and show update notifications."""
    # Show update message if available (result callback only runs on success)
    update_msg = update_checker.get_result(timeout=2.0) if update_checker else None
    if update_msg:
        console.print(update_msg, markup=True)


# register subcommands
register_commands(cli)

# Register plugins dynamically
for extension in load_extensions():
    extension(cli)

if __name__ == "__main__":
    cli()
