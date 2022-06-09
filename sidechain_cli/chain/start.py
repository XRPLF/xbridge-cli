"""CLI function for starting a rippled node."""

import os
import subprocess

import click


@click.command(name="chain")
@click.option(
    "--rippled",
    required=True,
    type=click.Path(exists=True),
    help="The filepath to the rippled node.",
)
@click.option(
    "--config",
    required=True,
    type=click.Path(exists=True),
    help="The filepath to the rippled config file.",
)
@click.option(
    "--verbose", is_flag=True, help="Whether or not to print more verbose information."
)
def start_chain(rippled: str, config: str, verbose: bool = False) -> None:
    """
    Start a standalone node of rippled.
    \f

    Args:
        rippled: The filepath to the rippled node.
        config: The filepath to the rippled config file.
        verbose: Whether or not to print more verbose information.
    """  # noqa: D301
    to_run = [rippled, "--conf", config, "-a"]
    if verbose:
        print("Starting server...")
    fout = open(os.devnull, "w")
    process = subprocess.Popen(
        to_run, stdout=fout, stderr=subprocess.STDOUT, close_fds=True
    )
    pid = process.pid
    if verbose:
        print(f"started rippled: {rippled} PID: {pid}", flush=True)
