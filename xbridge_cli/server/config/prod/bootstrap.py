"""Generate files related to a production bootstrap file."""

import json
import os
from sys import platform
from typing import List, Optional

import click
from xrpl import CryptoAlgorithm
from xrpl.wallet import Wallet

from xbridge_cli.server.config.config import _generate_template


@click.command(name="bootstrap")
@click.option(
    "-w",
    "--witness_file",
    required=True,
    prompt=True,
    type=click.Path(exists=True),
    help="The location of the witness config file.",
)
@click.option(
    "-o",
    "--output_file",
    prompt=True,
    type=click.Path(),
    help="The location of the witness config file.",
)
def get_bootstrap_piece_from_witness(
    witness_file: str, output_file: Optional[str] = None
) -> None:
    """
    Extract the info needed for the bootstrap file from a witness config file, without
    revealing any secret information.
    """
    with open(witness_file) as f:
        witness_config = json.load(f)

    locking_config = witness_config["LockingChain"]
    issuing_config = witness_config["IssuingChain"]

    locking_reward_account = locking_config["RewardAccount"]
    locking_submit_account = locking_config["TxnSubmit"]["SubmittingAccount"]
    issuing_reward_account = issuing_config["RewardAccount"]
    issuing_submit_account = issuing_config["TxnSubmit"]["SubmittingAccount"]
    signing_key_seed = witness_config["SigningKeySeed"]
    signing_key_algo = CryptoAlgorithm(witness_config["SigningKeyType"].upper())
    signing_key_account = Wallet(
        signing_key_seed, 0, algorithm=signing_key_algo
    ).classic_address

    template_data = {
        "locking_reward_account": locking_reward_account,
        "locking_submit_account": locking_submit_account,
        "issuing_reward_account": issuing_reward_account,
        "issuing_submit_account": issuing_submit_account,
        "signing_key_type": signing_key_algo.value,
        "signing_key_account": signing_key_account,
    }

    # add the rippled.cfg file
    _generate_template(
        "bootstrap-witness.jinja",
        template_data,
        output_file or os.path.join(os.getcwd(), "bootstrap-witness.json"),
    )


@click.command(name="combine")
@click.option(
    "-l",
    "--locking_seed",
    "locking_door_seed",
    required=True,
    prompt=True,
    help="The seed of the locking chain's door account.",
)
@click.option(
    "-i",
    "--issuing_seed",
    "issuing_door_seed",
    required=True,
    prompt=True,
    help="The seed of the issuing chain's door account.",
)
@click.option(
    "-b",
    "--bootstrap_piece",
    "bootstrap_pieces",
    required=True,
    multiple=True,
    type=click.Path(exists=True),
    help="One of the bootstrap pieces. Must include all of them here.",
)
def combine_bootstrap_pieces(
    locking_door_seed: str,
    issuing_door_seed: str,
    bootstrap_pieces: List[str],
) -> None:
    """Combine the bootstrap witness files into the bridge bootstrap file."""
    locking_reward_accounts = []
    locking_submit_accounts = []
    issuing_reward_accounts = []
    issuing_submit_accounts = []
    signing_accounts = []
    for bootstrap_piece in bootstrap_pieces:
        with open(os.path.abspath(bootstrap_piece)) as f:
            bootstrap_config = json.load(f)
        locking_reward_accounts.append(
            bootstrap_config["LockingChain"]["RewardAccount"]
        )
        locking_submit_accounts.append(
            bootstrap_config["LockingChain"]["SubmitAccount"]
        )
        issuing_reward_accounts.append(
            bootstrap_config["IssuingChain"]["RewardAccount"]
        )
        issuing_submit_accounts.append(
            bootstrap_config["IssuingChain"]["SubmitAccount"]
        )
        signing_accounts.append(bootstrap_config["SigningKeyAccount"])

    locking_door = Wallet(locking_door_seed, 0)
    issuing_door = Wallet(issuing_door_seed, 0)
    locking_issue = "XRP"
    issuing_issue = "XRP"

    template_data = {
        "is_linux": platform == "linux" or platform == "linux2",
        "locking_node_port": 5005,
        "locking_door_account": locking_door.classic_address,
        "locking_door_seed": locking_door.seed,
        "locking_issue": repr(locking_issue).replace("'", '"'),
        "locking_reward_accounts": locking_reward_accounts,
        "locking_submit_accounts": locking_submit_accounts,
        "issuing_node_port": 5006,
        "issuing_door_account": issuing_door.classic_address,
        "issuing_door_seed": issuing_door.seed,
        "issuing_issue": repr(issuing_issue).replace("'", '"'),
        "issuing_reward_accounts": issuing_reward_accounts,
        "issuing_submit_accounts": issuing_reward_accounts,
        "signing_accounts": signing_accounts,
    }
    # if verbose:
    #     click.echo(pformat(template_data))

    _generate_template(
        "bootstrap.jinja",
        template_data,
        os.path.join(os.getcwd(), "bridge_bootstrap.json"),
    )
