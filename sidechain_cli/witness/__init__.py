"""Subcommand for all commands dealing with witness nodes."""

import click

from sidechain_cli.witness.start import start_witness


@click.group()
def witness() -> None:
    """Subcommand for all commands dealing with witness nodes."""
    pass


witness.add_command(start_witness, name="witness")

__all__ = ["start"]
