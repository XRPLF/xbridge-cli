"""Bridge information stored in the CLI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Literal, Tuple, Union, cast

from xrpl.clients import JsonRpcClient
from xrpl.models import IssuedCurrency, XChainBridge

from sidechain_cli.utils.config_file.config_item import ConfigItem
from sidechain_cli.utils.types import Currency


def _to_issued_currency(
    xchain_currency: Union[Literal["XRP"], Currency]
) -> Union[Literal["XRP"], IssuedCurrency]:
    return (
        cast(Literal["XRP"], "XRP")
        if xchain_currency == "XRP"
        else IssuedCurrency.from_dict(cast(Dict[str, Any], xchain_currency))
    )


@dataclass
class BridgeConfig(ConfigItem):
    """Object representing the config for a bridge."""

    name: str
    chains: Tuple[str, str]
    num_witnesses: int
    door_accounts: Tuple[str, str]
    xchain_currencies: Tuple[Currency, Currency]
    signature_reward: str
    create_account_amounts: Tuple[str, str]

    def get_clients(self: BridgeConfig) -> Tuple[JsonRpcClient, JsonRpcClient]:
        """
        Get the clients for the chains associated with the bridge.

        Returns:
            The clients for the chains associated with the bridge.
        """
        return (JsonRpcClient(self.chains[0]), JsonRpcClient(self.chains[1]))

    def get_bridge(self: BridgeConfig) -> XChainBridge:
        """
        Get the XChainBridge object associated with the bridge.

        Returns:
            The XChainBridge object.
        """
        locking_chain_issue = _to_issued_currency(self.xchain_currencies[0])
        issuing_chain_issue = _to_issued_currency(self.xchain_currencies[1])
        return XChainBridge(
            locking_chain_door=self.door_accounts[0],
            locking_chain_issue=locking_chain_issue,
            issuing_chain_door=self.door_accounts[1],
            issuing_chain_issue=issuing_chain_issue,
        )

    def to_xrpl(self: BridgeConfig) -> Dict[str, Any]:
        """
        Get the XRPL-formatted dictionary for the XChainBridge object.

        Returns:
            The XRPL-formatted dictionary for the XChainBridge object.
        """
        locking_chain_issue = _to_issued_currency(self.xchain_currencies[0])
        issuing_chain_issue = _to_issued_currency(self.xchain_currencies[1])
        return {
            "LockingChainDoor": self.door_accounts[0],
            "LockingChainIssue": locking_chain_issue,
            "IssuingChainDoor": self.door_accounts[1],
            "IssuingChainIssue": issuing_chain_issue,
        }
