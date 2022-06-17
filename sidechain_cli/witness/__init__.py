"""Subcommand for all commands dealing with witness nodes."""

import click

from sidechain_cli.witness.start import restart_witness, start_witness, stop_witness


@click.group()
def witness() -> None:
    """Subcommand for all commands dealing with witness nodes."""
    pass


witness.add_command(start_witness, name="start")
witness.add_command(stop_witness, name="stop")
witness.add_command(restart_witness, name="restart")

__all__ = ["witness"]
