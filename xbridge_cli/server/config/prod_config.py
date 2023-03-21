"""Prod config generation."""
import os
from sys import platform
from typing import Optional

import click
from xrpl.wallet import Wallet

from xbridge_cli.server.config.config import _generate_template, _get_currency


@click.command(name="witness")
@click.option(
    "-c",
    "--config_path",
    default="./witness.json",
    prompt=True,
    type=click.Path(),
    help="The location in which to store this config file.",
)
@click.option(
    "--locking",
    "locking_chain",
    required=True,
    prompt="Locking Chain (IP:WS Port)",
    type=str,
    help=(
        "The address of the locking chain node's Websocket port, of the form "
        "`IP:Port`."
    ),
)
@click.option(
    "--issuing",
    "issuing_chain",
    required=True,
    prompt="Issuing Chain (IP:WS Port)",
    type=str,
    help=(
        "The address of the issuing chain node's Websocket port, of the form "
        "`IP:Port`."
    ),
)
@click.option(
    "--rpc_port",
    default="6006",
    prompt=True,
    type=int,
    help="The port that will be used by the witness server for RPC commands.",
)
@click.option(
    "--locking_door",
    required=True,
    prompt=True,
    help="The door account on the locking chain.",
)
@click.option(
    "--locking_currency",
    default="XRP",
    prompt=True,
    help=(
        "The currency on the locking chain. Defaults to XRP. An issued currency is of "
        "the form `{{currency}}.{{issue}}`"
    ),
)
@click.option(
    "--issuing_door",
    default="rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
    prompt=True,
    help="The door account on the issuing chain. Defaults to the genesis account.",
)
@click.option(
    "--signing_seed",
    "signing_seed_param",
    prompt="Signing Seed (leave blank to auto-generate)",
    default="",
    help="The seed to use for signing attestations.",
)
@click.option(
    "--locking_reward_seed",
    required=True,
    prompt=True,
    help="The seed for the reward account for the witness on the locking chain.",
)
@click.option(
    "--locking_reward_account",
    required=True,
    prompt=True,
    help="The reward account for the witness on the locking chain.",
)
@click.option(
    "--issuing_reward_seed",
    required=True,
    prompt=True,
    help="The seed for the reward account for the witness on the issuing chain.",
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
def generate_prod_witness_config(
    config_path: str,
    locking_chain: str,
    issuing_chain: str,
    rpc_port: int,
    locking_reward_seed: str,
    locking_reward_account: str,
    issuing_reward_seed: str,
    issuing_reward_account: str,
    locking_door: str,
    signing_seed_param: str = "",
    locking_currency: str = "XRP",
    issuing_door: str = "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
    verbose: bool = False,
) -> None:
    abs_config_path = os.path.abspath(config_path)
    sub_dir = "/opt/witness"

    locking_chain_ip, locking_chain_port = locking_chain.split(":")
    issuing_chain_ip, issuing_chain_port = issuing_chain.split(":")

    if signing_seed_param == "":
        signing_seed = Wallet.create().seed
    else:
        signing_seed = signing_seed_param

    locking_issue = _get_currency(locking_currency)
    issuing_issue = locking_issue.copy()
    if issuing_issue["currency"] != "XRP":
        issuing_issue["issuer"] = issuing_door

    log_file = os.path.join(os.path.dirname(abs_config_path), "witness.log")

    template_data = {
        "locking_chain_ip": locking_chain_ip,
        "locking_chain_port": locking_chain_port,
        "issuing_chain_ip": issuing_chain_ip,
        "issuing_chain_port": issuing_chain_port,
        "witness_port": rpc_port,
        "db_dir": os.path.join(sub_dir, "db"),
        "seed": signing_seed,
        "locking_reward_seed": locking_reward_seed,
        "locking_reward_account": locking_reward_account,
        "issuing_reward_seed": issuing_reward_seed,
        "issuing_reward_account": issuing_reward_account,
        "src_door": locking_door,
        "src_issue": repr(locking_issue).replace("'", '"'),
        "dst_door": issuing_door,
        "dst_issue": repr(issuing_issue).replace("'", '"'),
        "is_linux": platform == "linux" or platform == "linux2",
        "is_docker": False,
        "log_file": log_file,
    }

    if verbose:
        click.echo(template_data)

    # add the witness.json file
    _generate_template("witness.jinja", template_data, abs_config_path)
