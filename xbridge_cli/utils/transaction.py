"""Utils related to transactions."""

from pprint import pformat
from typing import List, Union, cast

import click
from xrpl.clients.sync_client import SyncClient
from xrpl.models import GenericRequest, Response, Transaction
from xrpl.transaction import autofill_and_sign, submit, submit_and_wait
from xrpl.wallet import Wallet

from xbridge_cli.exceptions import XBridgeCLIException


def submit_tx(
    txs: Union[Transaction, List[Transaction]],
    client: SyncClient,
    wallet: Wallet,
    verbose: int = 0,
    close_ledgers: bool = True,
) -> List[Response]:
    """
    Submit a transaction to rippled, asking rippled to sign it as well.

    Args:
        txs: The transaction(s) to submit.
        client: The client to submit it with.
        wallet: The wallet to sign the transaction with.
        verbose: Whether or not to print more verbose information.
        close_ledgers: Whether to close ledgers manually or wait for them to be closed
            automatically.

    Returns:
        The response from rippled.

    Raises:
        XBridgeCLIException: If a transaction fails.
    """
    if isinstance(txs, Transaction):
        txs = [txs]
    if len(txs) == 0:
        return []
    if verbose > 0:
        tx_types = ", ".join([tx.transaction_type.value for tx in txs])
        click.secho(f"Submitting {tx_types} tx to {client.url}...", fg="blue")
        if verbose > 1:
            for tx in txs:
                click.echo(pformat(tx.to_xrpl()))

    results = []
    tx_results: List[str] = []
    if close_ledgers:
        for tx in txs:
            signed_tx = autofill_and_sign(tx, client, wallet)
            results.append(submit(signed_tx, client))
        client.request(GenericRequest(method="ledger_accept"))
        tx_results = [
            cast(
                str,
                result.result.get("error")
                or result.result.get("engine_result", "ERROR"),
            )
            for result in results
        ]
    else:
        # TODO: improve runtime when there is a batch submit_and_wait
        for tx in txs:
            signed_tx = autofill_and_sign(tx, client, wallet)
            result = submit_and_wait(signed_tx, client)
            results.append(result)
            tx_results.append(result.result["meta"]["TransactionResult"])

    failed = False
    for i in range(len(results)):
        result = results[i]
        tx_result = tx_results[i]
        if verbose > 0:
            text_color = "bright_green" if tx_result == "tesSUCCESS" else "bright_red"
            click.secho(f"Result: {tx_result}", fg=text_color)
            if tx_result != "tesSUCCESS":
                failed = True
        if verbose > 1:
            click.echo(pformat(result.result))
    if failed:
        raise XBridgeCLIException(", ".join(tx_results))
    return results
