"""Restart a server/servers."""

from __future__ import annotations

import subprocess
from typing import List, Optional, cast

import click

from xbridge_cli.exceptions import XBridgeCLIException
from xbridge_cli.server.start import _DOCKER_COMPOSE, start_server
from xbridge_cli.server.stop import stop_server
from xbridge_cli.utils import ServerConfig, get_config


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
        XBridgeCLIException: If neither a name or `--all` is specified.
    """  # noqa: D301
    if name is None and restart_all is False:
        raise XBridgeCLIException("Must specify a name or `--all`.")

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
                [*_DOCKER_COMPOSE, "start", server.name],
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
