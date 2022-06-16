"""Config-related witness commands."""

from dataclasses import asdict

import click
from tabulate import tabulate

from sidechain_cli.utils import get_config


@click.command(name="list")
def list_witnesses() -> None:
    """Get a list of running witness nodes."""
    config = get_config()
    if len(config.witnesses) == 0:
        print("No witnesses running.")
        return
    print(
        tabulate(
            map(asdict, config.witnesses),
            headers="keys",
            tablefmt="presto",
        )
    )
