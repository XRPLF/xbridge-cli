"""CLI command for setting up a bridge."""

import json
import os
from typing import Tuple

import click
from xrpl.account import does_account_exist
from xrpl.clients import JsonRpcClient
from xrpl.models import (
    AccountSet,
    AccountSetFlag,
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

    Raises:
        ClickException: If an account on the locking chain doesn't exist (namely, the
            witness reward or submit accounts or the door account).
    """  # noqa: D301
    if bootstrap == os.getenv("XCHAIN_CONFIG_DIR"):
        bootstrap = os.path.join(bootstrap, "bridge_bootstrap.json")

    with open(bootstrap) as f:
        bootstrap_config = json.load(f)

    locking_door = bootstrap_config["LockingChain"]["DoorAccount"]["Address"]
    issuing_door = bootstrap_config["IssuingChain"]["DoorAccount"]["Address"]

    bridge_obj = XChainBridge(
        locking_chain_door=locking_door,
        locking_chain_issue=bootstrap_config["LockingChain"]["BridgeIssue"],
        issuing_chain_door=issuing_door,
        issuing_chain_issue=bootstrap_config["IssuingChain"]["BridgeIssue"],
    )

    client1 = JsonRpcClient(chain_urls[0])
    client2 = JsonRpcClient(chain_urls[1])

    # check locking chain
    accounts_check_existence = set(
        [locking_door]
        + bootstrap_config["LockingChain"]["WitnessRewardAccounts"]
        + bootstrap_config["LockingChain"]["WitnessSubmitAccounts"]
    )
    for account in accounts_check_existence:
        if not does_account_exist(account, client1):
            raise click.ClickException(
                f"Account {account} does not exist on the locking chain."
            )

    # get min create account amount values
    server_state1 = client1.request(ServerState())
    min_create1 = server_state1.result["state"]["validated_ledger"]["reserve_base"]
    server_state2 = client2.request(ServerState())
    min_create2 = server_state2.result["state"]["validated_ledger"]["reserve_base"]

    signer_entries = []
    for witness_entry in bootstrap_config["Witnesses"]["SignerList"]:
        signer_entries.append(
            SignerEntry(
                account=witness_entry["Account"], signer_weight=witness_entry["Weight"]
            )
        )

    # set up locking chain side
    def _set_up_one_chain(
        door_account: str, door_seed: str, min_create: int, client: JsonRpcClient
    ) -> None:
        create_tx = XChainCreateBridge(
            account=door_account,
            xchain_bridge=bridge_obj,
            signature_reward=signature_reward,
            min_account_create_amount=str(min_create),
        )
        submit_tx_external(create_tx, client, door_seed, verbose)

        signer_tx = SignerListSet(
            account=door_account,
            signer_quorum=max(1, len(signer_entries) - 1),
            signer_entries=signer_entries,
        )
        submit_tx_external(signer_tx, client, door_seed, verbose)

        disable_master_tx = AccountSet(
            account=door_account, set_flag=AccountSetFlag.ASF_DISABLE_MASTER
        )
        submit_tx_external(disable_master_tx, client, door_seed, verbose)

    _set_up_one_chain(
        door_account=locking_door,
        door_seed=bootstrap_config["LockingChain"]["DoorAccount"]["Seed"],
        min_create=min_create2,  # account reserve on issuing chain
        client=client1,
    )

    _set_up_one_chain(
        door_account=issuing_door,
        door_seed=bootstrap_config["IssuingChain"]["DoorAccount"]["Seed"],
        min_create=min_create1,  # account reserve on locking chain
        client=client2,
    )

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
