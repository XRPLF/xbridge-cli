"""CLI function for starting an attester node."""

import click


@click.command(name="attester")
@click.argument("attester")
@click.argument("config")
def start_attester(attester: str, config: str) -> None:
    """
    Start an attester node.

    Args:
        attester: The filepath to the attester node.
        config: The filepath to the attester config file.
    """
    print(attester)
    print(config)
