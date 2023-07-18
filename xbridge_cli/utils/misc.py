"""Miscellaneous util functions."""

import click
from xrpl import CryptoAlgorithm
from xrpl.clients import JsonRpcClient
from xrpl.models import ServerInfo

CryptoAlgorithmChoice = click.Choice([e.value for e in CryptoAlgorithm])


def is_standalone_network(client: JsonRpcClient) -> bool:
    """Checks if a client is connected to a standalone network or not.

    Args:
        client (JsonRpcClient): The client connected to the network.

    Returns:
        bool: Whether the network is a standalone node.
    """
    server_info = client.request(ServerInfo())
    validators = server_info.result["info"]["validation_quorum"]
    return bool(validators == 0)
