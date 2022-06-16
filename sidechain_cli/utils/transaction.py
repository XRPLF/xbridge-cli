"""Utils related to transactions."""

from xrpl.clients.sync_client import SyncClient
from xrpl.models import GenericRequest, Response, SignAndSubmit, Transaction


def submit_tx(tx: Transaction, client: SyncClient, seed: str) -> Response:
    """
    Submit a transaction to rippled, asking rippled to sign it as well.

    Args:
        tx: The transaction to submit.
        client: The client to submit it with.
        seed: The seed to sign the transaction with.

    Returns:
        The response from rippled.
    """
    result = client.request(SignAndSubmit(transaction=tx, secret=seed))
    client.request(GenericRequest(method="ledger_accept"))
    return result
