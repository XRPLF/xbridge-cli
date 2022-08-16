"""CLI functions involving sending RPC requests to a rippled node."""

import subprocess
from typing import Optional, Tuple

import click

from sidechain_cli.utils import ChainConfig, get_config


@click.command(name="request")
@click.option(
    "--name", required=True, prompt=True, help="The name of the chain to query."
)
@click.argument("command", required=True)
@click.argument("args", nargs=-1)
@click.option(
    "--verbose", is_flag=True, help="Whether or not to print more verbose information."
)
def request_server(
    name: str, command: str, args: Tuple[str], verbose: bool = False
) -> None:
    """
    Send a command-line request to a rippled or witness node.
    \f

    Args:
        name: The name of the server to query.
        command: The rippled RPC command.
        args: The arguments for the RPC command.
        verbose: Whether or not to print more verbose information.
    """  # noqa: D301
    if verbose:
        arg_string = " ".join(args)
        click.echo(f"{name}: {command} {arg_string}")
    config = get_config()
    server = config.get_server(name)

    if isinstance(server, ChainConfig):  # is a rippled node
        to_run = [server.rippled, "--conf", server.config, command, *args]
        subprocess.call(to_run)
    else:  # is a witness node
        click.echo("Cannot query witness nodes from the command line right now.")


@click.command(name="status")
@click.option("--name", help="The name of the server to query.")
@click.option("--all", is_flag=True, help="Whether to query all of the servers.")
def get_server_status(name: Optional[str] = None, query_all: bool = False) -> None:
    """
    Get the status of a rippled or witness node(s).
    \f

    Args:
        name: The name of the server to query.
        query_all: Whether to stop all of the servers.
    """  # noqa: D301
    if name is None and query_all is False:
        click.echo("Error: Must specify a name or `--all`.")
        return
    click.echo(f"{name} {query_all}")
