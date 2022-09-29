"""Generate config files."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from pprint import pformat
from sys import platform
from typing import Any, Dict, List, Tuple

import click
from jinja2 import Environment, FileSystemLoader
from xrpl import CryptoAlgorithm
from xrpl.wallet import Wallet

from sidechain_cli.server.config.ports import Ports

JINJA_ENV = Environment(
    loader=FileSystemLoader(
        searchpath=os.path.join(*os.path.split(__file__)[:-1], "templates")
    ),
    trim_blocks=True,
    lstrip_blocks=True,
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
        dirpath = Path(sub_dir + path)
        if dirpath.exists():
            if dirpath.is_dir():
                shutil.rmtree(dirpath)
            else:
                os.remove(dirpath)
        dirpath.mkdir(parents=True)

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
        ports=locking_ports, cfg_type="locking_chain", config_dir=config_dir
    )

    issuing_ports = Ports.generate(1)
    _generate_standalone_config(
        ports=issuing_ports, cfg_type="issuing_chain", config_dir=config_dir
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
    default="witness",
    help="The name of the witness server. Used for the folder name.",
)
@click.option(
    "--mc_port",
    "locking_chain_port",
    required=True,
    prompt=True,
    type=int,
    help="The port used by the locking chain.",
)
@click.option(
    "--sc_port",
    "issuing_chain_port",
    required=True,
    prompt=True,
    type=int,
    help="The port used by the issuing chain.",
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
    "--locking_reward_account",
    required=True,
    prompt=True,
    help="The reward account for the witness on the locking chain.",
)
@click.option(
    "--signing_seed",
    required=True,
    prompt=True,
    help="The seed to use for signing attestations.",
)
@click.option(
    "--issuing_reward_account",
    required=True,
    prompt=True,
    help="The reward account for the witness on the issuing chain.",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Whether or not to print more verbose information.",
)
def generate_witness_config(
    config_dir: str,
    name: str,
    locking_chain_port: int,
    issuing_chain_port: int,
    witness_port: int,
    locking_reward_seed: str,
    locking_reward_account: str,
    issuing_reward_seed: str,
    issuing_reward_account: str,
    src_door: str,
    signing_seed: str,
    dst_door: str = "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
    verbose: bool = False,
) -> None:
    """
    Generate a witness config file.
    \f

    Args:
        config_dir: The folder in which to store config files.
        name: The name of the witness server.
        locking_chain_port: The port used by the locking chain.
        issuing_chain_port: The port used by the issuing chain.
        witness_port: The port that will be used by the witness server.
        src_door: The door account on the source chain.
        dst_door: The door account on the destination chain. Defaults to the genesis
            account.
        signing_seed: The seed to use for signing attestations.
        locking_reward_account: The reward account for the witness on the locking chain.
        locking_reward_seed: The seed for the locking chain reward account.
        issuing_reward_account: The reward account for the witness on the issuing chain.
        issuing_reward_seed: The seed for the issuing chain reward account.
        verbose: Whether or not to print more verbose information.
    """  # noqa: D301
    abs_config_dir = os.path.abspath(config_dir)
    sub_dir = f"{abs_config_dir}/{name}"
    for path in ["", "/db"]:
        dirpath = Path(sub_dir + path)
        if dirpath.exists():
            if dirpath.is_dir():
                shutil.rmtree(dirpath)
            else:
                os.remove(dirpath)
        dirpath.mkdir(parents=True)

    template_data = {
        "locking_chain_port": locking_chain_port,
        "issuing_chain_port": issuing_chain_port,
        "witness_port": witness_port,
        "db_dir": f"{sub_dir}/db",
        "seed": signing_seed,
        "locking_reward_seed": locking_reward_seed,
        "locking_reward_account": locking_reward_account,
        "issuing_reward_seed": issuing_reward_seed,
        "issuing_reward_account": issuing_reward_account,
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
    "--directory",
    "config_dir",
    required=True,
    prompt=True,
    help="The folder in which to store the bridge bootstrap file.",
)
@click.option(
    "--mc_seed",
    "locking_chain_seed",
    required=True,
    prompt=True,
    help="The seed of the locking chain door account.",
)
@click.option(
    "--sc_seed",
    "issuing_chain_seed",
    default="snoPBrXtMeMyMHUVTgbuqAfg1SUTb",
    help="The seed of the issuing chain door account. Defaults to the genesis account.",
)
@click.option(
    "--reward_account",
    "reward_accounts",
    required=True,
    prompt=True,
    multiple=True,
    help="The seed of the witness reward account.",
)
@click.option(
    "--signing_account",
    "signing_accounts",
    required=True,
    prompt=True,
    multiple=True,
    help="The account the witness uses to sign attestations.",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Whether or not to print more verbose information.",
)
def generate_bootstrap(
    config_dir: str,
    locking_chain_seed: str,
    issuing_chain_seed: str,
    reward_accounts: List[str],
    signing_accounts: List[str],
    verbose: bool = False,
) -> None:
    """
    Generate a bootstrap config file. Used by the scripts to initialize the bridge.
    \f

    Args:
        config_dir: The folder in which to store config files.
        locking_chain_seed: The seed of the locking_chain door account.
        issuing_chain_seed: The seed of the issuing_chain door account. Defaults to the
            genesis account.
        reward_accounts: The witness reward accounts (which need to be created).
        signing_accounts: The accounts the witness uses to sign attestations.
        verbose: Whether or not to print more verbose information.
    """  # noqa: D301
    locking_door = Wallet(locking_chain_seed, 0)
    issuing_door = Wallet(issuing_chain_seed, 0)

    template_data = {
        "is_linux": platform == "linux" or platform == "linux2",
        "locking_node_port": 5005,
        "locking_door_account": locking_door.classic_address,
        "locking_door_seed": locking_door.seed,
        "locking_issue": "XRP",
        "locking_reward_accounts": reward_accounts,
        "locking_submit_accounts": reward_accounts,
        "issuing_node_port": 5006,
        "issuing_door_account": issuing_door.classic_address,
        "issuing_door_seed": issuing_door.seed,
        "issuing_issue": "XRP",
        "issuing_reward_accounts": reward_accounts,
        "issuing_submit_accounts": reward_accounts,
        "signing_accounts": signing_accounts,
    }
    if verbose:
        click.echo(pformat(template_data))

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
    "-v",
    "--verbose",
    is_flag=True,
    help="Whether or not to print more verbose information.",
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
    reward_accounts = []
    signing_accounts = []
    for i in range(num_witnesses):
        original_wallet = Wallet.create(crypto_algorithm=CryptoAlgorithm.SECP256K1)
        witness_reward_wallet = Wallet(
            original_wallet.seed, 0, algorithm=CryptoAlgorithm.ED25519
        )
        reward_accounts.append(witness_reward_wallet.classic_address)
        signing_wallet = Wallet.create(CryptoAlgorithm.SECP256K1)
        signing_accounts.append(signing_wallet.classic_address)
        ctx.invoke(
            generate_witness_config,
            config_dir=abs_config_dir,
            name=f"witness{i}",
            locking_chain_port=mc_port,
            issuing_chain_port=sc_port,
            witness_port=6010 + i,
            signing_seed=signing_wallet.seed,
            src_door=src_door.classic_address,
            locking_reward_seed=witness_reward_wallet.seed,
            locking_reward_account=witness_reward_wallet.classic_address,
            issuing_reward_seed=witness_reward_wallet.seed,
            issuing_reward_account=witness_reward_wallet.classic_address,
        )
    ctx.invoke(
        generate_bootstrap,
        config_dir=abs_config_dir,
        locking_chain_seed=src_door.seed,
        verbose=verbose,
        reward_accounts=reward_accounts,
        signing_accounts=signing_accounts,
    )
