"""Generate config files."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Type

import click
from jinja2 import Environment, FileSystemLoader

JINJA_ENV = Environment(
    loader=FileSystemLoader(searchpath="./sidechain_cli/config/templates")
)

NODE_SIZE = "medium"


class Ports:
    """
    Port numbers for various services.
    Port numbers differ by cfg_index so different configs can run
    at the same time without interfering with each other.
    """

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


def _generate_template(
    template_name: str, template_data: Dict[str, Any], filename: str
) -> None:
    template = JINJA_ENV.get_template(template_name)

    # add the rippled.cfg file
    with open(filename, "w") as f:
        f.write(template.render(template_data))


# generate a standalone rippled.cfg file
def _generate_standalone_config(
    *,
    ports: Ports,
    with_shards: bool = False,
    cfg_type: str,
    data_dir: str,
    full_history: bool = False,
) -> None:
    sub_dir = f"{data_dir}/{cfg_type}"

    for path in ["", "/db", "/shards"]:
        Path(sub_dir + path).mkdir(parents=True, exist_ok=True)

    template_data = {
        "sub_dir": sub_dir,
        "full_history": full_history,
        # ports stanza
        "ports": ports.to_dict(),
        # other
        "node_size": NODE_SIZE,
        "with_shards": with_shards,
    }

    # add the rippled.cfg file
    _generate_template(
        "standalone.jinja",
        template_data,
        os.path.join(sub_dir, "rippled.cfg"),
    )


def generate_rippled_configs(
    data_dir: str,
    number: int = 2,
) -> None:
    """
    Generate the rippled config files.

    Args:
        data_dir: The directory to use for the config files.
        number: The number of rippled configs to generate.
    """
    for i in range(number):
        ports = Ports.generate(number)
        _generate_standalone_config(
            ports=ports, cfg_type=f"rippled{i}", data_dir=data_dir
        )


if __name__ == "__main__":

    @click.command()
    @click.option(
        "--data_dir", required=True, help="The folder in which to store config files."
    )
    @click.option(
        "--number", required=True, help="The number of rippled configs to generate."
    )
    def main(data_dir: str, number: str) -> None:
        """
        Generate the config files.

        Args:
            data_dir: The directory to use for the config files.
            number: The number of rippled configs to generate.
        """
        generate_rippled_configs(data_dir, int(number))

    main()
