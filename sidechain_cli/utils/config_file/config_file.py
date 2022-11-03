"""ConfigFile helper class."""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Type

import httpx

from sidechain_cli.exceptions import SidechainCLIException
from sidechain_cli.utils.config_file.bridge_config import BridgeConfig
from sidechain_cli.utils.config_file.chain_config import ChainConfig
from sidechain_cli.utils.config_file.server_config import ServerConfig
from sidechain_cli.utils.config_file.witness_config import WitnessConfig
from sidechain_cli.utils.types import ServerData

_HOME = str(Path.home())

CONFIG_FOLDER = os.path.join(_HOME, ".config", "sidechain-cli")

# ~/.config/sidechain-cli/config.json
_CONFIG_FILE = os.path.join(CONFIG_FOLDER, "config.json")

# Initialize config file
Path(CONFIG_FOLDER).mkdir(parents=True, exist_ok=True)
if not os.path.exists(_CONFIG_FILE):
    with open(_CONFIG_FILE, "w") as f:
        data: Dict[str, Any] = {"chains": [], "witnesses": [], "bridges": []}
        json.dump(data, f, indent=4)

# TODO: consider having separate JSONs for each node type
# (e.g. chains.json, witnesses.json, bridges.json)


def get_config_folder() -> str:
    """
    Get the folder in which all of the CLI config data is located.

    Returns:
        The full name of the config folder.
    """
    return CONFIG_FOLDER


def _get_running_processes(servers: List[ServerData]) -> List[ServerData]:
    return_list = []
    for server in servers:
        http_url = f"http://{server['http_ip']}:{server['http_port']}"
        try:
            request = {"method": "server_info"}
            httpx.post(http_url, json=request)
            return_list.append(server)
            continue
        except (
            httpx.ConnectError,
            httpx.RemoteProtocolError,
            httpx.ReadError,
            httpx.WriteError,
        ):
            continue
    return return_list


class ConfigFile:
    """Helper class for working with the config file."""

    def __init__(self: ConfigFile, data: Dict[str, Any]) -> None:
        """
        Initialize a ConfigFile object.

        Args:
            data: The dictionary with the config data.
        """
        self.chains = [
            ChainConfig.from_dict(chain)
            for chain in _get_running_processes(data["chains"])
        ]
        self.witnesses = [
            WitnessConfig.from_dict(witness)
            for witness in _get_running_processes(data["witnesses"])
        ]
        self.bridges = [BridgeConfig.from_dict(bridge) for bridge in data["bridges"]]
        self.write_to_file()

    @classmethod
    def from_file(cls: Type[ConfigFile]) -> ConfigFile:
        """
        Initialize a ConfigFile object from a JSON file.

        Returns:
            The ConfigFile object.
        """
        with open(_CONFIG_FILE) as f:
            data = json.load(f)
            return cls(data)

    def get_chain(self: ConfigFile, name: str) -> ChainConfig:
        """
        Get the chain corresponding to the name.

        Args:
            name: The name of the chain.

        Returns:
            The ChainConfig object corresponding to that chain.

        Raises:
            SidechainCLIException: if there is no chain with that name.
        """
        for chain in self.chains:
            if chain.name == name:
                return chain
        raise SidechainCLIException(f"No chain with name {name}.")

    def get_witness(self: ConfigFile, name: str) -> WitnessConfig:
        """
        Get the witness corresponding to the name.

        Args:
            name: The name of the witness.

        Returns:
            The WitnessConfig object corresponding to that witness.

        Raises:
            SidechainCLIException: if there is no witness with that name.
        """
        for witness in self.witnesses:
            if witness.name == name:
                return witness
        raise SidechainCLIException(f"No witness with name {name}.")

    def get_server(self: ConfigFile, name: str) -> ServerConfig:
        """
        Get the server corresponding to the name.

        Args:
            name: The name of the server.

        Returns:
            The ServerConfig object corresponding to that server.

        Raises:
            SidechainCLIException: if there is no server with that name.
        """
        for chain in self.chains:
            if chain.name == name:
                return chain
        for witness in self.witnesses:
            if witness.name == name:
                return witness
        raise SidechainCLIException(f"No server with name {name}.")

    def get_bridge(self: ConfigFile, name: str) -> BridgeConfig:
        """
        Get the bridge corresponding to the name.

        Args:
            name: The name of the bridge.

        Returns:
            The BridgeConfig object corresponding to that bridge.

        Raises:
            SidechainCLIException: if there is no bridge with that name.
        """
        for bridge in self.bridges:
            if bridge.name == name:
                return bridge
        raise SidechainCLIException(f"No bridge with name {name}.")

    def to_dict(self: ConfigFile) -> Dict[str, List[Dict[str, Any]]]:
        """
        Convert a ConfigFile object back to a dictionary.

        Returns:
            A dictionary representing the data in the object.
        """
        return {
            "chains": [asdict(chain) for chain in self.chains],
            "witnesses": [asdict(witness) for witness in self.witnesses],
            "bridges": [asdict(bridge) for bridge in self.bridges],
        }

    def write_to_file(self: ConfigFile) -> None:
        """Write the ConfigFile data to file."""
        with open(_CONFIG_FILE, "w") as f:
            json.dump(self.to_dict(), f, indent=4)
