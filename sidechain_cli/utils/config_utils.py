"""Utils for working with the config file."""

from typing import Optional

from sidechain_cli.utils.config_file import ConfigFile
from sidechain_cli.utils.types import ChainData


def get_config() -> ConfigFile:
    """
    Get the config file.

    Returns:
        The config file, as a ConfigFile object.
    """
    return ConfigFile.from_file()


def add_chain(chain_data: ChainData) -> None:
    """
    Add a chain's data to the config file.

    Args:
        chain_data: The data of the chain to add.
    """
    conf = get_config()
    conf.chains.append(chain_data)
    conf.write_to_file()


def check_chain_exists(chain_name: str, chain_config: str) -> bool:
    """
    Check if a chain with a given name or config is already running.

    Args:
        chain_name: The name of the chain to check.
        chain_config: The name of the config to check.

    Returns:
        Whether there is already a chain running with that name or config.
    """
    conf = get_config()
    for chain in conf.chains:
        if chain["name"] == chain_name:
            return True
        if chain["config"] == chain_config:
            return True
    return False


def remove_chain(name: Optional[str] = None, remove_all: bool = False) -> None:
    """
    Remove a chain's data to the config file.

    Args:
        name: The data of the chain to remove.
        remove_all: Whether to remove all of the chains.

    Raises:
        Exception: If `name` is `None` and `remove_all` is `False`.
    """
    if name is None and remove_all is False:
        raise Exception(
            "Cannot remove chain if name is `None` and remove_all is `False`."
        )
    conf = get_config()
    if remove_all:
        conf.chains = []
    else:
        conf.chains = [chain for chain in conf.chains if chain["name"] != name]
    conf.write_to_file()
