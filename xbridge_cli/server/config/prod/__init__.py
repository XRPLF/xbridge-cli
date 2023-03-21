"""Subcommand for all commands dealing with production server config file generation."""

import click

from xbridge_cli.server.config.prod.witness import generate_prod_witness_config


@click.group(name="prod")
def create_prod_server_configs() -> None:
    """Subcommand for production server config file generation."""
    pass


create_prod_server_configs.add_command(generate_prod_witness_config, name="witness")

__all__ = ["create_prod_server_configs"]
