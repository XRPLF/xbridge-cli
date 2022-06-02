"""CLI command for setting up a bridge."""

import click


@click.command(name="bridge")
def setup_bridge() -> None:
    """Set up a bridge between a mainchain and sidechain."""
    print("BUILDING BRIDGE")
