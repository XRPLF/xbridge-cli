"""Helper types."""

from typing import TypedDict


class ChainData(TypedDict):
    """Helper type for chain data stored in the config file."""

    name: str
    rippled: str
    config: str
    pid: int


class WitnessData(TypedDict):
    """Helper type for witness data stored in the config file."""

    name: str
    witnessd: str
    config: str
    pid: int
