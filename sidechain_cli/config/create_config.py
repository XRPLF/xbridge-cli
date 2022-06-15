"""Generate config files."""

from __future__ import annotations

import os
from pathlib import Path
from sys import platform
from typing import Any, Dict, Optional, Tuple, Type

import click
from jinja2 import Environment, FileSystemLoader
from xrpl import CryptoAlgorithm
from xrpl.wallet import Wallet

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


def _generate_rippled_configs(data_dir: str) -> Tuple[int, int]:
    """
    Generate the rippled config files.

    Args:
        data_dir: The directory to use for the config files.

    Returns:
        The mainchain and sidechain WS ports.
    """
    mainchain_ports = Ports.generate(0)
    _generate_standalone_config(
        ports=mainchain_ports, cfg_type="mainchain", data_dir=data_dir
    )

    sidechain_ports = Ports.generate(1)
    _generate_standalone_config(
        ports=sidechain_ports, cfg_type="sidechain", data_dir=data_dir
    )

    return mainchain_ports.ws_public_port, sidechain_ports.ws_public_port


def _generate_witness_config(
    data_dir: str,
    mainchain_port: int,
    sidechain_port: int,
    witness_number: int,
    src_door: str,
) -> None:
    sub_dir = f"{data_dir}/witness{witness_number}"
    for path in ["", "/db"]:
        Path(sub_dir + path).mkdir(parents=True, exist_ok=True)

    template_data = {
        "mainchain_port": mainchain_port,
        "sidechain_port": sidechain_port,
        "witness_port": 6010 + witness_number,
        "db_dir": f"{sub_dir}/db",
        "seed": Wallet.create(CryptoAlgorithm.SECP256K1).seed,
        "src_door": src_door,
        "src_issue": "XRP",
        "dst_door": "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
        "dst_issue": "XRP",
        "is_linux": platform == "linux" or platform == "linux2",
    }
    # add the witness.json file
    _generate_template(
        "witness.jinja",
        template_data,
        os.path.join(sub_dir, "witness.json"),
    )


def _generate_bootstrap(data_dir: str, src_door: Wallet) -> None:
    template_data = {
        "mainchain_id": src_door.classic_address,
        "mainchain_seed": src_door.seed,
        "sidechain_id": "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
        "sidechain_seed": "snoPBrXtMeMyMHUVTgbuqAfg1SUTb",
    }
    _generate_template(
        "bootstrap.jinja",
        template_data,
        os.path.join(data_dir, "bridge_bootstrap.json"),
    )


def generate_all_configs(data_dir: str, num_witnesses: int = 5) -> None:
    """
    Generate the rippled and witness configs.

    Args:
        data_dir: The directory to use for the config files.
        num_witnesses: The number of witnesses configs to generate.
    """
    mc_port, sc_port = _generate_rippled_configs(data_dir)
    src_door = Wallet.create()
    for i in range(num_witnesses):
        _generate_witness_config(
            data_dir, mc_port, sc_port, i, src_door.classic_address
        )
    _generate_bootstrap(data_dir, src_door)


if __name__ == "__main__":

    @click.command()
    @click.option(
        "--data_dir", required=True, help="The folder in which to store config files."
    )
    @click.option("--num_witnesses", help="The number of witness configs to generate.")
    def main(data_dir: str, num_witnesses: Optional[str]) -> None:
        """
        Generate the config files.

        Args:
            data_dir: The directory to use for the config files.
            num_witnesses: The number of witnesses configs to generate.
        """
        generate_all_configs(
            data_dir, int(num_witnesses) if num_witnesses is not None else 5
        )

    main()
