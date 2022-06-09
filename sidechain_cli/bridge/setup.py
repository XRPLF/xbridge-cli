"""CLI command for setting up a bridge."""

import click


@click.command(name="build")
def setup_bridge() -> None:
    """Set up a bridge between a mainchain and sidechain."""
    print("BUILDING BRIDGE")
