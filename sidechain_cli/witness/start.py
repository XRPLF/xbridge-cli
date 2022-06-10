"""CLI functions for starting/stopping a witness node."""

from typing import Optional

import click


@click.command(name="start")
@click.option(
    "--name", help="The name of the witness (used for differentiation purposes)."
)
@click.option(
    "--witness",
    required=True,
    prompt=True,
    type=click.Path(exists=True),
    help="The filepath to the witness executable.",
)
@click.option(
    "--config",
    required=True,
    prompt=True,
    type=click.Path(exists=True),
    help="The filepath to the witness config file.",
)
@click.option(
    "--verbose", is_flag=True, help="Whether or not to print more verbose information."
)
def start_witness(name: str, witness: str, config: str, verbose: bool = False) -> None:
    """
    Start a standalone node of witness.
    \f

    Args:
        name: The name of the witness (used for differentiation purposes).
        witness: The filepath to the witness executable.
        config: The filepath to the witness config file.
        verbose: Whether or not to print more verbose information.
    """  # noqa: D301
    print(name, witness, config, verbose)


@click.command(name="stop")
@click.option("--name", help="The name of the witness to stop.")
@click.option("--all", is_flag=True, help="Whether to stop all of the witnesses.")
def stop_witness(name: Optional[str] = None, stop_all: bool = False) -> None:
    """
    Stop a witness node(s).
    \f

    Args:
        name: The name of the witness to stop.
        stop_all: Whether to stop all of the witnesses.
    """  # noqa: D301
    if name is None and stop_all is False:
        print("Error: Must specify a name or `--all`.")
        return
    print(name, stop_all)


@click.command(name="restart")
@click.option("--name", help="The name of the witness to restart.")
@click.option("--all", is_flag=True, help="Whether to restart all of the witnesses.")
def restart_witness(name: Optional[str] = None, restart_all: bool = False) -> None:
    """
    Restart a witness node(s).
    \f

    Args:
        name: The name of the witness to restart.
        restart_all: Whether to restart all of the witnesses.
    """  # noqa: D301
    if name is None and restart_all is False:
        print("Error: Must specify a name or `--all`.")
        return
    print(name, restart_all)
