"""Server information stored in the CLI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Union

from sidechain_cli.utils.config_file.config_item import ConfigItem


@dataclass
class ServerConfig(ConfigItem):
    """Object representing the config for a server (chain/witness)."""

    name: str
    type: Union[Literal["rippled"], Literal["witness"]]
    pid: int
    exe: str
    config: str
    http_ip: str
    http_port: int

    def is_docker(self: ServerConfig) -> bool:
        """
        Return whether the server is running on docker.

        Returns:
            Whether the server is running on docker.
        """
        return self.exe == "docker"
