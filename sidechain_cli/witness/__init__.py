"""Subcommand for all commands dealing with witness nodes."""

import click

from sidechain_cli.witness.config import list_witnesses
from sidechain_cli.witness.request import get_witness_status, request_witness
from sidechain_cli.witness.start import restart_witness, start_witness, stop_witness


@click.group()
def witness() -> None:
    """Subcommand for all commands dealing with witness nodes."""
    pass


witness.add_command(start_witness, name="start")
witness.add_command(stop_witness, name="stop")
witness.add_command(restart_witness, name="restart")

witness.add_command(list_witnesses, name="list")

witness.add_command(get_witness_status, name="status")
witness.add_command(request_witness, name="request")

__all__ = ["witness"]
