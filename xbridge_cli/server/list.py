"""Config-related rippled commands."""

from dataclasses import asdict
from typing import Any, Dict, cast

import click
from tabulate import tabulate

from xbridge_cli.utils import get_config

# TODO: actually combine these tables


def _sort(server: Dict[str, Any]) -> str:
    return cast(str, server["name"])


def _list_chains() -> None:
    config = get_config()
    if len(config.chains) == 0:
        click.echo("No chains running.")
        return
    chains = list(map(asdict, config.chains))
    for chain in chains:
        del chain["type"]
    chains.sort(key=_sort)
    click.echo("Chains:")
    click.echo(
        tabulate(
            chains,
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

    witnesses = list(map(asdict, config.witnesses))
    for witness in witnesses:
        del witness["type"]
    witnesses.sort(key=_sort)

    click.echo("Witnesses:")
    click.echo(
        tabulate(
            witnesses,
            headers="keys",
            tablefmt="presto",
        )
    )


@click.command(name="list")
def list_servers() -> None:
    """Get a list of running rippled nodes."""
    _list_chains()
    click.echo("")
    _list_witnesses()
