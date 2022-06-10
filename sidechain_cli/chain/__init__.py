"""Subcommand for all commands dealing with rippled nodes."""

import click

from sidechain_cli.chain.config import list_chains
from sidechain_cli.chain.request import get_chain_status, request_chain
from sidechain_cli.chain.start import restart_chain, start_chain, stop_chain


@click.group()
def chain() -> None:
    """Subcommand for all commands dealing with rippled nodes."""
    pass


chain.add_command(start_chain, name="start")
chain.add_command(stop_chain, name="stop")
chain.add_command(restart_chain, name="restart")

chain.add_command(list_chains, name="list")

chain.add_command(get_chain_status, name="status")
chain.add_command(request_chain, name="request")

__all__ = ["chain"]
