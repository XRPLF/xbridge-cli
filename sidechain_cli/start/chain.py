"""CLI function for starting a rippled node."""

import os
import subprocess

import click


@click.command(name="chain")
@click.argument("rippled", required=True, type=click.Path(exists=True))
@click.argument("config", required=True, type=click.Path(exists=True))
@click.option(
    "--verbose", is_flag=True, help="Whether or not to print more verbose information."
)
def start_chain(rippled: str, config: str, verbose: bool = False) -> None:
    """
    Start a standalone node of rippled.

    \b
    Args:
        rippled: The filepath to the rippled node.
        config: The filepath to the rippled config file.
    """
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
