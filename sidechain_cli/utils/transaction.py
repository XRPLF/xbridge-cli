"""Utils related to transactions."""

from pprint import pformat

import click
from xrpl.clients.sync_client import SyncClient
from xrpl.models import GenericRequest, Response, Transaction
from xrpl.transaction import safe_sign_and_autofill_transaction, submit_transaction
from xrpl.wallet import Wallet


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
        click.secho(
            f"Submitting {tx.transaction_type.value} tx to {client.url}...", fg="blue"
        )
        if verbose > 1:
            click.echo(pformat(tx.to_xrpl()))
    signed_tx = safe_sign_and_autofill_transaction(tx, Wallet(seed, 0), client)
    result = submit_transaction(signed_tx, client)

    client.request(GenericRequest(method="ledger_accept"))

    tx_result = result.result.get("error") or result.result.get("engine_result")
    if verbose > 0:
        text_color = "bright_green" if tx_result == "tesSUCCESS" else "bright_red"
        click.secho(f"Result: {tx_result}", fg=text_color)
    if verbose > 1:
        click.echo(pformat(result.result))
    return result
