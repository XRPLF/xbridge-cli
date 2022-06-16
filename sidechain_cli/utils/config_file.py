"""ConfigFile helper class."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple, Type, TypeVar

from xrpl.clients import JsonRpcClient

from sidechain_cli.utils.types import Currency

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

T = TypeVar("T", bound="ConfigItem")


class ConfigItem:
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        return cls(**data)


@dataclass
class ChainConfig(ConfigItem):
    name: str
    rippled: str
    config: str
    pid: int
    ws_ip: str
    ws_port: int
    http_ip: str
    http_port: int

    def get_client(self: ChainConfig) -> JsonRpcClient:
        return JsonRpcClient(f"http://{self.http_ip}:{self.http_port}")


@dataclass
class WitnessConfig(ConfigItem):
    name: str
    witnessd: str
    config: str
    pid: int
    ip: str
    rpc_port: int


@dataclass
class BridgeConfig(ConfigItem):
    name: str
    chains: Tuple[str, str]
    witnesses: List[str]
    door_accounts: Tuple[str, str]
    xchain_currencies: Tuple[Currency, Currency]


class ConfigFile:
    """Helper class for working with the config file."""

    def __init__(self: ConfigFile, data: Dict[str, Any]) -> None:
        """
        Initialize a ConfigFile object.

        Args:
            data: The dictionary with the config data.
        """
        self.chains = [ChainConfig.from_dict(chain) for chain in data["chains"]]
        self.witnesses = [
            WitnessConfig.from_dict(witness) for witness in data["witnesses"]
        ]
        self.bridges = [BridgeConfig.from_dict(bridge) for bridge in data["bridges"]]

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
            Exception: if there is no chain with that name.
        """
        for chain in self.chains:
            if chain.name == name:
                return chain
        raise Exception(f"No chain with name {name}.")

    def get_witness(self: ConfigFile, name: str) -> WitnessConfig:
        """
        Get the witness corresponding to the name.

        Args:
            name: The name of the witness.

        Returns:
            The WitnessConfig object corresponding to that witness.

        Raises:
            Exception: if there is no witness with that name.
        """
        for witness in self.witnesses:
            if witness.name == name:
                return witness
        raise Exception(f"No witness with name {name}.")

    def get_bridge(self: ConfigFile, name: str) -> BridgeConfig:
        """
        Get the bridge corresponding to the name.

        Args:
            name: The name of the bridge.

        Returns:
            The BridgeConfig object corresponding to that bridge.

        Raises:
            Exception: if there is no bridge with that name.
        """
        for bridge in self.bridges:
            if bridge.name == name:
                return bridge
        raise Exception(f"No bridge with name {name}.")

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
