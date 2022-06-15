"""Helper types."""

from typing import Optional, TypedDict


class ChainData(TypedDict):
    """Helper type for chain data stored in the config file."""

    name: str
    rippled: str
    config: str
    pid: int
    ws_ip: str
    ws_port: int
    http_ip: str
    http_port: Optional[int]


class WitnessData(TypedDict):
    """Helper type for witness data stored in the config file."""

    name: str
    witnessd: str
    config: str
    pid: int
    ip: str
    rpc_port: int
