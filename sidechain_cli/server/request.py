"""CLI functions involving sending RPC requests to a rippled node."""

from typing import Optional, Tuple

import click


@click.command(name="request")
@click.option(
    "--name", required=True, prompt=True, help="The name of the chain to query."
)
@click.argument("command", required=True)
@click.argument("args", nargs=-1)
def request_server(name: str, command: str, args: Tuple[str]) -> None:
    """
    Send a command-line request to a rippled or witness node.
    \f

    Args:
        name: The name of the chain to query.
        command: The rippled RPC command.
        args: The arguments for the RPC command.
    """  # noqa: D301
    print(f"{name}:", command, *args)


@click.command(name="status")
@click.option("--name", help="The name of the chain to query.")
@click.option("--all", is_flag=True, help="Whether to query all of the chains.")
def get_server_status(name: Optional[str] = None, query_all: bool = False) -> None:
    """
    Get the status of a rippled or witness node(s).
    \f

    Args:
        name: The name of the chain to query.
        query_all: Whether to stop all of the chains.
    """  # noqa: D301
    if name is None and query_all is False:
        print("Error: Must specify a name or `--all`.")
        return
    print(name, query_all)
