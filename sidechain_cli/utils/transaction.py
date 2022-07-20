"""Utils related to transactions."""

from pprint import pprint

from xrpl.clients.sync_client import SyncClient
from xrpl.models import GenericRequest, Response, SignAndSubmit, Transaction


def submit_tx(
    tx: Transaction, client: SyncClient, seed: str, verbose: bool = False
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
    if verbose:
        print(f"submitting tx to {client.url}:")
        pprint(tx.to_xrpl())
    result = client.request(SignAndSubmit(transaction=tx, secret=seed))
    client.request(GenericRequest(method="ledger_accept"))
    if verbose:
        pprint(result.result)
    return result
