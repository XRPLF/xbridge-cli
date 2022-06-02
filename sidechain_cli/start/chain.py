"""CLI function for starting a rippled node."""

import click


@click.command(name="chain")
@click.argument("rippled")
@click.argument("config")
def start_chain(rippled: str, config: str) -> None:
    """
    Start a standalone node of rippled.

    Args:
        rippled: The filepath to the rippled node.
        config: The filepath to the rippled config file.
    """
    print(rippled)
    print(config)
