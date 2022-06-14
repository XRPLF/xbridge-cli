"""Config-related witness commands."""

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
            config.witnesses,
            headers="keys",
            tablefmt="presto",
        )
    )
