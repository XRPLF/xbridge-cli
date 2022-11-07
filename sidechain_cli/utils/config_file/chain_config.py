"""Chain information stored in the CLI."""

from __future__ import annotations

from dataclasses import dataclass

from xrpl.clients import JsonRpcClient

from sidechain_cli.utils.config_file.server_config import ServerConfig
from sidechain_cli.utils.rippled_config import RippledConfig


@dataclass
class ChainConfig(ServerConfig):
    """Object representing the config for a chain."""

    ws_ip: str
    ws_port: int

    @property
    def rippled(self: ChainConfig) -> str:
        """
        Get the rippled executable. Alias for `self.exe`.

        Returns:
            `self.exe`.
        """
        return self.exe

    def get_client(self: ChainConfig) -> JsonRpcClient:
        """
        Get a client connected to the chain. Requires that the chain be running.

        Returns:
            A JsonRpcClient that is connected to this chain.
        """
        return JsonRpcClient(f"http://{self.http_ip}:{self.http_port}")

    def get_config(self: ChainConfig) -> RippledConfig:
        """
        Get the config file for this chain.

        Returns:
            The RippledConfig object for this config file.
        """
        return RippledConfig(file_name=self.config)
