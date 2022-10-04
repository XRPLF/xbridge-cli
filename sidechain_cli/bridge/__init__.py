"""CLI command for starting a bridge."""

import click

from sidechain_cli.bridge.setup import setup_bridge
from sidechain_cli.bridge.transfer import send_transfer


@click.group()
def bridge() -> None:
    """Subcommand for all commands dealing with the bridge itself."""
    pass


bridge.add_command(setup_bridge, name="build")
bridge.add_command(send_transfer, name="transfer")

__all__ = ["bridge"]
