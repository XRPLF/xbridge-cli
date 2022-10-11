"""Helper types."""

from typing import Literal, Tuple, TypedDict, Union


class ServerData(TypedDict):
    """Helper type for server data stored in the config file."""

    name: str
    type: Union[Literal["rippled"], Literal["witness"]]
    pid: int
    exe: str


class ChainData(ServerData):
    """Helper type for chain data stored in the config file."""

    config: str
    ws_ip: str
    ws_port: int
    http_ip: str
    http_port: int


class WitnessData(ServerData):
    """Helper type for witness data stored in the config file."""

    config: str
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
    num_witnesses: int
    door_accounts: Tuple[str, str]
    xchain_currencies: Tuple[Currency, Currency]
    signature_reward: str
    create_account_amounts: Tuple[str, str]
