"""CLI subcommand for starting different types of nodes."""

import click

from sidechain_cli.start.attester import start_attester
from sidechain_cli.start.chain import start_chain


@click.group()
def start() -> None:
    """Start a node."""
    pass


start.add_command(start_chain, name="chain")
start.add_command(start_attester, name="attester")

__all__ = ["start"]
