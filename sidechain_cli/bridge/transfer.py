"""CLI command for setting up a bridge."""

from typing import Any, Dict, cast

import click
from xrpl.clients import JsonRpcClient
from xrpl.models import (
    XRP,
    Currency,
    IssuedCurrency,
    Response,
    Transaction,
    Tx,
    XChainCommit,
    XChainCreateClaimID,
)
from xrpl.wallet import Wallet

from sidechain_cli.exceptions import SidechainCLIException
from sidechain_cli.utils import get_config, submit_tx, wait_for_attestations

_ATTESTATION_TIME_LIMIT = 10  # in seconds
_WAIT_STEP_LENGTH = 0.05


def _submit_tx(
    tx: Transaction,
    client: JsonRpcClient,
    secret: str,
    verbose: int,
    close_ledgers: bool,
) -> Response:
    result = submit_tx(tx, client, secret, verbose, close_ledgers)[0]
    tx_result = (
        result.result.get("error")
        or result.result.get("engine_result")
        or result.result["meta"]["TransactionResult"]
    )
    if tx_result != "tesSUCCESS":
        raise SidechainCLIException(
            str(
                result.result.get("error_message")
                or result.result.get("engine_result_message")
            )
        )
    tx_hash = cast(Dict[str, Any], (result.result.get("tx_json") or result.result))[
        "hash"
    ]
    return client.request(Tx(transaction=tx_hash))


@click.command(name="transfer")
@click.option(
    "--bridge",
    required=True,
    prompt=True,
    type=str,
    help="The bridge to transfer across.",
)
@click.option(
    "--from_locking/--from_issuing",
    "from_locking",
    required=True,
    prompt=True,
    help=(
        "Whether funding from the locking chain or the issuing chain. "
        "Defaults to the locking chain."
    ),
)
@click.option(
    "--amount", required=True, prompt=True, type=str, help="The amount to transfer."
)
@click.option(
    "--from",
    "from_account",
    required=True,
    prompt=True,
    type=str,
    help="The seed of the account to transfer from.",
)
@click.option(
    "--to",
    "to_account",
    required=True,
    prompt=True,
    type=str,
    help="The seed of the account to transfer to.",
)
@click.option(
    "--close-ledgers/--no-close-ledgers",
    "close_ledgers",
    default=True,
    help=(
        "Whether to close ledgers manually (via `ledger_accept`) or wait for ledgers "
        "to close automatically. A standalone node requires ledgers to be closed; an "
        "external network does not support ledger closing."
    ),
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Whether or not to print more verbose information. Supports `-vv`.",
)
@click.option(
    "--tutorial",
    is_flag=True,
    help="Turn this flag on if you want to slow down and really understand each step.",
)
def send_transfer(
    bridge: str,
    from_locking: bool,
    amount: str,
    from_account: str,
    to_account: str,
    close_ledgers: bool = True,
    verbose: int = 0,
    tutorial: bool = False,
) -> None:
    """
    Set up a bridge between a locking chain and issuing chain.
    \f

    Args:
        bridge: The bridge to transfer across.
        from_locking: Whether funding from the locking chain or the issuing chain.
            Defaults to the locking chain.
        amount: The amount to transfer.
        from_account: The seed of the account to transfer from.
        to_account: The seed of the account to transfer to.
        close_ledgers: Whether to close ledgers manually (via `ledger_accept`) or wait
            for ledgers to close automatically. A standalone node requires ledgers to
            be closed; an external network does not support ledger closing.
        verbose: Whether or not to print more verbose information. Supports `-vv`.
        tutorial: Whether to slow down and explain each step.

    Raises:
        SidechainCLIException: If there is an error with a transaction somewhere along
            the way.
        AttestationTimeoutException: If there is a timeout when waiting for
            attestations.
    """  # noqa: D301
    print_level = max(verbose, 2 if tutorial else 0)
    bridge_config = get_config().get_bridge(bridge)
    bridge_obj = bridge_config.get_bridge()
    locking_client, issuing_client = bridge_config.get_clients()
    if from_locking:
        src_client = locking_client
        dst_client = issuing_client
        from_issue = bridge_obj.locking_chain_issue
    else:
        src_client = issuing_client
        dst_client = locking_client
        from_issue = bridge_obj.issuing_chain_issue

    if isinstance(from_issue, IssuedCurrency):
        original_issue: Currency = from_issue
    else:
        original_issue = XRP()

    try:
        from_wallet = Wallet(from_account, 0)
    except ValueError:
        raise SidechainCLIException(f"Invalid `from` seed: {from_account}")
    try:
        to_wallet = Wallet(to_account, 0)
    except ValueError:
        raise SidechainCLIException(f"Invalid `to` seed: {to_account}")

    transfer_amount = original_issue.to_amount(amount)

    # XChainSeqNumCreate
    if tutorial:
        click.pause(
            info=click.style(
                "\nCreating a cross-chain claim ID on the destination chain...",
                fg="blue",
            )
        )

    seq_num_tx = XChainCreateClaimID(
        account=to_wallet.classic_address,
        xchain_bridge=bridge_obj,
        signature_reward=bridge_config.signature_reward,
        other_chain_source=from_wallet.classic_address,
    )
    seq_num_result = _submit_tx(
        seq_num_tx, dst_client, to_wallet.seed, print_level, close_ledgers
    )

    # extract new sequence number from metadata
    nodes = seq_num_result.result["meta"]["AffectedNodes"]
    created_nodes = [
        node["CreatedNode"] for node in nodes if "CreatedNode" in node.keys()
    ]
    claim_ids_ledger_entries = [
        node for node in created_nodes if node["LedgerEntryType"] == "XChainClaimID"
    ]
    assert len(claim_ids_ledger_entries) == 1
    xchain_claim_id = claim_ids_ledger_entries[0]["NewFields"]["XChainClaimID"]

    # XChainTransfer
    if tutorial:
        click.pause(
            info=click.style("\nLocking the funds on the source chain...", fg="blue")
        )

    commit_tx = XChainCommit(
        account=from_wallet.classic_address,
        amount=transfer_amount,
        xchain_bridge=bridge_obj,
        xchain_claim_id=xchain_claim_id,
        other_chain_destination=to_wallet.classic_address,
    )
    submit_tx(commit_tx, src_client, from_wallet.seed, print_level, close_ledgers)

    # wait for attestations
    if tutorial:
        click.pause(
            info=click.style(
                "Waiting for attestations from the witness servers on "
                f"{dst_client.url}...",
                fg="blue",
            )
        )
    elif print_level > 0:
        click.secho(
            f"Waiting for attestations from the witness servers on {dst_client.url}...",
            fg="blue",
        )

    wait_for_attestations(
        True,
        bridge_config,
        dst_client,
        from_wallet,
        to_wallet.classic_address,
        transfer_amount,
        xchain_claim_id,
        close_ledgers,
        verbose,
    )
