"""Subcommand for all commands dealing with node config file generation."""

import click

from sidechain_cli.create_config.config import generate_all_configs


@click.group(name="create-config")
def create_config() -> None:
    """Subcommand for all commands dealing with node config file generation."""
    pass


create_config.add_command(generate_all_configs, name="all")

__all__ = ["create_config"]
