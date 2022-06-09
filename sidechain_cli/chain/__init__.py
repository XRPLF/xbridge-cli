"""Subcommand for all commands dealing with rippled nodes."""

import click

from sidechain_cli.chain.start import start_chain


@click.group()
def chain() -> None:
    """Subcommand for all commands dealing with rippled nodes."""
    pass


chain.add_command(start_chain, name="start")

__all__ = ["chain"]
