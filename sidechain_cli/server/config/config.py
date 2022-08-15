"""Generate config files."""

from __future__ import annotations

import os
from pathlib import Path
from pprint import pprint
from sys import platform
from typing import Any, Dict, Tuple

import click
from jinja2 import Environment, FileSystemLoader
from xrpl import CryptoAlgorithm
from xrpl.wallet import Wallet

from sidechain_cli.server.config.ports import Ports

JINJA_ENV = Environment(
    loader=FileSystemLoader(
        searchpath=os.path.join(*os.path.split(__file__)[:-1], "templates")
    )
)


# render a Jinja template and dump it into a file
def _generate_template(
    template_name: str, template_data: Dict[str, Any], filename: str
) -> None:
    template = JINJA_ENV.get_template(template_name)

    with open(filename, "w") as f:
        f.write(template.render(template_data))


# generate a standalone rippled.cfg file
def _generate_standalone_config(
    *,
    ports: Ports,
    cfg_type: str,
    config_dir: str,
) -> None:
    abs_config_dir = os.path.abspath(config_dir)
    sub_dir = f"{abs_config_dir}/{cfg_type}"

    for path in ["", "/db"]:
        Path(sub_dir + path).mkdir(parents=True, exist_ok=True)

    template_data = {
        "sub_dir": sub_dir,
        "ports": ports.to_dict(),
    }

    # add the rippled.cfg file
    _generate_template(
        "rippled.jinja",
        template_data,
        os.path.join(sub_dir, "rippled.cfg"),
    )


def _generate_rippled_configs(config_dir: str) -> Tuple[int, int]:
    """
    Generate the rippled config files.

    Args:
        config_dir: The directory to use for the config files.

    Returns:
        The locking chain and issuing chain WS ports.
    """
    locking_ports = Ports.generate(0)
    _generate_standalone_config(
        ports=locking_ports, cfg_type="mainchain", config_dir=config_dir
    )

    issuing_ports = Ports.generate(1)
    _generate_standalone_config(
        ports=issuing_ports, cfg_type="sidechain", config_dir=config_dir
    )

    return locking_ports.ws_public_port, issuing_ports.ws_public_port


@click.command(name="witness")
@click.option(
    "--config_dir",
    required=True,
    prompt=True,
    help="The folder in which to store config files.",
)
@click.option(
    "--name",
    required=True,
    prompt=True,
    help="The name of the witness server.",
)
@click.option(
    "--mc_port",
    "mainchain_port",
    required=True,
    prompt=True,
    type=int,
    help="The port used by the mainchain.",
)
@click.option(
    "--sc_port",
    "sidechain_port",
    required=True,
    prompt=True,
    type=int,
    help="The port used by the sidechain.",
)
@click.option(
    "--witness_port",
    required=True,
    prompt=True,
    type=int,
    help="The port that will be used by the witness server.",
)
@click.option(
    "--src_door",
    required=True,
    prompt=True,
    help="The door account on the source chain.",
)
@click.option(
    "--dst_door",
    default="rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
    help="The door account on the destination chain. Defaults to the genesis account.",
)
@click.option(
    "--verbose", is_flag=True, help="Whether or not to print more verbose information."
)
def generate_witness_config(
    config_dir: str,
    name: str,
    mainchain_port: int,
    sidechain_port: int,
    witness_port: int,
    src_door: str,
    dst_door: str = "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
    verbose: bool = False,
) -> None:
    """
    Generate a witness config file.

    Args:
        config_dir: The folder in which to store config files.
        name: The name of the witness server.
        mainchain_port: The port used by the mainchain.
        sidechain_port: The port used by the sidechain.
        witness_port: The port that will be used by the witness server.
        src_door: The door account on the source chain.
        dst_door: The door account on the destination chain. Defaults to the genesis
            account.
        verbose: Whether or not to print more verbose information.
    """
    abs_config_dir = os.path.abspath(config_dir)
    sub_dir = f"{abs_config_dir}/{name}"
    for path in ["", "/db"]:
        Path(sub_dir + path).mkdir(parents=True, exist_ok=True)

    template_data = {
        "mainchain_port": mainchain_port,
        "sidechain_port": sidechain_port,
        "witness_port": witness_port,
        "db_dir": f"{sub_dir}/db",
        "seed": Wallet.create(CryptoAlgorithm.SECP256K1).seed,
        "src_door": src_door,
        "src_issue": "XRP",
        "dst_door": dst_door,
        "dst_issue": "XRP",
        "is_linux": platform == "linux" or platform == "linux2",
    }
    # add the witness.json file
    _generate_template(
        "witness.jinja",
        template_data,
        os.path.join(sub_dir, "witness.json"),
    )


@click.command(name="bootstrap")
@click.option(
    "--config_dir",
    required=True,
    prompt=True,
    help="The folder in which to store config files.",
)
@click.option(
    "--mc_seed",
    "mainchain_seed",
    required=True,
    prompt=True,
    help="The seed of the mainchain door account.",
)
@click.option(
    "--sc_seed",
    "sidechain_seed",
    default="snoPBrXtMeMyMHUVTgbuqAfg1SUTb",
    help="The seed of the sidechain door account. Defaults to the genesis account.",
)
@click.option(
    "--verbose", is_flag=True, help="Whether or not to print more verbose information."
)
def generate_bootstrap(
    config_dir: str, mainchain_seed: str, sidechain_seed: str, verbose: bool = False
) -> None:
    """
    Generate a bootstrap config file. Used by the scripts to initialize the bridge.

    Args:
        config_dir: The folder in which to store config files.
        mainchain_seed: The seed of the mainchain door account.
        sidechain_seed: The seed of the sidechain door account. Defaults to the genesis
            account.
        verbose: Whether or not to print more verbose information.
    """
    mainchain_door = Wallet(mainchain_seed, 0)
    sidechain_door = Wallet(sidechain_seed, 0)

    template_data = {
        "mainchain_id": mainchain_door.classic_address,
        "mainchain_seed": mainchain_door.seed,
        "sidechain_id": sidechain_door.classic_address,
        "sidechain_seed": sidechain_door.seed,
    }
    if verbose:
        pprint(template_data)

    _generate_template(
        "bootstrap.jinja",
        template_data,
        os.path.join(config_dir, "bridge_bootstrap.json"),
    )


@click.command(name="all")
@click.option(
    "--config_dir",
    envvar="XCHAIN_CONFIG_DIR",
    required=True,
    prompt=True,
    type=click.Path(),
    help="The folder in which to store config files.",
)
@click.option(
    "--num_witnesses",
    default=5,
    type=int,
    help="The number of witness configs to generate.",
)
@click.option(
    "--verbose", is_flag=True, help="Whether or not to print more verbose information."
)
@click.pass_context
def generate_all_configs(
    ctx: click.Context, config_dir: str, num_witnesses: int = 5, verbose: bool = False
) -> None:
    """
    Generate the rippled and witness configs.

    Args:
        ctx: The click context.
        config_dir: The directory to use for the config files.
        num_witnesses: The number of witnesses configs to generate.
        verbose: Whether or not to print more verbose information.
    """
    # TODO: add support for external networks
    abs_config_dir = os.path.abspath(config_dir)
    mc_port, sc_port = _generate_rippled_configs(abs_config_dir)
    src_door = Wallet.create(CryptoAlgorithm.SECP256K1)
    for i in range(num_witnesses):
        ctx.invoke(
            generate_witness_config,
            config_dir=abs_config_dir,
            name=f"witness{i}",
            mainchain_port=mc_port,
            sidechain_port=sc_port,
            witness_port=6010 + i,
            src_door=src_door.classic_address,
        )
    ctx.invoke(
        generate_bootstrap,
        config_dir=abs_config_dir,
        mainchain_seed=src_door.seed,
        verbose=verbose,
    )
