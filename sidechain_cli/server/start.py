"""CLI functions for starting/stopping a rippled node."""

import json
import os
import signal
import subprocess
import time
from typing import List, Optional, cast

import click

from sidechain_cli.utils import (
    CONFIG_FOLDER,
    ChainConfig,
    ChainData,
    RippledConfig,
    ServerConfig,
    WitnessConfig,
    WitnessData,
    add_chain,
    add_witness,
    check_server_exists,
    get_config,
    remove_server,
)


@click.command(name="start")
@click.option(
    "--name",
    required=True,
    prompt=True,
    help="The name of the chain (used for differentiation purposes).",
)
@click.option(
    "--exe",
    required=True,
    prompt=True,
    type=click.Path(exists=True),
    help="The filepath to the executable.",
)
@click.option(
    "--config",
    required=True,
    prompt=True,
    type=click.Path(exists=True),
    help="The filepath to the exe config file.",
)
@click.option(
    "--verbose", is_flag=True, help="Whether or not to print more verbose information."
)
def start_server(name: str, exe: str, config: str, verbose: bool = False) -> None:
    """
    Start a standalone node of rippled or a witness node.
    \f

    Args:
        name: The name of the chain (used for differentiation purposes).
        exe: The filepath to the executable.
        config: The filepath to the config file.
        verbose: Whether or not to print more verbose information.
    """  # noqa: D301
    exe = os.path.abspath(exe)
    config = os.path.abspath(config)
    try:
        config_object = RippledConfig(file_name=config)
        is_rippled = True
    except ValueError:
        with open(config) as f:
            config_json = json.load(f)
        is_rippled = False
    if check_server_exists(name, config):
        click.echo("Error: Server already running with that name or config.")
        return

    server_type = "rippled" if is_rippled else "witness"
    if verbose:
        click.echo(f"Starting {server_type} server {name}...")

    if is_rippled:
        to_run = [exe, "--conf", config, "-a"]
    else:
        to_run = [exe, "--config", config, "--verbose"]

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

    # check if server actually started up correctly
    time.sleep(0.3)
    if process.poll() is not None:
        click.echo("ERROR")
        with open(output_file) as f:
            click.echo(f.read())
        return

    if is_rippled:
        chain_data: ChainData = {
            "name": name,
            "type": "rippled",
            "rippled": exe,
            "config": config,
            "pid": pid,
            "ws_ip": config_object.port_ws_admin_local.ip,
            "ws_port": int(config_object.port_ws_admin_local.port),
            "http_ip": config_object.port_rpc_admin_local.ip,
            "http_port": int(config_object.port_rpc_admin_local.port),
        }
        # add chain to config file
        add_chain(chain_data)
    else:
        witness_data: WitnessData = {
            "name": name,
            "type": "witness",
            "witnessd": exe,
            "config": config,
            "pid": pid,
            "ip": config_json["RPCEndpoint"]["IP"],
            "rpc_port": config_json["RPCEndpoint"]["Port"],
        }
        # add witness to config file
        add_witness(witness_data)

    if verbose:
        click.echo(f"started {server_type} at `{exe}` with config `{config}`")
        click.echo(f"PID: {pid}")


@click.command(name="start-all")
@click.option(
    "--config_dir",
    envvar="XCHAIN_CONFIG_DIR",
    required=True,
    prompt=True,
    type=click.Path(exists=True),
    help="The folder in which config files are storeds.",
)
@click.option(
    "--rippled_exe",
    envvar="RIPPLED_EXE",
    required=True,
    prompt=True,
    type=click.Path(exists=True),
    help="The filepath to the rippled executable.",
)
@click.option(
    "--witnessd_exe",
    envvar="WITNESSD_EXE",
    required=True,
    prompt=True,
    type=click.Path(exists=True),
    help="The filepath to the witnessd executable.",
)
@click.option(
    "--verbose", is_flag=True, help="Whether or not to print more verbose information."
)
@click.pass_context
def start_all_servers(
    ctx: click.Context,
    config_dir: str,
    rippled_exe: str,
    witnessd_exe: str,
    verbose: bool = False,
) -> None:
    """
    Start all the servers (both rippled and witnesses) that have config files in the
    config directory. If there is a rippled.cfg file in the folder, it will start
    rippled. If there is a witness.json file in the folder, it will start a witness.
    \f

    Args:
        ctx: The click context.
        config_dir: The filepath to the config folder.
        rippled_exe: The filepath to the rippled executable.
        witnessd_exe: The filepath to the witnessd executable.
        verbose: Whether or not to print more verbose information.
    """  # noqa: D301
    if not os.path.isdir(config_dir):
        click.echo(f"Error: {config_dir} is not a directory.")
        return
    chains = []
    witnesses = []
    for name in os.listdir(config_dir):
        filepath = os.path.join(config_dir, name)
        if os.path.isdir(filepath):
            if "rippled.cfg" in os.listdir(filepath):
                config = os.path.join(filepath, "rippled.cfg")
                chains.append((name, config))
            elif "witness.json" in os.listdir(filepath):
                config = os.path.join(filepath, "witness.json")
                witnesses.append((name, config))
            else:
                continue

    # TODO: simplify this logic once the witness can start up without the chains
    for name, config in chains:
        ctx.invoke(
            start_server, name=name, exe=rippled_exe, config=config, verbose=verbose
        )
    time.sleep(3)
    for name, config in witnesses:
        ctx.invoke(
            start_server, name=name, exe=witnessd_exe, config=config, verbose=verbose
        )


@click.command(name="stop")
@click.option("--name", help="The name of the server to stop.")
@click.option(
    "--all", "stop_all", is_flag=True, help="Whether to stop all of the servers."
)
@click.option(
    "--verbose", is_flag=True, help="Whether or not to print more verbose information."
)
def stop_server(
    name: Optional[str] = None, stop_all: bool = False, verbose: bool = False
) -> None:
    """
    Stop a rippled node(s).
    \f

    Args:
        name: The name of the server to stop.
        stop_all: Whether to stop all of the servers.
        verbose: Whether or not to print more verbose information.
    """  # noqa: D301
    if name is None and stop_all is False:
        click.echo("Error: Must specify a name or `--all`.")
        return
    config = get_config()
    if stop_all:
        servers = cast(List[ServerConfig], config.chains) + cast(
            List[ServerConfig], config.witnesses
        )
    else:
        assert name is not None
        servers = [config.get_server(name)]
    if verbose:
        server_names = ",".join([server.name for server in servers])
        click.echo(f"Shutting down: {server_names}")

    # fout = open(os.devnull, "w")
    for server in servers:
        if isinstance(server, ChainConfig):
            # TODO: stop the server with a CLI command
            # to_run = [server.rippled, "--conf", server.config, "stop"]
            # subprocess.call(to_run, stdout=fout, stderr=subprocess.STDOUT)
            pid = server.pid
            try:
                os.kill(pid, signal.SIGINT)
            except ProcessLookupError:
                pass  # process already died somehow
        else:
            # TODO: stop the server with a CLI command
            # to_run = [server.witnessd, "--config", server.config, "stop"]
            # subprocess.call(to_run, stdout=fout, stderr=subprocess.STDOUT)
            pid = server.pid
            try:
                os.kill(pid, signal.SIGINT)
            except ProcessLookupError:
                pass  # process already died somehow
        if verbose:
            click.echo(f"Stopped {server.name}")

    remove_server(name, stop_all)


@click.command(name="restart")
@click.option("--name", help="The name of the server to restart.")
@click.option(
    "--all", "restart_all", is_flag=True, help="Whether to stop all of the servers."
)
@click.option(
    "--verbose", is_flag=True, help="Whether or not to print more verbose information."
)
@click.pass_context
def restart_server(
    ctx: click.Context,
    name: Optional[str] = None,
    restart_all: bool = False,
    verbose: bool = False,
) -> None:
    """
    Restart a rippled or witness node(s).
    \f

    Args:
        ctx: The click context.
        name: The name of the server to restart.
        restart_all: Whether to restart all of the servers.
        verbose: Whether or not to print more verbose information.
    """  # noqa: D301
    if name is None and restart_all is False:
        click.echo("Error: Must specify a name or `--all`.")
        return

    config = get_config()
    if restart_all:
        servers = cast(List[ServerConfig], config.chains) + cast(
            List[ServerConfig], config.witnesses
        )
    else:
        assert name is not None
        servers = [config.get_server(name)]

    ctx.invoke(stop_server, name=name, stop_all=restart_all, verbose=verbose)
    for server in servers:
        if isinstance(server, ChainConfig):
            ctx.invoke(
                start_server,
                name=server.name,
                exe=server.rippled,
                config=server.config,
                verbose=verbose,
            )
        else:
            assert isinstance(server, WitnessConfig)
            ctx.invoke(
                start_server,
                name=server.name,
                exe=server.witnessd,
                config=server.config,
                verbose=verbose,
            )
