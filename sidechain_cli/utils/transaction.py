"""Utils related to transactions."""

from pprint import pprint

import click
from xrpl.clients.sync_client import SyncClient
from xrpl.models import GenericRequest, Response, SignAndSubmit, Transaction


def submit_tx(
    tx: Transaction, client: SyncClient, seed: str, verbose: int = 0
) -> Response:
    """
    Submit a transaction to rippled, asking rippled to sign it as well.

    Args:
        tx: The transaction to submit.
        client: The client to submit it with.
        seed: The seed to sign the transaction with.
        verbose: Whether or not to print more verbose information.

    Returns:
        The response from rippled.
    """
    if verbose > 0:
        click.echo(f"submitting {tx.transaction_type.value} tx to {client.url}...")
        if verbose > 1:
            pprint(tx.to_xrpl())
    result = client.request(SignAndSubmit(transaction=tx, secret=seed))
    client.request(GenericRequest(method="ledger_accept"))
    tx_result = result.result.get("error") or result.result.get("engine_result")
    if verbose > 0:
        click.echo(f"Result: {tx_result}")
    if verbose > 1:
        pprint(result.result)
    return result
