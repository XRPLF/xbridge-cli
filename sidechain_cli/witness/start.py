"""CLI functions for starting/stopping a witness node."""

import os
import signal
import subprocess
import time
from typing import Optional

import click

from sidechain_cli.utils import (
    CONFIG_FOLDER,
    WitnessData,
    add_witness,
    check_witness_exists,
    get_config,
    remove_witness,
)


@click.command(name="start")
@click.option(
    "--name",
    required=True,
    prompt=True,
    help="The name of the witness (used for differentiation purposes).",
)
@click.option(
    "--witnessd",
    required=True,
    prompt=True,
    type=click.Path(exists=True),
    help="The filepath to the witnessd executable.",
)
@click.option(
    "--config",
    required=True,
    prompt=True,
    type=click.Path(exists=True),
    help="The filepath to the witnessd config file.",
)
@click.option(
    "--verbose", is_flag=True, help="Whether or not to print more verbose information."
)
def start_witness(name: str, witnessd: str, config: str, verbose: bool = False) -> None:
    """
    Start a standalone node of witness.
    \f

    Args:
        name: The name of the witness (used for differentiation purposes).
        witnessd: The filepath to the witness executable.
        config: The filepath to the witnessd config file.
        verbose: Whether or not to print more verbose information.
    """  # noqa: D301
    witnessd = os.path.abspath(witnessd)
    config = os.path.abspath(config)
    if check_witness_exists(name, config):
        print("Error: Witness already running with that name or config.")
        return
    to_run = [witnessd, "--config", config]
    if verbose:
        print(f"Starting server {name}...")

    # create output file for easier debug purposes
    output_file = f"{CONFIG_FOLDER}/{name}.out"
    if not os.path.exists(output_file):
        # initialize file if it doesn't exist
        with open(output_file, "w") as f:
            f.write("")
    fout = open(output_file, "w")

    process = subprocess.Popen(
        to_run, stdout=fout, stderr=subprocess.STDOUT, close_fds=True
    )
    pid = process.pid

    witness_data: WitnessData = {
        "name": name,
        "witnessd": witnessd,
        "config": config,
        "pid": pid,
    }

    # check if witnessd actually started up correctly
    time.sleep(0.3)
    if process.poll() is not None:
        print("ERROR")
        with open(output_file) as f:
            print(f.read())
        return

    # add witness to config file
    add_witness(witness_data)
    if verbose:
        print(f"started witnessd at `{witnessd}` with config `{config}`", flush=True)
        print(f"PID: {pid}", flush=True)


@click.command(name="stop")
@click.option("--name", help="The name of the witness to stop.")
@click.option(
    "--all", "stop_all", is_flag=True, help="Whether to stop all of the witnesses."
)
@click.option(
    "--verbose", is_flag=True, help="Whether or not to print more verbose information."
)
def stop_witness(
    name: Optional[str] = None, stop_all: bool = False, verbose: bool = False
) -> None:
    """
    Stop a witness node(s).
    \f

    Args:
        name: The name of the witness to stop.
        stop_all: Whether to stop all of the witnesses.
        verbose: Whether or not to print more verbose information.
    """  # noqa: D301
    if name is None and stop_all is False:
        print("Error: Must specify a name or `--all`.")
        return
    config = get_config()
    if stop_all:
        witnesses = config.witnesses
    else:
        witnesses = [witness for witness in config.witnesses if witness["name"] == name]
    if verbose:
        witness_names = ",".join([witness["name"] for witness in witnesses])
        print(f"Shutting down: {witness_names}")

    # fout = open(os.devnull, "w")
    for witness in witnesses:
        # name = witness["name"]
        # witnessd = witness["witnessd"]
        # config = witness["config"]
        # to_run = [witnessd, "--config", config, "stop"]
        # subprocess.call(to_run, stdout=fout, stderr=subprocess.STDOUT)
        pid = witness["pid"]
        os.kill(pid, signal.SIGINT)
        if verbose:
            print(f"Stopped {name}")

    remove_witness(name, stop_all)


@click.command(name="restart")
@click.option("--name", help="The name of the witness to restart.")
@click.option(
    "--all",
    "restart_all",
    is_flag=True,
    help="Whether to restart all of the witnesses.",
)
@click.option(
    "--verbose", is_flag=True, help="Whether or not to print more verbose information."
)
@click.pass_context
def restart_witness(
    ctx: click.Context,
    name: Optional[str] = None,
    restart_all: bool = False,
    verbose: bool = False,
) -> None:
    """
    Restart a witness node(s).
    \f

    Args:
        ctx: The click context.
        name: The name of the witness to restart.
        restart_all: Whether to restart all of the witnesses.
        verbose: Whether or not to print more verbose information.
    """  # noqa: D301
    if name is None and restart_all is False:
        print("Error: Must specify a name or `--all`.")
        return

    config = get_config()
    if restart_all:
        witnesses = config.witnesses
    else:
        witnesses = [witness for witness in config.witnesses if witness["name"] == name]

    ctx.invoke(stop_witness, name=name, stop_all=restart_all, verbose=verbose)
    for witness in witnesses:
        ctx.invoke(
            start_witness,
            name=witness["name"],
            witnessd=witness["witnessd"],
            config=witness["config"],
            verbose=verbose,
        )
