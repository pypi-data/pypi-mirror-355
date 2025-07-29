from __future__ import annotations

import rich_click as click

from hcli.commands.auth.keys.create import create
from hcli.commands.auth.keys.install import install_key
from hcli.commands.auth.keys.list import list_keys
from hcli.commands.auth.keys.revoke import revoke
from hcli.commands.auth.keys.uninstall import uninstall_key


@click.group()
def keys() -> None:
    """API key management."""
    pass


keys.add_command(create)
keys.add_command(list_keys, name="list")
keys.add_command(revoke)
keys.add_command(install_key)
keys.add_command(uninstall_key)
