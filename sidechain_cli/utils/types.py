"""Helper types."""

from typing import TypedDict


class ChainData(TypedDict):
    """Helper type for chain data stored in the config file."""

    name: str
    rippled: str
    config: str
    pid: int
