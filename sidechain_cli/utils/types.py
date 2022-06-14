"""Helper types."""

from typing import List, Literal, Tuple, TypedDict, Union


class ChainData(TypedDict):
    """Helper type for chain data stored in the config file."""

    name: str
    rippled: str
    config: str
    pid: int
    ws_ip: str
    ws_port: int
    http_ip: str
    http_port: int


class WitnessData(TypedDict):
    """Helper type for witness data stored in the config file."""

    name: str
    witnessd: str
    config: str
    pid: int
    ip: str
    rpc_port: int


class IssuedCurrencyDict(TypedDict):
    """Helper type for an issued currency dictionary."""

    currency: str
    issuer: str


Currency = Union[Literal["XRP"], IssuedCurrencyDict]


class BridgeData(TypedDict):
    """Helper type for bridge data stored in the config file."""

    name: str
    chains: Tuple[str, str]
    witnesses: List[str]
    door_accounts: Tuple[str, str]
    xchain_currencies: Tuple[Currency, Currency]
