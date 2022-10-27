"""CLI command for setting up a bridge."""

import click
from xrpl.clients import JsonRpcClient
from xrpl.models import Response, Transaction, Tx, XChainCommit, XChainCreateClaimID
from xrpl.wallet import Wallet

from sidechain_cli.exceptions import SidechainCLIException
from sidechain_cli.utils import (
    get_config,
    is_external_chain,
    submit_tx,
    wait_for_attestations,
)

_ATTESTATION_TIME_LIMIT = 10  # in seconds
_WAIT_STEP_LENGTH = 0.05


def _submit_tx(
    tx: Transaction, client: JsonRpcClient, secret: str, verbose: int
) -> Response:
    result = submit_tx(tx, client, secret, verbose)
    tx_result = result.result.get("error") or result.result.get("engine_result")
    if tx_result != "tesSUCCESS":
        raise SidechainCLIException(
            str(
                result.result.get("error_message")
                or result.result.get("engine_result_message")
            )
        )
    tx_hash = result.result["tx_json"]["hash"]
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
    "--src_chain",
    required=True,
    prompt=True,
    type=str,
    help="The chain to transfer from.",
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
    src_chain: str,
    amount: str,
    from_account: str,
    to_account: str,
    verbose: int = 0,
    tutorial: bool = False,
) -> None:
    """
    Set up a bridge between a locking chain and issuing chain.
    \f

    Args:
        bridge: The bridge to transfer across.
        src_chain: The chain to transfer from.
        amount: The amount to transfer.
        from_account: The seed of the account to transfer from.
        to_account: The seed of the account to transfer to.
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
    locking_client, issuing_client = bridge_config.get_clients()
    if is_external_chain(src_chain):
        from_url = src_chain
    else:
        from_config = get_config().get_chain(src_chain)
        from_url = f"http://{from_config.http_ip}:{from_config.http_port}"
    if locking_client.url == from_url:
        src_client = locking_client
        dst_client = issuing_client
    elif issuing_client.url == from_url:
        src_client = issuing_client
        dst_client = locking_client
    else:
        raise SidechainCLIException(
            f"{src_chain} is not one of the chains in {bridge}."
        )

    try:
        from_wallet = Wallet(from_account, 0)
    except ValueError:
        raise SidechainCLIException(f"Invalid `from` seed: {from_account}")
    try:
        to_wallet = Wallet(to_account, 0)
    except ValueError:
        raise SidechainCLIException(f"Invalid `to` seed: {to_account}")

    bridge_obj = bridge_config.get_bridge()

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
    seq_num_result = _submit_tx(seq_num_tx, dst_client, to_wallet.seed, print_level)

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
        amount=amount,
        xchain_bridge=bridge_obj,
        xchain_claim_id=xchain_claim_id,
        other_chain_destination=to_wallet.classic_address,
    )
    _submit_tx(commit_tx, src_client, from_wallet.seed, print_level)

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
        amount,
        xchain_claim_id,
        True,  # TODO: add support for close_ledgers bool
        verbose,
    )
