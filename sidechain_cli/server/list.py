"""Config-related rippled commands."""

from dataclasses import asdict

import click
from tabulate import tabulate

from sidechain_cli.utils import get_config

# TODO: actually combine these tables


def _list_chains() -> None:
    config = get_config()
    if len(config.chains) == 0:
        click.echo("No chains running.")
        return
    click.echo(
        tabulate(
            map(asdict, config.chains),
            headers="keys",
            tablefmt="presto",
        )
    )


def _list_witnesses() -> None:
    """Get a list of running witness nodes."""
    config = get_config()
    if len(config.witnesses) == 0:
        click.echo("No witnesses running.")
        return
    click.echo(
        tabulate(
            map(asdict, config.witnesses),
            headers="keys",
            tablefmt="presto",
        )
    )


@click.command(name="list")
def list_servers() -> None:
    """Get a list of running rippled nodes."""
    _list_chains()
    _list_witnesses()
