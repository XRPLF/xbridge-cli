"""Subcommand for all commands dealing with server config file generation."""

import click

from xbridge_cli.server.config.config import (
    generate_all_configs,
    generate_bootstrap,
    generate_witness_config,
)
from xbridge_cli.server.config.prod_config import generate_prod_witness_config


@click.group(name="prod")
def create_prod_server_configs() -> None:
    """Subcommand for production server config file generation."""
    pass


create_prod_server_configs.add_command(generate_prod_witness_config, name="witness")


@click.group(name="create-config")
def create_server_configs() -> None:
    """Subcommand for server config file generation."""
    pass


create_server_configs.add_command(generate_all_configs, name="all")
create_server_configs.add_command(generate_bootstrap, name="bootstrap")
create_server_configs.add_command(generate_witness_config, name="witness")
create_server_configs.add_command(create_prod_server_configs, name="prod")

__all__ = ["create_server_configs"]
