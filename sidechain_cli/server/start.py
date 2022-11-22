"""CLI functions for starting/stopping a rippled node."""

from __future__ import annotations

import json
import os
import subprocess
import time
from typing import List, Tuple

import click
import httpx

import docker
from sidechain_cli.exceptions import SidechainCLIException
from sidechain_cli.utils import (
    ChainData,
    RippledConfig,
    WitnessData,
    add_chain,
    add_witness,
    check_server_exists,
    get_config_folder,
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

_DOCKER_COMPOSE = ["docker", "compose", "-f", _DOCKER_COMPOSE_FILE]

_START_UP_TIME = 10  # seconds
_WAIT_INCREMENT = 0.5  # seconds


def _wait_for_process(
    process: subprocess.Popen[bytes],
    name: str,
    http_ip: str,
    http_port: int,
    output_file: str,
    is_docker: bool = False,
) -> None:
    http_url = f"http://{http_ip}:{http_port}"
    time_waited = 0.0
    while time_waited < _START_UP_TIME:
        try:
            request = {"method": "server_info"}
            httpx.post(http_url, json=request)
            if is_docker:
                docker_client = docker.from_env()
                container = docker_client.containers.get(name)
                assert container.status == "running"
            return
        except (
            httpx.ConnectError,
            httpx.RemoteProtocolError,
            httpx.ReadError,
            httpx.WriteError,
            docker.errors.NotFound,
            AssertionError,
        ):
            time.sleep(_WAIT_INCREMENT)
            time_waited += _WAIT_INCREMENT
    with open(output_file) as f:
        click.echo(f.read())
    raise SidechainCLIException("Process did not start up correctly.")


def _run_process(
    to_run: List[str], out_file: str
) -> Tuple[subprocess.Popen[bytes], str]:
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

    return process, output_file


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
@click.pass_context
def start_server(
    ctx: click.Context, name: str, exe: str, config: str, verbose: bool = False
) -> None:
    """
    Start a standalone node of rippled or a witness node.
    \f

    Args:
        ctx: The click context.
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
        to_run = [*_DOCKER_COMPOSE, "up", name]
    elif is_rippled:
        to_run = [exe, "--conf", config, "-a"]
    else:
        to_run = [exe, "--conf", config, "--verbose"]

    process, output_file = _run_process(to_run, name)

    if is_rippled:
        # check if server actually started up correctly
        _wait_for_process(
            process,
            name,
            config_object.port_rpc_admin_local.ip,
            int(config_object.port_rpc_admin_local.port),
            output_file,
            exe == "docker",
        )

        chain_data: ChainData = {
            "name": name,
            "type": "rippled",
            "exe": exe,
            "config": config,
            "pid": process.pid,
            "ws_ip": config_object.port_ws_admin_local.ip,
            "ws_port": int(config_object.port_ws_admin_local.port),
            "http_ip": config_object.port_rpc_admin_local.ip,
            "http_port": int(config_object.port_rpc_admin_local.port),
        }
        # add chain to config file
        add_chain(chain_data)
    else:
        # check if server actually started up correctly
        _wait_for_process(
            process,
            name,
            config_json["RPCEndpoint"]["IP"],
            config_json["RPCEndpoint"]["Port"],
            output_file,
            exe == "docker",
        )
        witness_data: WitnessData = {
            "name": name,
            "type": "witness",
            "exe": exe,
            "config": config,
            "pid": process.pid,
            "http_ip": config_json["RPCEndpoint"]["IP"],
            "http_port": config_json["RPCEndpoint"]["Port"],
        }
        # add witness to config file
        add_witness(witness_data)

    if verbose:
        click.echo(f"started {server_type} at `{exe}` with config `{config}`")
        click.echo(f"PID: {process.pid}")


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
            name_list = [name for (name, _) in chains]
            to_run = [*_DOCKER_COMPOSE, "up", *name_list]

            process, output_file = _run_process(to_run, "docker-rippled")

            for name, config in chains:
                config_object = RippledConfig(file_name=config)
                # check if server actually started up correctly
                _wait_for_process(
                    process,
                    name,
                    config_object.port_rpc_admin_local.ip,
                    int(config_object.port_rpc_admin_local.port),
                    output_file,
                    rippled_exe == "docker",
                )
                chain_data: ChainData = {
                    "name": name,
                    "type": "rippled",
                    "exe": "docker",
                    "config": config,
                    "pid": process.pid,
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
            name_list = [name for (name, _) in witnesses]
            to_run = [*_DOCKER_COMPOSE, "up", *name_list]

            process, output_file = _run_process(to_run, "docker-witness")

            for name, config in witnesses:
                with open(config) as f:
                    config_json = json.load(f)

                # check if server actually started up correctly
                _wait_for_process(
                    process,
                    name,
                    config_json["RPCEndpoint"]["IP"],
                    config_json["RPCEndpoint"]["Port"],
                    output_file,
                    witnessd_exe == "docker",
                )

                witness_data: WitnessData = {
                    "name": name,
                    "type": "witness",
                    "exe": "docker",
                    "config": config,
                    "pid": process.pid,
                    "http_ip": config_json["RPCEndpoint"]["IP"],
                    "http_port": config_json["RPCEndpoint"]["Port"],
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
