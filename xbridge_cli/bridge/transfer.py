"""CLI command for setting up a bridge."""

from typing import Any, Dict, Union, cast

import click
from xrpl.clients import JsonRpcClient
from xrpl.models import Response, Transaction, Tx, XChainCommit, XChainCreateClaimID
from xrpl.wallet import Wallet

from xbridge_cli.exceptions import XBridgeCLIException
from xbridge_cli.utils import get_config, submit_tx, wait_for_attestations
from xbridge_cli.utils.misc import is_standalone_network


def _submit_tx(
    tx: Transaction,
    client: JsonRpcClient,
    wallet: Wallet,
    verbosity: int,
    close_ledgers: bool,
) -> Response:
    result = submit_tx(tx, client, wallet, verbosity, close_ledgers)[0]
    tx_result = (
        result.result.get("error")
        or result.result.get("engine_result")
        or result.result["meta"]["TransactionResult"]
    )
    if tx_result != "tesSUCCESS":
        raise XBridgeCLIException(
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
    help="Specify the transfer bridge.",
)
@click.option(
    "--from-locking/--from-issuing",
    "from_locking",
    required=True,
    prompt=True,
    help=(
        "Specify if funding comes from the locking chain or the issuing chain. "
        "Defaults to the locking chain."
    ),
)
@click.option(
    "--amount",
    required=True,
    prompt=True,
    type=float,
    help="Specify the amount to transfer.",
)
@click.option(
    "--from",
    "from_account",
    required=True,
    prompt=True,
    type=str,
    help="Specify the seed of the account to transfer from.",
)
@click.option(
    "--to",
    "to_account",
    required=True,
    prompt=True,
    type=str,
    help="Specify the seed of the account to transfer to.",
)
@click.option(
    "--close-ledgers/--no-close-ledgers",
    "close_ledgers",
    default=True,
    help=(
        "Close ledgers manually with `ledger_accept` or wait for ledgers "
        "to close automatically. Standalone nodes requires ledgers to be closed; "
        "external networks don't support ledger closing."
    ),
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Print more verbose information. Supports `-vv`.",
)
@click.option(
    "-s",
    "--silent",
    is_flag=True,
    help="Print no information. Can't be used with -v.",
)
@click.option(
    "--tutorial",
    is_flag=True,
    help="Enable this flag to slow down and understand each step.",
)
def send_transfer(
    bridge: str,
    from_locking: bool,
    amount: Union[int, float],
    from_account: str,
    to_account: str,
    close_ledgers: bool = True,
    verbose: int = 0,
    silent: bool = False,
    tutorial: bool = False,
) -> None:
    """
    Set up a bridge between a locking chain and issuing chain.
    \f

    Args:
        bridge: The bridge to transfer across.
        from_locking: Whether funding from the locking chain or the issuing chain.
            Defaults to the locking chain.
        amount: The amount to transfer (in XRP).
        from_account: The seed of the account to transfer from.
        to_account: The seed of the account to transfer to.
        close_ledgers: Whether to close ledgers manually (via `ledger_accept`) or wait
            for ledgers to close automatically. A standalone node requires ledgers to
            be closed; an external network does not support ledger closing.
        verbose: Whether or not to print more verbose information. Supports `-vv`.
        silent: Whether or not to print no information. Cannot be used with `-v`.
        tutorial: Whether to slow down and explain each step.

    Raises:
        XBridgeCLIException: If there is an error with a transaction somewhere along
            the way.
        AttestationTimeoutException: If there is a timeout when waiting for
            attestations.
    """  # noqa: D301
    if silent and verbose > 0:
        raise XBridgeCLIException("Cannot have verbose and silent flags.")
    if silent and tutorial:
        raise XBridgeCLIException("Cannot have tutorial and silent flags.")

    verbosity = 0 if silent else 1 + verbose
    print_level = max(verbosity, 2 if tutorial else 0)
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

    if not is_standalone_network(locking_client) and close_ledgers:
        raise XBridgeCLIException(
            "Must use `--no-close-ledgers` on a non-standalone node."
        )

    try:
        from_wallet = Wallet.from_seed(from_account)
    except ValueError as error:
        raise XBridgeCLIException(f"Invalid `from` seed: {from_account}") from error
    try:
        to_wallet = Wallet.from_seed(to_account)
    except ValueError as error:
        raise XBridgeCLIException(f"Invalid `to` seed: {to_account}") from error

    transfer_amount = from_issue.to_amount(amount)

    # XChainCreateClaimID
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
        seq_num_tx, dst_client, to_wallet, print_level, close_ledgers
    )

    # extract new sequence number from metadata
    nodes = seq_num_result.result["meta"]["AffectedNodes"]
    created_nodes = [
        node["CreatedNode"] for node in nodes if "CreatedNode" in node.keys()
    ]
    claim_ids_ledger_entries = [
        node
        for node in created_nodes
        if node["LedgerEntryType"] == "XChainOwnedClaimID"
    ]
    assert len(claim_ids_ledger_entries) == 1, len(claim_ids_ledger_entries)
    xchain_claim_id = claim_ids_ledger_entries[0]["NewFields"]["XChainClaimID"]

    # XChainCommit
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
    submit_tx(commit_tx, src_client, from_wallet, print_level, close_ledgers)

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
        verbosity,
    )
