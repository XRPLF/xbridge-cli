"""Config-related rippled commands."""

import os
import subprocess

import click

from sidechain_cli.utils import get_config, get_config_folder


@click.command(name="print")
@click.option("--name", help="The name of the server.")
def print_server_output(name: str) -> None:
    """
    Print the stdout/stderr output of a server.
    \f

    Args:
        name: Name of the server.
    """  # noqa: D301
    server_config = get_config().get_server(name)
    if server_config.is_docker():
        subprocess.run(["docker", "logs", name])
    else:
        file_loc = os.path.join(get_config_folder(), f"{name}.out")
        with open(file_loc) as f:
            for line in f:
                click.echo(line.strip("\n"))
