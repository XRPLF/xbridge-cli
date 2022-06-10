"""Utils for working with the config file."""

from sidechain_cli.utils.config_file import ConfigFile
from sidechain_cli.utils.types import ChainData


def _get_config() -> ConfigFile:
    return ConfigFile.from_file()


def add_chain(chain_data: ChainData) -> None:
    """
    Add a chain's data to the config file.

    Args:
        chain_data: The data of the chain to add.
    """
    conf = _get_config()
    conf.chains.append(chain_data)
    conf.write_to_file()
