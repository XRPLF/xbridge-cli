"""Config-related witness commands."""

import click


@click.command(name="list")
def list_witnesses() -> None:
    """Get a list of running witness nodes."""  # noqa: D301
    print("Insert list of witnesses here")
