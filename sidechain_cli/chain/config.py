"""Config-related rippled commands."""

import click
from tabulate import tabulate

from sidechain_cli.utils import get_config


@click.command(name="list")
def list_chains() -> None:
    """Get a list of running rippled nodes."""  # noqa: D301
    config = get_config()
    print(
        tabulate(
            config.chains,
            headers="keys",
            tablefmt="presto",
        )
    )
