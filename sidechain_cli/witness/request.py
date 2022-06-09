"""CLI functions involving sending RPC requests to a witness node."""

from typing import Optional, Tuple

import click


@click.command(name="request")
@click.option(
    "--name", required=True, prompt=True, help="The name of the witness node to query."
)
@click.argument("command", required=True)
@click.argument("args", nargs=-1)
def request_witness(name: str, command: str, args: Tuple[str]) -> None:
    """
    Send a command-line request to a witness node.
    \f

    Args:
        name: The name of the witness to query.
        command: The witness RPC command.
        args: The arguments for the RPC command.
    """  # noqa: D301
    print(f"{name}:", command, *args)


@click.command(name="status")
@click.option("--name", help="The name of the witness to query.")
@click.option("--all", is_flag=True, help="Whether to query all of the witnesses.")
def get_witness_status(name: Optional[str] = None, query_all: bool = False) -> None:
    """
    Get the status of a witness node(s).
    \f

    Args:
        name: The name of the witness to query.
        query_all: Whether to stop all of the witnesses.
    """  # noqa: D301
    if name is None and query_all is False:
        print("Error: Must specify a name or `--all`.")
        return
    print(name, query_all)
