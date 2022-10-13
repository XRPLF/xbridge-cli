"""CLI functions for starting/stopping a rippled node."""

import json
import os
import signal
import subprocess
import time
from typing import List, Optional, Tuple, cast

import click

from sidechain_cli.exceptions import SidechainCLIException
from sidechain_cli.utils import (
    ChainConfig,
    ChainData,
    RippledConfig,
    ServerConfig,
    WitnessData,
    add_chain,
    add_witness,
    check_server_exists,
    get_config,
    get_config_folder,
    remove_server,
)

_DOCKER_COMPOSE_FILE = os.path.abspath(
    os.path.join(
        os.path.realpath(__file__),
        "..",
        "..",
        "..",
        "docker",
        "docker-compose.yml",
    )
)


def _run_process(to_run: List[str], out_file: str) -> Tuple[int, str]:
    # create output file for easier debug purposes
    output_file = f"{get_config_folder()}/{out_file}.out"
    if not os.path.exists(output_file):
        # initialize file if it doesn't exist
        with open(output_file, "w") as f:
            f.write("")
    fout = open(output_file, "w")

    process = subprocess.Popen(
        to_run, stdout=fout, stderr=subprocess.STDOUT, close_fds=True
    )

    # check if server actually started up correctly
    time.sleep(0.5)
    if process.poll() is not None:
        with open(output_file) as f:
            click.echo(f.read())
        raise SidechainCLIException("Process did not start up correctly.")

    return process.pid, output_file


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
    "-v",
    "--verbose",
    is_flag=True,
    help="Whether or not to print more verbose information.",
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

    Raises:
        SidechainCLIException: If server is already running with that name/config.
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
        raise SidechainCLIException("Server already running with that name or config.")

    server_type = "rippled" if is_rippled else "witness"
    if verbose:
        click.echo(f"Starting {server_type} server {name}...")

    if exe == "docker":
        to_run = ["docker", "compose", "-f", _DOCKER_COMPOSE_FILE, "up", name]
    elif is_rippled:
        to_run = [exe, "--conf", config, "-a"]
    else:
        to_run = [exe, "--config", config, "--verbose"]

    pid, output_file = _run_process(to_run, name)

    if is_rippled:
        chain_data: ChainData = {
            "name": name,
            "type": "rippled",
            "exe": exe,
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
            "exe": exe,
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
@click.option("--docker", is_flag=True, help="Use executables from Docker.")
@click.option("--rippled-only", is_flag=True, help="Only start up the rippled servers.")
@click.option("--witness-only", is_flag=True, help="Only start up the witness servers.")
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Whether or not to print more verbose information.",
)
@click.pass_context
def start_all_servers(
    ctx: click.Context,
    config_dir: str,
    rippled_exe: str,
    witnessd_exe: str,
    docker: bool = False,
    rippled_only: bool = False,
    witness_only: bool = False,
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
        docker: Use executables from Docker.
        rippled_only: Only start up the rippled servers.
        witness_only: Only start up the witness servers.
        verbose: Whether or not to print more verbose information.

    Raises:
        SidechainCLIException: If `config_dir` is not a directory.
    """  # noqa: D301
    if not os.path.isdir(config_dir):
        raise SidechainCLIException(f"{config_dir} is not a directory.")
    if not rippled_only and not witness_only:
        all_chains = True
    else:
        all_chains = False
    if docker:
        rippled_exe = "docker"
        witnessd_exe = "docker"

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
    if rippled_only or all_chains:
        if rippled_exe == "docker":
            to_run = [
                "docker",
                "compose",
                "-f",
                _DOCKER_COMPOSE_FILE,
                "up",
            ]
            name_list = [name for (name, _) in chains]
            to_run.extend(name_list)

            pid, output_file = _run_process(to_run, name)

            for name, config in chains:
                config_object = RippledConfig(file_name=config)
                chain_data: ChainData = {
                    "name": name,
                    "type": "rippled",
                    "exe": "docker",
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
            for name, config in chains:
                ctx.invoke(
                    start_server,
                    name=name,
                    exe=rippled_exe,
                    config=config,
                    verbose=verbose,
                )
    if witness_only or all_chains:
        if witnessd_exe == "docker":
            to_run = [
                "docker",
                "compose",
                "-f",
                _DOCKER_COMPOSE_FILE,
                "up",
            ]
            name_list = [name for (name, _) in witnesses]
            to_run.extend(name_list)

            pid, output_file = _run_process(to_run, name)

            for name, config in witnesses:
                with open(config) as f:
                    config_json = json.load(f)
                witness_data: WitnessData = {
                    "name": name,
                    "type": "witness",
                    "exe": "docker",
                    "config": config,
                    "pid": pid,
                    "ip": config_json["RPCEndpoint"]["IP"],
                    "rpc_port": config_json["RPCEndpoint"]["Port"],
                }
                # add witness to config file
                add_witness(witness_data)
        else:
            for name, config in witnesses:
                ctx.invoke(
                    start_server,
                    name=name,
                    exe=witnessd_exe,
                    config=config,
                    verbose=verbose,
                )


@click.command(name="stop")
@click.option("--name", help="The name of the server to stop.")
@click.option(
    "--all", "stop_all", is_flag=True, help="Whether to stop all of the servers."
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Whether or not to print more verbose information.",
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

    Raises:
        SidechainCLIException: If neither a name or `--all` is specified.
    """  # noqa: D301
    if name is None and stop_all is False:
        raise SidechainCLIException("Must specify a name or `--all`.")
    config = get_config()
    if stop_all:
        servers = cast(List[ServerConfig], config.witnesses) + cast(
            List[ServerConfig], config.chains
        )
    else:
        assert name is not None
        servers = [config.get_server(name)]
    if verbose:
        server_names = ",".join([server.name for server in servers])
        click.echo(f"Shutting down: {server_names}")

    # fout = open(os.devnull, "w")
    for server in servers:
        if server.is_docker():
            to_run = [
                "docker",
                "compose",
                "-f",
                _DOCKER_COMPOSE_FILE,
                "stop",
                server.name,
            ]
            subprocess.run(to_run, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif isinstance(server, ChainConfig):
            # TODO: stop the rippled server with a CLI command
            # to_run = [server.rippled, "--conf", server.config, "stop"]
            # subprocess.call(to_run, stdout=fout, stderr=subprocess.STDOUT)
            pid = server.pid
            try:
                os.kill(pid, signal.SIGINT)
            except ProcessLookupError:
                pass  # process already died somehow
        else:
            # TODO: stop the witnessd server with a CLI command
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
    "-v",
    "--verbose",
    is_flag=True,
    help="Whether or not to print more verbose information.",
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

    Raises:
        SidechainCLIException: If neither a name or `--all` is specified.
    """  # noqa: D301
    if name is None and restart_all is False:
        raise SidechainCLIException("Must specify a name or `--all`.")

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
        if server.is_docker():
            subprocess.run(
                [
                    "docker",
                    "compose",
                    "-f",
                    _DOCKER_COMPOSE_FILE,
                    "start",
                    server.name,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            ctx.invoke(
                start_server,
                name=server.name,
                exe=server.exe,
                config=server.config,
                verbose=verbose,
            )
