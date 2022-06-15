"""CLI command for setting up a bridge."""

from pprint import pprint
from typing import Any, Dict, Literal, Union, cast

import click
from xrpl.clients import JsonRpcClient
from xrpl.models import (
    GenericRequest,
    IssuedCurrency,
    Response,
    Sidechain,
    SignAndSubmit,
    Transaction,
    Tx,
    XChainClaim,
    XChainSeqNumCreate,
    XChainTransfer,
)
from xrpl.wallet import Wallet

from sidechain_cli.utils import IssuedCurrencyDict, get_config


def _to_currency(
    token: Union[Literal["XRP"], IssuedCurrencyDict]
) -> Union[Literal["XRP"], IssuedCurrency]:
    if isinstance(token, dict):
        return cast(
            IssuedCurrency, IssuedCurrency.from_dict(cast(Dict[str, Any], token))
        )
    return token


def _submit_tx(
    tx: Transaction, client: JsonRpcClient, secret: str, verbose: bool
) -> Response:
    if verbose:
        print(f"submitting tx to {client.url}:")
        pprint(tx.to_xrpl())
    result = client.request(SignAndSubmit(transaction=tx, secret=secret))
    print(result)
    client.request(GenericRequest(method="ledger_accept"))
    tx_hash = result.result["tx_json"]["hash"]
    print(tx_hash)
    tx_result = client.request(Tx(transaction=tx_hash))
    if verbose:
        pprint(tx_result.result)
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
def send_transfer(
    bridge: str,
    src_chain: str,
    amount: str,
    from_account: str,
    to_account: str,
    verbose: bool = False,
) -> None:
    """Set up a bridge between a mainchain and sidechain."""
    # TODO: validate
    print(bridge, src_chain, amount, from_account, to_account)
    from_wallet = Wallet(from_account, 0)
    to_wallet = Wallet(to_account, 0)
    bridge_config = get_config().get_bridge(bridge)

    if src_chain not in bridge_config.chains:
        print(f"Error: {src_chain} not one of the chains in {bridge}.")
        return
    dst_chain = [chain for chain in bridge_config.chains if chain != src_chain][0]
    dst_door = bridge_config.door_accounts[bridge_config.chains.index(dst_chain)]
    src_chain_config = get_config().get_chain(src_chain)
    dst_chain_config = get_config().get_chain(dst_chain)
    witness_config = get_config().get_witness(bridge_config.witnesses[0])
    src_client = src_chain_config.get_client()
    dst_client = dst_chain_config.get_client()
    witness_client = JsonRpcClient(
        f"http://{witness_config.ip}:{witness_config.rpc_port}"
    )

    sidechain = Sidechain(
        src_chain_door=bridge_config.door_accounts[0],
        src_chain_issue=_to_currency(bridge_config.xchain_currencies[0]),
        dst_chain_door=bridge_config.door_accounts[1],
        dst_chain_issue=_to_currency(bridge_config.xchain_currencies[1]),
    )

    # XChainSeqNumCreate
    seq_num_tx = XChainSeqNumCreate(
        account=to_wallet.classic_address, sidechain=sidechain
    )
    seq_num_result = _submit_tx(seq_num_tx, dst_client, to_wallet.seed, verbose)
    nodes = seq_num_result.result["meta"]["AffectedNodes"]
    modified_nodes = [
        node["ModifiedNode"]["PreviousFields"]
        for node in nodes
        if "ModifiedNode" in node.keys()
        and "PreviousFields" in node["ModifiedNode"].keys()
    ]
    xchain_seq = [
        node["XChainSequence"]
        for node in modified_nodes
        if "XChainSequence" in node.keys()
    ][0]

    # XChainTransfer
    transfer_tx = XChainTransfer(
        account=from_wallet.classic_address,
        amount=amount,
        sidechain=sidechain,
        xchain_sequence=xchain_seq,
    )
    _submit_tx(transfer_tx, src_client, from_wallet.seed, verbose)

    # retrieve proof from witness
    proof_request = GenericRequest(
        method="witness",
        amount=amount,
        xchain_sequence_number=xchain_seq,
        dst_door=dst_door,
        sidechain=sidechain,
    )
    print(proof_request.to_dict())
    print(witness_client.request(proof_request))

    # XChainClaim
