"""Utils related to transactions."""

from pprint import pformat
from typing import List, Union

import click
from xrpl.clients.sync_client import SyncClient
from xrpl.models import GenericRequest, Response, Transaction
from xrpl.transaction import (
    safe_sign_and_autofill_transaction,
    send_reliable_submission,
    submit_transaction,
)
from xrpl.wallet import Wallet


def submit_tx(
    txs: Union[Transaction, List[Transaction]],
    client: SyncClient,
    seed: str,
    verbose: int = 0,
    close_ledgers: bool = True,
) -> List[Response]:
    """
    Submit a transaction to rippled, asking rippled to sign it as well.

    Args:
        txs: The transaction(s) to submit.
        client: The client to submit it with.
        seed: The seed to sign the transaction with.
        verbose: Whether or not to print more verbose information.
        close_ledgers: Whether to close ledgers manually or wait for them to be closed
            automatically.

    Returns:
        The response from rippled.
    """
    if isinstance(txs, Transaction):
        txs = [txs]
    if verbose > 0:
        tx_types = ", ".join([tx.transaction_type.value for tx in txs])
        click.secho(f"Submitting {tx_types} tx to {client.url}...", fg="blue")
        if verbose > 1:
            for tx in txs:
                click.echo(pformat(tx.to_xrpl()))

    if close_ledgers:
        results = []
        for tx in txs:
            signed_tx = safe_sign_and_autofill_transaction(tx, Wallet(seed, 0), client)
            results.append(submit_transaction(signed_tx, client))
        client.request(GenericRequest(method="ledger_accept"))
        tx_results = [
            result.result.get("error") or result.result.get("engine_result")
            for result in results
        ]
    else:
        # TODO: improve runtime when there is a batch send_reliable_submission
        results = []
        tx_results = []
        for tx in txs:
            signed_tx = safe_sign_and_autofill_transaction(tx, Wallet(seed, 0), client)
            result = send_reliable_submission(signed_tx, client)
            results.append(result)
            tx_results.append(result.result["meta"]["TransactionResult"])

    for i in range(len(results)):
        result = results[i]
        tx_result = tx_results[i]
        if verbose > 0:
            text_color = "bright_green" if tx_result == "tesSUCCESS" else "bright_red"
            click.secho(f"Result: {tx_result}", fg=text_color)
        if verbose > 1:
            click.echo(pformat(result.result))
    return results
