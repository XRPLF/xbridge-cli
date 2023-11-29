"""Generate config files."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from pprint import pformat
from sys import platform
from typing import Any, Dict, List, Optional, Tuple

import click
from jinja2 import Environment, FileSystemLoader
from xrpl import CryptoAlgorithm
from xrpl.wallet import Wallet

from xbridge_cli.exceptions import XBridgeCLIException
from xbridge_cli.server.config.ports import Ports
from xbridge_cli.utils import CryptoAlgorithmChoice, CurrencyDict

_GENESIS_SEED = "snoPBrXtMeMyMHUVTgbuqAfg1SUTb"

_JINJA_ENV = Environment(
    loader=FileSystemLoader(
        searchpath=os.path.join(*os.path.split(__file__)[:-1], "templates")
    ),
    trim_blocks=True,
    lstrip_blocks=True,
)


def _get_currency(currency_str: str) -> CurrencyDict:
    if currency_str == "XRP":
        return {"currency": "XRP"}

    assert currency_str.count(".") == 1
    currency_split = currency_str.split(".")
    return {"currency": currency_split[0], "issuer": currency_split[1]}


# render a Jinja template and dump it into a file
def _generate_template(
    template_name: str, template_data: Dict[str, Any], filename: str
) -> None:
    template = _JINJA_ENV.get_template(template_name)

    with open(filename, "w+") as f:
        f.write(template.render(template_data))


# generate a standalone rippled.cfg file
def _generate_standalone_config(
    *, ports: Ports, cfg_type: str, config_dir: str, docker: bool = False
) -> None:
    abs_config_dir = os.path.abspath(config_dir)
    if docker:
        sub_dir = "/etc/opt/ripple"
        cfg_dir = f"{abs_config_dir}/{cfg_type}"
    else:
        sub_dir = f"{abs_config_dir}/{cfg_type}"
        cfg_dir = sub_dir

    for path in ["", "/db"]:
        dirpath = Path(cfg_dir + path)
        if not dirpath.exists():
            dirpath = Path(cfg_dir + path)
            dirpath.mkdir(parents=True)

    template_data = {
        "sub_dir": sub_dir,
        "ports": ports.to_dict(),
    }

    # add the rippled.cfg file
    _generate_template(
        "rippled.jinja",
        template_data,
        os.path.join(cfg_dir, "rippled.cfg"),
    )


def _generate_rippled_configs(config_dir: str, docker: bool = False) -> Tuple[int, int]:
    """
    Generate the rippled config files.

    Args:
        config_dir: The directory to use for the config files.
        docker: Whether the config files are for a docker setup.

    Returns:
        The locking chain and issuing chain WS ports.
    """
    locking_ports = Ports.generate(0)
    _generate_standalone_config(
        ports=locking_ports,
        cfg_type="locking_chain",
        config_dir=config_dir,
        docker=docker,
    )

    issuing_ports = Ports.generate(1)
    _generate_standalone_config(
        ports=issuing_ports,
        cfg_type="issuing_chain",
        config_dir=config_dir,
        docker=docker,
    )

    return locking_ports.ws_public_port, issuing_ports.ws_public_port


@click.command(name="witness")
@click.option(
    "--config-dir",
    "config_dir",
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
    "--docker",
    "is_docker",
    is_flag=True,
    help="Whether the config files are for a docker setup.",
)
@click.option(
    "--locking-ip",
    "locking_chain_ip",
    default="127.0.0.1",
    type=str,
    help="The IP address of the locking chain node.",
)
@click.option(
    "--locking-port",
    "locking_chain_port",
    required=True,
    prompt=True,
    type=int,
    help="The port used by the locking chain.",
)
@click.option(
    "--issuing-ip",
    "issuing_chain_ip",
    default="127.0.0.1",
    type=str,
    help="The IP address of the issuing chain node.",
)
@click.option(
    "--issuing-port",
    "issuing_chain_port",
    required=True,
    prompt=True,
    type=int,
    help="The port used by the issuing chain.",
)
@click.option(
    "--witness-port",
    "witness_port",
    required=True,
    prompt=True,
    type=int,
    help="The port that will be used by the witness server.",
)
@click.option(
    "--src-door",
    "src_door",
    required=True,
    prompt=True,
    help="The door account on the source chain.",
)
@click.option(
    "--src-currency",
    "src_currency",
    default="XRP",
    help=(
        "The currency on the source chain. Defaults to XRP. An issued currency is of "
        "the form `{{currency}}.{{issue}}`"
    ),
)
@click.option(
    "--dst-door",
    "dst_door",
    default="rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
    help="The door account on the destination chain. Defaults to the genesis account.",
)
@click.option(
    "--dst-currency",
    "dst_currency",
    default="XRP",
    help=(
        "The currency on the destination chain. Defaults to XRP. An issued currency "
        "is of the form `{{currency}}.{{issue}}`"
    ),
)
@click.option(
    "--locking-reward-seed",
    "locking_reward_seed",
    required=True,
    prompt=True,
    help="The seed for the reward account for the witness on the locking chain.",
)
@click.option(
    "--locking-reward-account",
    "locking_reward_account",
    required=True,
    prompt=True,
    help="The reward account for the witness on the locking chain.",
)
@click.option(
    "--signing-seed",
    "signing_seed",
    required=True,
    prompt=True,
    help="The seed to use for signing attestations.",
)
@click.option(
    "--issuing-reward-seed",
    "issuing_reward_seed",
    required=True,
    prompt=True,
    help="The seed for the reward account for the witness on the issuing chain.",
)
@click.option(
    "--issuing-reward-account",
    "issuing_reward_account",
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
    locking_chain_ip: str,
    locking_chain_port: int,
    issuing_chain_ip: str,
    issuing_chain_port: int,
    witness_port: int,
    locking_reward_seed: str,
    locking_reward_account: str,
    issuing_reward_seed: str,
    issuing_reward_account: str,
    src_door: str,
    signing_seed: str,
    src_currency: str = "XRP",
    dst_door: str = "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
    dst_currency: str = "XRP",
    is_docker: bool = True,
    verbose: bool = False,
) -> None:
    """
    Generate a witness config file.
    \f

    Args:
        config_dir: The folder in which to store config files.
        name: The name of the witness server.
        locking_chain_ip: The IP address of the locking chain node.
        issuing_chain_ip: The IP address of the issuing chain node.
        locking_chain_port: The port used by the locking chain.
        issuing_chain_port: The port used by the issuing chain.
        witness_port: The port that will be used by the witness server.
        src_door: The door account on the source chain.
        src_currency: The currency on the source chain.
        dst_door: The door account on the destination chain. Defaults to the genesis
            account.
        dst_currency: The currency on the destination chain.
        signing_seed: The seed to use for signing attestations.
        locking_reward_account: The reward account for the witness on the locking chain.
        locking_reward_seed: The seed for the locking chain reward account.
        issuing_reward_account: The reward account for the witness on the issuing chain.
        is_docker: Whether the config files are for a docker setup.
        issuing_reward_seed: The seed for the issuing chain reward account.
        verbose: Whether or not to print more verbose information.
    """  # noqa: D301
    abs_config_dir = os.path.abspath(config_dir)
    if is_docker:
        sub_dir = "/opt/witness"
        cfg_dir = os.path.join(abs_config_dir, name)
    else:
        sub_dir = os.path.join(abs_config_dir, name)
        cfg_dir = sub_dir

    assert (src_currency == "XRP" and dst_currency == "XRP") or (
        src_currency != "XRP" and dst_currency != "XRP"
    )
    src_issue = _get_currency(src_currency)
    dst_issue = _get_currency(dst_currency)
    if "issuer" in dst_issue:
        assert dst_issue["issuer"] == dst_door

    for path in ["", "/db"]:
        dirpath = Path(cfg_dir + path)
        if dirpath.exists():
            if dirpath.is_dir():
                shutil.rmtree(dirpath)
            else:
                os.remove(dirpath)
        dirpath.mkdir(parents=True)

    log_file = os.path.join(sub_dir, "witness.log")

    template_data = {
        "locking_chain_ip": locking_chain_ip,
        "locking_chain_port": locking_chain_port,
        "issuing_chain_ip": issuing_chain_ip,
        "issuing_chain_port": issuing_chain_port,
        "witness_port": witness_port,
        "db_dir": os.path.join(sub_dir, "db"),
        "seed": signing_seed,
        "locking_reward_seed": locking_reward_seed,
        "locking_reward_account": locking_reward_account,
        "issuing_reward_seed": issuing_reward_seed,
        "issuing_reward_account": issuing_reward_account,
        "src_door": src_door,
        "src_issue": repr(src_issue).replace("'", '"'),
        "dst_door": dst_door,
        "dst_issue": repr(dst_issue).replace("'", '"'),
        "is_linux": platform == "linux" or platform == "linux2",
        "is_docker": is_docker,
        "log_file": log_file,
    }

    if verbose:
        click.echo(template_data)

    # add the witness.json file
    _generate_template(
        "witness.jinja",
        template_data,
        os.path.join(cfg_dir, "witness.json"),
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
    "--locking-seed",
    "locking_seed",
    required=True,
    prompt=True,
    help="The seed of the locking chain door account.",
)
@click.option(
    "--locking-algorithm",
    "locking_algorithm",
    type=CryptoAlgorithmChoice,
    help="The algorithm used to generate the keypair from the locking door's seed.",
)
@click.option(
    "--locking-currency",
    "locking_currency",
    default="XRP",
    help=(
        "The bridge's locking chain currency. Defaults to XRP. An issued currency is "
        "of the form `{{currency}}.{{issue}}`."
    ),
)
@click.option(
    "--issuing-seed",
    "issuing_seed",
    default=_GENESIS_SEED,
    help="The seed of the issuing chain door account. Defaults to the genesis account.",
)
@click.option(
    "--issuing-algorithm",
    "issuing_algorithm",
    type=CryptoAlgorithmChoice,
    help="The algorithm used to generate the keypair from the issuing door's seed.",
)
@click.option(
    "--issuing-currency",
    "issuing_currency",
    default="XRP",
    help=(
        "The bridge's issuing chain currency. Defaults to XRP. An issued currency is "
        "of the form `{{currency}}.{{issue}}`."
    ),
)
@click.option(
    "--reward-account",
    "reward_accounts",
    required=True,
    prompt=True,
    multiple=True,
    help="The seed of the witness reward account.",
)
@click.option(
    "--signing-account",
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
    locking_seed: str,
    locking_currency: str,
    issuing_seed: str,
    issuing_currency: str,
    reward_accounts: List[str],
    signing_accounts: List[str],
    locking_algorithm: Optional[str] = None,
    issuing_algorithm: Optional[str] = None,
    verbose: bool = False,
) -> None:
    """
    Generate a bootstrap config file. Used by the scripts to initialize the bridge.
    \f

    Args:
        config_dir: The folder in which to store config files.
        locking_seed: The seed of the locking_chain door account.
        locking_algorithm: The algorithm used to generate the keypair from the locking
            door seed.
        locking_currency: The currency on the locking chain.
        issuing_seed: The seed of the issuing_chain door account. Defaults to the
            genesis account.
        issuing_algorithm: The algorithm used to generate the keypair from the issuing
            door seed.
        issuing_currency: The currency on the issuing chain.
        reward_accounts: The witness reward accounts (which need to be created).
        signing_accounts: The accounts the witness uses to sign attestations.
        verbose: Whether or not to print more verbose information.
    """  # noqa: D301
    locking_wallet_algo = (
        CryptoAlgorithm(locking_algorithm)
        if locking_algorithm
        else CryptoAlgorithm.ED25519
    )
    issuing_wallet_algo = (
        CryptoAlgorithm(issuing_algorithm)
        if issuing_algorithm
        else CryptoAlgorithm.ED25519
    )
    locking_door = Wallet.from_seed(locking_seed, algorithm=locking_wallet_algo)
    issuing_door = Wallet.from_seed(issuing_seed, algorithm=issuing_wallet_algo)

    assert (locking_currency == "XRP" and issuing_currency == "XRP") or (
        locking_currency != "XRP" and issuing_currency != "XRP"
    )
    locking_issue = _get_currency(locking_currency)
    issuing_issue = _get_currency(issuing_currency)
    if "issuer" in issuing_issue:
        assert issuing_issue["issuer"] == issuing_door.classic_address

    template_data = {
        "is_linux": platform == "linux" or platform == "linux2",
        "locking_node_port": 5005,
        "locking_door_account": locking_door.classic_address,
        "locking_door_seed": locking_door.seed,
        "locking_door_algo": locking_wallet_algo.value,
        "locking_issue": repr(locking_issue).replace("'", '"'),
        "locking_reward_accounts": reward_accounts,
        "locking_submit_accounts": reward_accounts,
        "issuing_node_port": 5006,
        "issuing_door_account": issuing_door.classic_address,
        "issuing_door_seed": issuing_door.seed,
        "issuing_door_algo": issuing_wallet_algo.value,
        "issuing_issue": repr(issuing_issue).replace("'", '"'),
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
    "--config-dir",
    "config_dir",
    envvar="XCHAIN_CONFIG_DIR",
    required=True,
    prompt=True,
    type=click.Path(),
    help="The folder in which to store config files.",
)
@click.option(
    "--num-witnesses",
    "num_witnesses",
    default=5,
    type=int,
    help="The number of witness configs to generate. Defaults to 5.",
)
@click.option(
    "--currency",
    default="XRP",
    help=(
        "The currency transferred across the bridge. Defaults to XRP. An issued "
        "currency is of the form `{{currency}}.{{issue}}`."
    ),
)
@click.option(
    "--docker",
    "is_docker",
    is_flag=True,
    help="Whether the config files are for a docker setup.",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Whether or not to print more verbose information.",
)
@click.pass_context
def generate_all_configs(
    ctx: click.Context,
    config_dir: str,
    num_witnesses: int = 5,
    currency: str = "XRP",
    is_docker: bool = False,
    verbose: bool = False,
) -> None:
    """
    Generate the rippled and witness configs.

    Args:
        ctx: The click context.
        config_dir: The directory to use for the config files.
        num_witnesses: The number of witnesses configs to generate.
        currency: The currency that is being transferred across the bridge.
        is_docker: Whether the config files are for a docker setup.
        verbose: Whether or not to print more verbose information.

    Raises:
        XBridgeCLIException: If something really weird goes wrong.
    """
    # TODO: add support for external networks
    abs_config_dir = os.path.abspath(config_dir)

    locking_port, issuing_port = _generate_rippled_configs(abs_config_dir, is_docker)
    locking_door = Wallet.create(algorithm=CryptoAlgorithm.SECP256K1)

    if currency == "XRP":
        locking_currency = "XRP"
        issuing_currency = "XRP"
        issuing_door = Wallet.from_seed(
            _GENESIS_SEED, algorithm=CryptoAlgorithm.SECP256K1
        )
        issuing_algorithm = "secp256k1"
    else:
        assert currency.count(".") == 1
        currency_code, _issuer = currency.split(".")
        locking_currency = currency
        issuing_door = Wallet.create()
        issuing_algorithm = "ed25519"
        issuing_currency = f"{currency_code}.{issuing_door.classic_address}"

    reward_accounts = []
    signing_accounts = []
    for i in range(num_witnesses):
        original_wallet = Wallet.create(algorithm=CryptoAlgorithm.SECP256K1)
        if original_wallet.seed is None:
            raise XBridgeCLIException(
                "Something weird happened, the wallet should have a seed"
            )
        witness_reward_wallet = Wallet.from_seed(
            original_wallet.seed, algorithm=CryptoAlgorithm.ED25519
        )
        reward_accounts.append(witness_reward_wallet.classic_address)
        wallet = Wallet.create(algorithm=CryptoAlgorithm.SECP256K1)
        if wallet.seed is None:
            raise XBridgeCLIException(
                "Something weird happened, the wallet should have a seed"
            )
        signing_wallet = Wallet.from_seed(
            wallet.seed, algorithm=CryptoAlgorithm.ED25519
        )
        signing_accounts.append(signing_wallet.classic_address)
        ctx.invoke(
            generate_witness_config,
            config_dir=abs_config_dir,
            name=f"witness{i}",
            locking_chain_port=locking_port,
            issuing_chain_port=issuing_port,
            witness_port=6010 + i,
            signing_seed=signing_wallet.seed,
            src_door=locking_door.classic_address,
            src_currency=locking_currency,
            dst_door=issuing_door.classic_address,
            dst_currency=issuing_currency,
            locking_reward_seed=witness_reward_wallet.seed,
            locking_reward_account=witness_reward_wallet.classic_address,
            issuing_reward_seed=witness_reward_wallet.seed,
            issuing_reward_account=witness_reward_wallet.classic_address,
            is_docker=is_docker,
        )
    ctx.invoke(
        generate_bootstrap,
        config_dir=abs_config_dir,
        locking_seed=locking_door.seed,
        locking_algorithm="secp256k1",
        locking_currency=locking_currency,
        issuing_seed=issuing_door.seed,
        issuing_algorithm=issuing_algorithm,
        issuing_currency=issuing_currency,
        verbose=verbose,
        reward_accounts=reward_accounts,
        signing_accounts=signing_accounts,
    )
