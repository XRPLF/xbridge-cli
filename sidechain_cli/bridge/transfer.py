"""CLI command for setting up a bridge."""

from pprint import pprint
from typing import Any, Dict, List, cast

import click
import requests
from xrpl.clients import JsonRpcClient
from xrpl.models import (
    GenericRequest,
    Response,
    SignAndSubmit,
    Transaction,
    Tx,
    XChainClaim,
    XChainSeqNumCreate,
    XChainTransfer,
)
from xrpl.models.xchain_claim_proof import XChainClaimProof
from xrpl.wallet import Wallet

from sidechain_cli.utils import get_config


def _combine_proofs(proofs: List[Dict[str, Any]]) -> XChainClaimProof:
    proof = proofs[0]
    for extra_proof in proofs[1:]:
        signatures = proof["signatures"]
        proof["signatures"].extend(signatures)
    return cast(XChainClaimProof, XChainClaimProof.from_dict(proof))


def _submit_tx(
    tx: Transaction, client: JsonRpcClient, secret: str, verbose: bool
) -> Response:
    if verbose:
        print(f"submitting tx to {client.url}:")
        pprint(tx.to_xrpl())
    result = client.request(SignAndSubmit(transaction=tx, secret=secret))
    if verbose:
        print(f"Result: {result.result['engine_result']}")
    if result.result["engine_result"] != "tesSUCCESS":
        raise Exception(result.result["engine_result_message"])
    client.request(GenericRequest(method="ledger_accept"))
    tx_hash = result.result["tx_json"]["hash"]
    tx_result = client.request(Tx(transaction=tx_hash))
    return tx_result


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
    "--verbose", is_flag=True, help="Whether or not to print more verbose information."
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
    verbose: bool = False,
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
        verbose: Whether or not to print more verbose information.
        tutorial: Whether to slow down and explain each step.
    """
    bridge_config = get_config().get_bridge(bridge)
    if src_chain not in bridge_config.chains:
        print(f"Error: {src_chain} not one of the chains in {bridge}.")
        return

    try:
        from_wallet = Wallet(from_account, 0)
    except ValueError:
        print(f"Invalid seed: {from_account}")
        return
    try:
        to_wallet = Wallet(to_account, 0)
    except ValueError:
        print(f"Invalid seed: {to_account}")
        return

    dst_chain = [chain for chain in bridge_config.chains if chain != src_chain][0]
    src_door = bridge_config.door_accounts[bridge_config.chains.index(src_chain)]
    src_chain_config = get_config().get_chain(src_chain)
    dst_chain_config = get_config().get_chain(dst_chain)
    src_client = src_chain_config.get_client()
    dst_client = dst_chain_config.get_client()

    sidechain = bridge_config.get_sidechain()

    # XChainSeqNumCreate
    if tutorial:
        input("\nCreating a cross-sequence number on the destination chain...")

    seq_num_tx = XChainSeqNumCreate(
        account=to_wallet.classic_address, sidechain=sidechain
    )
    seq_num_result = _submit_tx(
        seq_num_tx, dst_client, to_wallet.seed, verbose or tutorial
    )

    # extract new sequence number from metadata
    nodes = seq_num_result.result["meta"]["AffectedNodes"]
    created_nodes = [
        node["CreatedNode"] for node in nodes if "CreatedNode" in node.keys()
    ]
    seqnum_ledger_entries = [
        node for node in created_nodes if node["LedgerEntryType"] == "CrosschainSeqNum"
    ]
    assert len(seqnum_ledger_entries) == 1
    xchain_seq = seqnum_ledger_entries[0]["NewFields"]["XChainSequence"]

    # XChainTransfer
    if tutorial:
        input("\nLocking the funds on the source chain...")

    transfer_tx = XChainTransfer(
        account=from_wallet.classic_address,
        amount=amount,
        sidechain=sidechain,
        xchain_sequence=xchain_seq,
    )
    _submit_tx(transfer_tx, src_client, from_wallet.seed, verbose or tutorial)

    # Retrieve proof from witness
    if tutorial:
        input("\nRetrieving the proofs from the witness servers...")

    proofs = []
    for witness in bridge_config.witnesses:
        witness_config = get_config().get_witness(witness)
        witness_url = f"http://{witness_config.ip}:{witness_config.rpc_port}"
        proof_request = {
            "method": "witness",
            "params": [
                {
                    "amount": amount,
                    "xchain_sequence_number": xchain_seq,
                    "dst_door": src_door,
                    "sidechain": sidechain.to_dict(),
                }
            ],
        }

        proof_result = requests.post(witness_url, json=proof_request).json()
        if verbose:
            pprint(proof_result)
        proofs.append(proof_result["result"]["proof"])

    # XChainClaim
    if tutorial:
        input(
            "\nClaiming the funds on the destination chain with the witness proofs..."
        )

    claim_tx = XChainClaim(
        account=to_wallet.classic_address,
        destination=to_wallet.classic_address,
        xchain_claim_proof=_combine_proofs(proofs),
    )
    _submit_tx(claim_tx, dst_client, to_wallet.seed, verbose)
