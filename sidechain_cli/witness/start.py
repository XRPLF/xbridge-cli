"""CLI function for starting an witness node."""

import click


@click.command(name="witness")
@click.argument("witness")
@click.argument("config")
def start_witness(witness: str, config: str) -> None:
    """
    Start an witness node.

    Args:
        witness: The filepath to the witness node.
        config: The filepath to the witness config file.
    """
    print(witness)
    print(config)
