"""Utils for working with the config file."""

from typing import Any, Dict, Optional, cast

from sidechain_cli.exceptions import SidechainCLIException
from sidechain_cli.utils.config_file import (
    BridgeConfig,
    ChainConfig,
    ConfigFile,
    WitnessConfig,
)
from sidechain_cli.utils.types import BridgeData, ChainData, WitnessData


def get_config() -> ConfigFile:
    """
    Get the config file.

    Returns:
        The config file, as a ConfigFile object.
    """
    return ConfigFile.from_file()


def check_chain_exists(chain_name: str, chain_config: Optional[str] = None) -> bool:
    """
    Check if a chain with a given name or config is already running.

    Args:
        chain_name: The name of the chain to check.
        chain_config: The name of the config to check. Optional.

    Returns:
        Whether there is already a chain running with that name or config.
    """
    conf = get_config()
    for chain in conf.chains:
        if chain.name == chain_name:
            return True
        if chain.config == chain_config:
            return True
    return False


def check_witness_exists(
    witness_name: str, witness_config: Optional[str] = None
) -> bool:
    """
    Check if a witness with a given name or config is already running.

    Args:
        witness_name: The name of the witness to check.
        witness_config: The name of the config to check. Optional.

    Returns:
        Whether there is already a witness running with that name or config.
    """
    conf = get_config()
    for witness in conf.witnesses:
        if witness.name == witness_name:
            return True
        if witness.config == witness_config:
            return True
    return False


def check_bridge_exists(bridge_name: str) -> bool:
    """
    Check if a bridge with a given name is already running.

    Args:
        bridge_name: The name of the bridge to check.

    Returns:
        Whether there is already a bridge running with that name or config.
    """
    conf = get_config()
    for bridge in conf.bridges:
        if bridge.name == bridge_name:
            return True
    return False


def check_server_exists(name: str, config: Optional[str] = None) -> bool:
    """
    Check if a server with a given name or config is already running.

    Args:
        name: The name of the server to check.
        config: The name of the config to check. Optional.

    Returns:
        Whether there is already a server running with that name or config.
    """
    return check_chain_exists(name, config) or check_witness_exists(name, config)


def add_chain(chain_data: ChainData) -> None:
    """
    Add a chain's data to the config file.

    Args:
        chain_data: The data of the chain to add.
    """
    conf = get_config()
    conf.chains.append(ChainConfig.from_dict(cast(Dict[str, Any], chain_data)))
    conf.write_to_file()


def remove_chain(name: Optional[str] = None, remove_all: bool = False) -> None:
    """
    Remove a chain's data to the config file.

    Args:
        name: The data of the chain to remove.
        remove_all: Whether to remove all of the chains.

    Raises:
        SidechainCLIException: If `name` is `None` and `remove_all` is `False`.
    """
    if name is None and remove_all is False:
        raise SidechainCLIException(
            "Cannot remove chain if name is `None` and remove_all is `False`."
        )
    conf = get_config()
    if remove_all:
        conf.chains = []
    else:
        conf.chains = [chain for chain in conf.chains if chain.name != name]
    conf.write_to_file()


def add_witness(witness_data: WitnessData) -> None:
    """
    Add a witness's data to the config file.

    Args:
        witness_data: The data of the witness to add.
    """
    conf = get_config()
    conf.witnesses.append(WitnessConfig.from_dict(cast(Dict[str, Any], witness_data)))
    conf.write_to_file()


def remove_witness(name: Optional[str] = None, remove_all: bool = False) -> None:
    """
    Remove a witness's data to the config file.

    Args:
        name: The data of the witness to remove.
        remove_all: Whether to remove all of the witnesses.

    Raises:
        SidechainCLIException: If `name` is `None` and `remove_all` is `False`.
    """
    if name is None and remove_all is False:
        raise SidechainCLIException(
            "Cannot remove witness if name is `None` and remove_all is `False`."
        )
    conf = get_config()
    if remove_all:
        conf.witnesses = []
    else:
        conf.witnesses = [witness for witness in conf.witnesses if witness.name != name]
    conf.write_to_file()


def remove_server(name: Optional[str] = None, remove_all: bool = False) -> None:
    """
    Remove a server's data to the config file.

    Args:
        name: The data of the server to remove.
        remove_all: Whether to remove all of the servers.

    Raises:
        SidechainCLIException: If `name` is `None` and `remove_all` is `False`.
    """
    if name is None and remove_all is False:
        raise SidechainCLIException(
            "Cannot remove server if name is `None` and remove_all is `False`."
        )
    conf = get_config()
    if remove_all:
        conf.chains = []
        conf.witnesses = []
    else:
        assert name is not None
        try:
            conf.get_witness(name)
            conf.witnesses = [
                witness for witness in conf.witnesses if witness.name != name
            ]
        except Exception:
            conf.chains = [chain for chain in conf.chains if chain.name != name]
    conf.write_to_file()


def add_bridge(bridge_data: BridgeData) -> None:
    """
    Add a bridge's data to the config file.

    Args:
        bridge_data: The data of the bridge to add.
    """
    conf = get_config()
    conf.bridges.append(BridgeConfig.from_dict(cast(Dict[str, Any], bridge_data)))
    conf.write_to_file()


def remove_bridge(name: Optional[str] = None, remove_all: bool = False) -> None:
    """
    Remove a bridge's data to the config file.

    Args:
        name: The data of the bridge to remove.
        remove_all: Whether to remove all of the bridges.

    Raises:
        SidechainCLIException: If `name` is `None` and `remove_all` is `False`.
    """
    if name is None and remove_all is False:
        raise SidechainCLIException(
            "Cannot remove bridge if name is `None` and remove_all is `False`."
        )
    conf = get_config()
    if remove_all:
        conf.bridges = []
    else:
        conf.bridges = [bridge for bridge in conf.bridges if bridge.name != name]
    conf.write_to_file()
