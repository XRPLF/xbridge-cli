"""Utils for working with the config file."""

from typing import Any, Dict

from sidechain_cli.utils.config_file import ConfigFile


def _get_config() -> ConfigFile:
    return ConfigFile.from_file()


def add_chain(chain_data: Dict[str, Any]) -> None:
    """
    Add a chain's data to the config file.

    Args:
        chain_data: The data of the chain to add.
    """
    conf = _get_config()
    conf.chains.append(chain_data)
    conf.write_to_file()
