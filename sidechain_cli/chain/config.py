"""Config-related rippled commands."""

import click


@click.command(name="list")
def list_chains() -> None:
    """Get a list of running rippled nodes."""  # noqa: D301
    print("Insert list of chains here")
