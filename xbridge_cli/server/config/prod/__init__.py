"""Subcommand for all commands dealing with production server config file generation."""

import click

from xbridge_cli.server.config.prod.bootstrap import (
    combine_bootstrap_pieces,
    get_bootstrap_piece_from_witness,
)
from xbridge_cli.server.config.prod.witness import generate_prod_witness_config


@click.group(name="prod")
def create_prod_server_configs() -> None:
    """Subcommand for production server config file generation."""
    pass


create_prod_server_configs.add_command(generate_prod_witness_config, name="witness")
create_prod_server_configs.add_command(
    get_bootstrap_piece_from_witness, name="bootstrap"
)
create_prod_server_configs.add_command(combine_bootstrap_pieces, name="combine")

__all__ = ["create_prod_server_configs"]
