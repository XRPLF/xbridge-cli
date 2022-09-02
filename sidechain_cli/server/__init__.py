"""Subcommand for all commands dealing with rippled nodes."""

import click

from sidechain_cli.server.config import create_server_configs
from sidechain_cli.server.list import list_servers
from sidechain_cli.server.print import print_server_output
from sidechain_cli.server.request import get_server_status, request_server
from sidechain_cli.server.start import (
    restart_server,
    start_all_servers,
    start_server,
    stop_server,
)


@click.group()
def server() -> None:
    """Subcommand for all commands dealing with rippled and witness servers."""
    pass


server.add_command(start_server, name="start")
server.add_command(start_all_servers, name="start-all")
server.add_command(stop_server, name="stop")
server.add_command(restart_server, name="restart")

server.add_command(create_server_configs, name="create-config")

server.add_command(list_servers, name="list")
server.add_command(print_server_output, name="print")

server.add_command(get_server_status, name="status")
server.add_command(request_server, name="request")

__all__ = ["server"]
