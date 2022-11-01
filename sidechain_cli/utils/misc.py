"""Miscellaneous util functions."""


def is_external_chain(chain: str) -> bool:
    """
    Determines whether a chain name is the URL of an external chain or the name of a
    local chain.

    Args:
        chain: The chain "name".

    Returns:
        True if the chain is an external chain's URL, False if it's the name of a local
        chain.
    """
    return "http" in chain or "ws" in chain
