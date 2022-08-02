"""CLI command for setting up a bridge."""

from pprint import pprint

import click
import httpx
from xrpl.clients import JsonRpcClient
from xrpl.models import (
    Response,
    Transaction,
    Tx,
    XChainAddAttestation,
    XChainCommit,
    XChainCreateClaimID,
)
from xrpl.models.transactions.xchain_add_attestation import (
    XChainAttestationBatch,
    XChainClaimAttestationBatchElement,
)
from xrpl.wallet import Wallet

from sidechain_cli.utils import get_config, submit_tx


def _submit_tx(
    tx: Transaction, client: JsonRpcClient, secret: str, verbose: bool
) -> Response:
    if verbose:
        print(f"submitting tx to {client.url}:")
        pprint(tx.to_xrpl())
    result = submit_tx(tx, client, secret)
    tx_result = result.result.get("error") or result.result.get("engine_result")
    if verbose:
        print(f"Result: {tx_result}")
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

    Raises:
        Exception: If there is an error with a transaction somewhere along the way.
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
    src_chain_config = get_config().get_chain(src_chain)
    dst_chain_config = get_config().get_chain(dst_chain)
    src_client = src_chain_config.get_client()
    dst_client = dst_chain_config.get_client()
    src_door = bridge_config.door_accounts[bridge_config.chains.index(src_chain)]

    bridge_obj = bridge_config.get_bridge()

    # XChainSeqNumCreate
    if tutorial:
        input("\nCreating a cross-chain claim ID on the destination chain...")

    seq_num_tx = XChainCreateClaimID(
        account=to_wallet.classic_address,
        xchain_bridge=bridge_obj,
        signature_reward=bridge_config.signature_reward,
        other_chain_account=from_wallet.classic_address,
    )
    seq_num_result = _submit_tx(
        seq_num_tx, dst_client, to_wallet.seed, verbose or tutorial
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
        input("\nLocking the funds on the source chain...")

    commit_tx = XChainCommit(
        account=from_wallet.classic_address,
        amount=amount,
        xchain_bridge=bridge_obj,
        xchain_claim_id=xchain_claim_id,
        # other_chain_destination=to_wallet.classic_address
    )
    _submit_tx(commit_tx, src_client, from_wallet.seed, verbose or tutorial)

    # TODO: wait for the witnesses to send their attestations (once witnesses send
    # their own)
    if tutorial:
        input("\nRetrieving the proofs from the witness servers...")

    for witness in bridge_config.witnesses:
        witness_config = get_config().get_witness(witness)

        if tutorial:
            input(f"\nRetrieving the proofs from witness {witness_config.name}...")

        witness_url = f"http://{witness_config.ip}:{witness_config.rpc_port}"
        proof_request = {
            "method": "witness",
            "params": [
                {
                    "sending_account": from_wallet.classic_address,
                    "reward_account": "rGzx83BVoqTYbGn7tiVAnFw7cbxjin13jL",
                    "sending_amount": amount,
                    "claim_id": int(xchain_claim_id, 16),
                    "door": src_door,
                    "bridge": bridge_config.to_xrpl(),
                    "signature_reward": bridge_config.signature_reward,
                    "destination": to_wallet.classic_address,
                }
            ],
        }

        proof_result = httpx.post(witness_url, json=proof_request).json()
        if verbose or tutorial:
            pprint(proof_result)
        if "error" in proof_result:
            error_message = proof_result["error"]["error"]
            raise Exception(f"Request for proof failed: {error_message}")
        proof = proof_result["result"]["XChainAttestationBatch"][
            "XChainClaimAttestationBatch"
        ][0]
        # TODO: remove when this bug is fixed in rippled
        proof["XChainClaimAttestationBatchElement"]["XChainClaimID"] = str(
            int(proof["XChainClaimAttestationBatchElement"]["XChainClaimID"], 16)
        )

        attestation_tx = XChainAddAttestation(
            account="rGzx83BVoqTYbGn7tiVAnFw7cbxjin13jL",
            xchain_attestation_batch=XChainAttestationBatch(
                xchain_bridge=bridge_config.get_bridge(),
                xchain_claim_attestation_batch=[
                    XChainClaimAttestationBatchElement.from_xrpl(proof)
                ],
                xchain_create_account_attestation_batch=[],
            ),
        )
        if tutorial:
            input(f"\nSubmitting attestation tx for witness {witness_config.name}...")

        _submit_tx(
            attestation_tx,
            dst_client,
            "snLsJNbh3qQVJuB2FmoGu3SGBENLB",
            verbose or tutorial,
        )

    # TODO: add support for XChainClaim if something goes wrong
