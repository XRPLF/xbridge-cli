"""CLI command for setting up a bridge."""

import time

import click
from xrpl.clients import JsonRpcClient
from xrpl.models import (
    GenericRequest,
    Ledger,
    Response,
    Transaction,
    Tx,
    XChainCommit,
    XChainCreateClaimID,
)
from xrpl.wallet import Wallet

from sidechain_cli.utils import get_config, submit_tx


def _submit_tx(
    tx: Transaction, client: JsonRpcClient, secret: str, verbose: int
) -> Response:
    result = submit_tx(tx, client, secret, verbose)
    tx_result = result.result.get("error") or result.result.get("engine_result")
    if tx_result != "tesSUCCESS":
        raise Exception(
            result.result.get("error_message")
            or result.result.get("engine_result_message")
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
    Set up a bridge between a mainchain and sidechain.

    Args:
        bridge: The bridge to transfer across.
        src_chain: The chain to transfer from.
        amount: The amount to transfer.
        from_account: The seed of the account to transfer from.
        to_account: The seed of the account to transfer to.
        verbose: Whether or not to print more verbose information. Supports `-vv`.
        tutorial: Whether to slow down and explain each step.

    Raises:
        Exception: If there is an error with a transaction somewhere along the way.
    """
    print_level = max(verbose, 2 if tutorial else 0)
    bridge_config = get_config().get_bridge(bridge)
    if src_chain not in bridge_config.chains:
        click.secho(f"Error: {src_chain} not one of the chains in {bridge}.", fg="red")
        return

    try:
        from_wallet = Wallet(from_account, 0)
    except ValueError:
        click.secho(f"Invalid `from` seed: {from_account}", fg="red")
        return
    try:
        to_wallet = Wallet(to_account, 0)
    except ValueError:
        click.secho(f"Invalid `to` seed: {to_account}", fg="red")
        return

    dst_chain = [chain for chain in bridge_config.chains if chain != src_chain][0]
    src_chain_config = get_config().get_chain(src_chain)
    dst_chain_config = get_config().get_chain(dst_chain)
    src_client = src_chain_config.get_client()
    dst_client = dst_chain_config.get_client()

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

    if print_level > 0:
        click.secho(
            f"Waiting for attestations from the witness servers on {dst_client.url}...",
            fg="blue",
        )

    # TODO: this should handle external networks better
    seconds_count = 0
    attestation_count = 0
    while True:
        time.sleep(1)
        open_ledger = dst_client.request(
            Ledger(ledger_index="current", transactions=True, expand=True)
        )
        open_txs = open_ledger.result["ledger"]["transactions"]
        open_attestations = 0
        for tx in open_txs:
            if tx["TransactionType"] == "XChainAddAttestation":
                batch = tx["XChainAttestationBatch"]
                if batch["XChainBridge"] != bridge_config.to_xrpl():
                    # make sure attestation is for this bridge
                    continue
                attestations = batch["XChainClaimAttestationBatch"]
                for attestation in attestations:
                    element = attestation["XChainClaimAttestationBatchElement"]
                    # check that the attestation actually matches this transfer
                    if element["Account"] != from_wallet.classic_address:
                        continue
                    if element["Amount"] != amount:
                        continue
                    if element["Destination"] != to_wallet.classic_address:
                        continue
                    if element["XChainClaimID"] != xchain_claim_id:
                        continue
                    open_attestations += 1
                    click.secho(
                        f"Received {open_attestations} attestations", fg="bright_green"
                    )
        if len(open_txs) > 0:
            dst_client.request(GenericRequest(method="ledger_accept"))
            attestation_count += open_attestations
            seconds_count = 0
        else:
            seconds_count += 1

        if attestation_count >= 4:
            break

        if seconds_count > 4:
            click.secho("Error: no transaction sent by witnesses.", fg="red")
            return

    # TODO: add support for XChainClaim if something goes wrong
