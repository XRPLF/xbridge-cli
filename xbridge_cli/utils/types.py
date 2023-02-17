"""Helper types."""

from typing import Literal, Optional, Tuple, TypedDict, Union

from typing_extensions import NotRequired


class ServerData(TypedDict):
    """Helper type for server data stored in the config file."""

    name: str
    type: Union[Literal["rippled"], Literal["witness"]]
    pid: int
    exe: str
    config: str
    http_ip: str
    http_port: int


class ChainData(ServerData):
    """Helper type for chain data stored in the config file."""

    ws_ip: str
    ws_port: int


class WitnessData(ServerData):
    """Helper type for witness data stored in the config file."""

    pass


class CurrencyDict(TypedDict):
    """Helper type for a currency dictionary."""

    currency: str
    issuer: NotRequired[str]


class BridgeData(TypedDict):
    """Helper type for bridge data stored in the config file."""

    name: str
    chains: Tuple[str, str]
    quorum: int
    door_accounts: Tuple[str, str]
    xchain_currencies: Tuple[CurrencyDict, CurrencyDict]
    signature_reward: str
    create_account_amounts: Tuple[Optional[str], Optional[str]]
