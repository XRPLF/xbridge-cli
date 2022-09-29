"""CLI command for setting up a bridge."""

import json
import os
from typing import Tuple

import click
from xrpl.clients import JsonRpcClient
from xrpl.models import (
    ServerState,
    SignerEntry,
    SignerListSet,
    XChainBridge,
    XChainCreateBridge,
)

from sidechain_cli.utils import submit_tx_external


@click.command(name="prod-build")
@click.option(
    "--chains",
    "chain_urls",
    required=True,
    nargs=2,
    type=str,
    help="The URLs of nodes on each of the two chains that the bridge goes between.",
)
@click.option(
    "--signature_reward",
    default="100",
    help="The reward for witnesses providing a signature.",
)
@click.option(
    "--bootstrap",
    envvar="XCHAIN_CONFIG_DIR",
    required=True,
    prompt=True,
    type=click.Path(exists=True),
    help="The filepath to the bootstrap config file.",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Whether or not to print more verbose information.",
)
def setup_production_bridge(
    chain_urls: Tuple[str, str],
    signature_reward: str,
    bootstrap: str,
    verbose: bool = True,
) -> None:
    """
    Keep track of a bridge between a locking chain and issuing chain.
    \f

    Args:
        chain_urls: The URLs of nodes on each of the two chains that the bridge goes
            between.
        signature_reward: The reward for witnesses providing a signature.
        bootstrap: The filepath to the bootstrap config file.
        verbose: Whether or not to print more verbose information.
    """  # noqa: D301
    if bootstrap == os.getenv("XCHAIN_CONFIG_DIR"):
        bootstrap = os.path.join(bootstrap, "bridge_bootstrap.json")

    with open(bootstrap) as f:
        bootstrap_config = json.load(f)

    bridge_obj = XChainBridge(
        locking_chain_door=bootstrap_config["LockingChain"]["DoorAccount"]["Address"],
        locking_chain_issue=bootstrap_config["LockingChain"]["BridgeIssue"],
        issuing_chain_door=bootstrap_config["IssuingChain"]["DoorAccount"]["Address"],
        issuing_chain_issue=bootstrap_config["IssuingChain"]["BridgeIssue"],
    )

    client1 = JsonRpcClient(chain_urls[0])
    client2 = JsonRpcClient(chain_urls[1])
    server_state1 = client1.request(ServerState())
    min_create1 = str(server_state1.result["state"]["validated_ledger"]["reserve_base"])
    server_state2 = client2.request(ServerState())
    min_create2 = str(server_state2.result["state"]["validated_ledger"]["reserve_base"])

    signer_entries = []
    for witness_entry in bootstrap_config["Witnesses"]["SignerList"]:
        signer_entries.append(
            SignerEntry(
                account=witness_entry["Account"], signer_weight=witness_entry["Weight"]
            )
        )

    locking_door_account = bootstrap_config["LockingChain"]["DoorAccount"]["Address"]
    locking_door_seed = bootstrap_config["LockingChain"]["DoorAccount"]["Seed"]

    create_tx1 = XChainCreateBridge(
        account=locking_door_account,
        xchain_bridge=bridge_obj,
        signature_reward=signature_reward,
        min_account_create_amount=min_create2,  # account reserve on issuing chain
    )
    submit_tx_external(create_tx1, client1, locking_door_seed, verbose)

    signer_tx1 = SignerListSet(
        account=locking_door_account,
        signer_quorum=max(1, len(signer_entries) - 1),
        signer_entries=signer_entries,
    )
    submit_tx_external(signer_tx1, client1, locking_door_seed, verbose)

    # TODO: disable master key

    issuing_door_account = bootstrap_config["IssuingChain"]["DoorAccount"]["Address"]
    issuing_door_seed = bootstrap_config["IssuingChain"]["DoorAccount"]["Seed"]

    create_tx2 = XChainCreateBridge(
        account=issuing_door_account,
        xchain_bridge=bridge_obj,
        signature_reward=signature_reward,
        min_account_create_amount=min_create1,  # account reserve on locking chain
    )
    issuing_door_seed = bootstrap_config["IssuingChain"]["DoorAccount"]["Seed"]
    submit_tx_external(create_tx2, client2, issuing_door_seed, verbose)

    signer_tx2 = SignerListSet(
        account=issuing_door_account,
        signer_quorum=max(1, len(signer_entries) - 1),
        signer_entries=signer_entries,
    )
    submit_tx_external(signer_tx2, client2, issuing_door_seed, verbose)

    # TODO: disable master key

    accounts_to_create = set(
        bootstrap_config["IssuingChain"]["WitnessRewardAccounts"]
        + bootstrap_config["IssuingChain"]["WitnessSubmitAccounts"]
    )
    for witness_acct in accounts_to_create:
        pass
        # ctx.invoke(
        #     fund_account,
        #     chain=bridge_config.chains[0],
        #     account=witness_acct,
        #     verbose=verbose > 1,
        # )
        # ctx.invoke(
        #     fund_account,
        #     chain=bridge_config.chains[1],
        #     account=witness_acct,
        #     verbose=verbose > 1,
        # )

    if verbose > 0:
        click.secho("Initialized witness reward accounts", fg="blue")
