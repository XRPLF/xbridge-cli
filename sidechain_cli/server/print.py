"""Config-related rippled commands."""

import os

import click

from sidechain_cli.utils.config_file import CONFIG_FOLDER


@click.command(name="print")
@click.option("--name", help="The name of the server.")
def print_server_output(name: str) -> None:
    """
    Print the stdout/stderr output of a server.

    Args:
        name: Name of the server.
    """
    file_loc = os.path.join(CONFIG_FOLDER, f"{name}.out")
    with open(file_loc) as f:
        for line in f:
            click.echo(line.strip())
