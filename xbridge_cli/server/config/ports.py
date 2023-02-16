"""Port numbers for various services."""

from __future__ import annotations

from typing import Dict, Type


class Ports:
    """
    Port numbers for various services.
    Port numbers differ by cfg_index so different configs can run
    at the same time without interfering with each other.
    """

    # TODO: somehow keep track of ports in the CLI config file

    peer_port_base = 51235
    http_admin_port_base = 5005
    ws_public_port_base = 6005

    def __init__(
        self: Ports,
        peer_port: int,
        http_admin_port: int,
        ws_public_port: int,
        ws_admin_port: int,
    ) -> None:
        """
        Initialize a Ports.

        Args:
            peer_port: The peer port of the node. Only needed for a local node.
            http_admin_port: The admin HTTP port of the node. Only needed for a local
                node.
            ws_public_port: The public WS port of the node.
            ws_admin_port: The admin WS port of the node. Only needed for a local node.
        """
        self.peer_port = peer_port
        self.http_admin_port = http_admin_port
        self.ws_public_port = ws_public_port
        self.ws_admin_port = ws_admin_port

    @classmethod
    def generate(cls: Type[Ports], cfg_index: int) -> Ports:
        """
        Generate a Ports with the given config index.

        Args:
            cfg_index: The port number the set of ports should start at.

        Returns:
            A Ports with the ports all set up based on the config index.
        """
        return cls(
            Ports.peer_port_base + cfg_index,
            Ports.http_admin_port_base + cfg_index,
            Ports.ws_public_port_base + (2 * cfg_index),
            # note admin port uses public port base
            Ports.ws_public_port_base + (2 * cfg_index) + 1,
        )

    def to_dict(self: Ports) -> Dict[str, int]:
        """
        Convert the Ports to a dictionary.

        Returns:
            The ports represented by the Ports, in dictionary form.
        """
        return {
            "peer_port": self.peer_port,
            "http_admin_port": self.http_admin_port,
            "ws_public_port": self.ws_public_port,
            "ws_admin_port": self.ws_admin_port,
        }
