"""Stop a server/servers."""

from __future__ import annotations

import os
import signal
import subprocess
from typing import List, Optional, cast

import click

from sidechain_cli.exceptions import SidechainCLIException
from sidechain_cli.server.start import _DOCKER_COMPOSE
from sidechain_cli.utils import ChainConfig, ServerConfig, get_config, remove_server


def _pid_is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True


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
        server_names = ", ".join([server.name for server in servers])
        click.echo(f"Shutting down: {server_names}")

    docker_servers = []
    fout = open(os.devnull, "w")
    for server in servers:
        if server.is_docker():
            docker_servers.append(server.name)
        else:
            if isinstance(server, ChainConfig):
                to_run = [server.exe, "--conf", server.config, "stop"]
            else:
                to_run = [server.exe, "--config", server.config, "stop"]

            subprocess.call(to_run, stdout=fout, stderr=subprocess.STDOUT)
            if _pid_is_alive(server.pid):
                if verbose:
                    click.echo(f"Needed to kill {server.name}")
                os.kill(server.pid, signal.SIGINT)
            if verbose:
                click.echo(f"Stopped {server.name}")

    if len(docker_servers) > 0:
        to_run = [*_DOCKER_COMPOSE, "stop", *docker_servers]
        subprocess.run(to_run, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if verbose:
            docker_names = ", ".join([name for name in docker_servers])
            click.echo(f"Stopped {docker_names}")

    remove_server(name, stop_all)
