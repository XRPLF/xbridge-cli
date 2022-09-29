"""CLI command for setting up a bridge."""

import json
import os
from typing import Optional, Tuple

import click
from xrpl.account import does_account_exist
from xrpl.clients import JsonRpcClient
from xrpl.models import (
    AccountSet,
    AccountSetFlag,
    ServerState,
    SignerEntry,
    SignerListSet,
    XChainAccountCreateCommit,
    XChainAddAttestation,
    XChainBridge,
    XChainCreateBridge,
)
from xrpl.models.transactions.xchain_add_attestation import (
    XChainAttestationBatch,
    XChainCreateAccountAttestationBatchElement,
)
from xrpl.wallet import Wallet

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
    "--funding_seed",
    help=(
        "The master key of an account on the locking chain that can fund accounts on "
        "the issuing chain. This is only needed for an XRP-XRP bridge."
    ),
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Whether or not to print more verbose information.",
)
def setup_production_bridge(
    chain_urls: Tuple[str, str],
    signature_reward: str,
    bootstrap: str,
    funding_seed: Optional[str],
    verbose: int = 0,
) -> None:
    """
    Keep track of a bridge between a locking chain and issuing chain.
    \f

    Args:
        chain_urls: The URLs of nodes on each of the two chains that the bridge goes
            between.
        signature_reward: The reward for witnesses providing a signature.
        bootstrap: The filepath to the bootstrap config file.
        funding_seed: The master key of an account on the locking chain that can fund
            accounts on the issuing chain. This is only needed for an XRP-XRP bridge.
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

    if bridge_obj.issuing_chain_issue == "XRP" and funding_seed is None:
        raise click.ClickException("Must include `funding_seed` for XRP-XRP bridge.")

    client1 = JsonRpcClient(chain_urls[0])
    client2 = JsonRpcClient(chain_urls[1])

    accounts_locking_check = set(
        [locking_door]
        + bootstrap_config["LockingChain"]["WitnessRewardAccounts"]
        + bootstrap_config["LockingChain"]["WitnessSubmitAccounts"]
    )
    accounts_issuing_check = set(
        bootstrap_config["IssuingChain"]["WitnessRewardAccounts"]
        + bootstrap_config["IssuingChain"]["WitnessSubmitAccounts"]
    )

    # check locking chain for accounts
    for account in accounts_locking_check:
        if not does_account_exist(account, client1):
            raise click.ClickException(
                f"Account {account} does not exist on the locking chain."
            )
    if not does_account_exist(issuing_door, client2):
        raise click.ClickException(
            f"Issuing chain door {issuing_door} does not exist on the locking chain."
        )
    if bridge_obj.issuing_chain_issue != "XRP":
        # if a bridge is an XRP bridge, then the accounts need to be created via the
        # bridge (the bridge that doesn't exist yet)
        for account in accounts_issuing_check:
            if not does_account_exist(account, client2):
                raise click.ClickException(
                    f"Account {account} does not exist on the issuing chain."
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

    locking_door_seed = bootstrap_config["LockingChain"]["DoorAccount"]["Seed"]
    issuing_door_seed = bootstrap_config["IssuingChain"]["DoorAccount"]["Seed"]

    ###################################################################################
    # set up locking chain

    create_tx1 = XChainCreateBridge(
        account=locking_door,
        xchain_bridge=bridge_obj,
        signature_reward=signature_reward,
        min_account_create_amount=str(min_create2),
    )
    submit_tx_external(create_tx1, client1, locking_door_seed, verbose)

    signer_tx1 = SignerListSet(
        account=locking_door,
        signer_quorum=max(1, len(signer_entries) - 1),
        signer_entries=signer_entries,
    )
    submit_tx_external(signer_tx1, client1, locking_door_seed, verbose)

    disable_master_tx1 = AccountSet(
        account=locking_door, set_flag=AccountSetFlag.ASF_DISABLE_MASTER
    )
    submit_tx_external(disable_master_tx1, client1, locking_door_seed, verbose)

    ###################################################################################
    # set up issuing chain

    create_tx2 = XChainCreateBridge(
        account=issuing_door,
        xchain_bridge=bridge_obj,
        signature_reward=signature_reward,
        min_account_create_amount=str(min_create1),
    )
    submit_tx_external(create_tx2, client2, issuing_door_seed, verbose)

    if bridge_obj.issuing_chain_issue == "XRP":
        # we need to create the accounts via the bridge
        assert funding_seed is not None  # for typing purposes - checked earlier
        funding_wallet = Wallet(funding_seed, 0)
        amount = str(min_create2 * 2)  # submit accounts need spare funds
        attestations = []
        for account in accounts_issuing_check:
            acct_tx = XChainAccountCreateCommit(
                account=funding_wallet.classic_address,
                xchain_bridge=bridge_obj,
                signature_reward=signature_reward,
                destination=account,
                amount=amount,
            )
            submit_tx_external(acct_tx, client1, funding_seed, verbose)
            attestation = XChainCreateAccountAttestationBatchElement(
                account=issuing_door,
                amount=amount,
                attestation_reward_account=issuing_door,
                destination=account,
                public_key=funding_wallet.public_key,
                signature="",
                signature_reward=signature_reward,
                was_locking_chain_send=1,
                xchain_account_create_count="1",
            )
            attestations.append(attestation)

            if len(attestations) == 8:
                attestation_tx = XChainAddAttestation(
                    xchain_attestation_batch=XChainAttestationBatch(
                        xchain_create_account_attestation_batch=attestations
                    )
                )
                submit_tx_external(attestation_tx, client1, issuing_door_seed, verbose)
                attestations = []

        attestation_tx = XChainAddAttestation(
            account=issuing_door,
            xchain_attestation_batch=XChainAttestationBatch(
                xchain_bridge=bridge_obj,
                xchain_claim_attestation_batch=[],
                xchain_create_account_attestation_batch=attestations,
            ),
        )
        submit_tx_external(attestation_tx, client1, issuing_door_seed, verbose)

    signer_tx2 = SignerListSet(
        account=issuing_door,
        signer_quorum=max(1, len(signer_entries) - 1),
        signer_entries=signer_entries,
    )
    submit_tx_external(signer_tx2, client2, issuing_door_seed, verbose)

    disable_master_tx2 = AccountSet(
        account=issuing_door, set_flag=AccountSetFlag.ASF_DISABLE_MASTER
    )
    submit_tx_external(disable_master_tx2, client2, issuing_door_seed, verbose)
