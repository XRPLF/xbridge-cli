"""CLI command for setting up a bridge."""

import click


@click.command(name="transfer")
def send_transfer() -> None:
    """Set up a bridge between a mainchain and sidechain."""
    print("TRANSFERRING ACROSS BRIDGE")
