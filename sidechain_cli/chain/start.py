"""CLI functions for starting/stopping a rippled node."""

import os
import subprocess
from typing import Optional

import click

from sidechain_cli.utils import ChainData, add_chain, check_chain_exists


@click.command(name="start")
@click.option(
    "--name",
    required=True,
    prompt=True,
    help="The name of the chain (used for differentiation purposes).",
)
@click.option(
    "--rippled",
    required=True,
    prompt=True,
    type=click.Path(exists=True),
    help="The filepath to the rippled executable.",
)
@click.option(
    "--config",
    required=True,
    prompt=True,
    type=click.Path(exists=True),
    help="The filepath to the rippled config file.",
)
@click.option(
    "--verbose", is_flag=True, help="Whether or not to print more verbose information."
)
def start_chain(name: str, rippled: str, config: str, verbose: bool = False) -> None:
    """
    Start a standalone node of rippled.
    \f

    Args:
        name: The name of the chain (used for differentiation purposes).
        rippled: The filepath to the rippled executable.
        config: The filepath to the rippled config file.
        verbose: Whether or not to print more verbose information.
    """  # noqa: D301
    rippled = os.path.abspath(rippled)
    config = os.path.abspath(config)
    if check_chain_exists(name, config):
        print("Error: Chain already running with that name or config.")
        return
    to_run = [rippled, "--conf", config, "-a"]
    if verbose:
        print("Starting server...")
    fout = open(os.devnull, "w")
    process = subprocess.Popen(
        to_run, stdout=fout, stderr=subprocess.STDOUT, close_fds=True
    )
    pid = process.pid
    chain_data: ChainData = {
        "name": name,
        "rippled": rippled,
        "config": config,
        "pid": pid,
    }
    add_chain(chain_data)
    if verbose:
        print(f"started rippled: {rippled} PID: {pid}", flush=True)


@click.command(name="stop")
@click.option("--name", help="The name of the chain to stop.")
@click.option(
    "--all", "stop_all", is_flag=True, help="Whether to stop all of the chains."
)
def stop_chain(name: Optional[str] = None, stop_all: bool = False) -> None:
    """
    Stop a rippled node(s).
    \f

    Args:
        name: The name of the chain to stop.
        stop_all: Whether to stop all of the chains.
    """  # noqa: D301
    if name is None and stop_all is False:
        print("Error: Must specify a name or `--all`.")
        return
    print(name, stop_all)


@click.command(name="restart")
@click.option("--name", help="The name of the chain to restart.")
@click.option(
    "--all", "restart_all", is_flag=True, help="Whether to stop all of the chains."
)
def restart_chain(name: Optional[str] = None, restart_all: bool = False) -> None:
    """
    Restart a rippled node(s).
    \f

    Args:
        name: The name of the chain to restart.
        restart_all: Whether to restart all of the chains.
    """  # noqa: D301
    if name is None and restart_all is False:
        print("Error: Must specify a name or `--all`.")
        return
    print(name, restart_all)
