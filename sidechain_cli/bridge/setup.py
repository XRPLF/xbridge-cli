"""CLI command for setting up a bridge."""

import json
from typing import Any, Dict, List, Literal, Tuple, Union, cast

import click
from xrpl.clients import JsonRpcClient
from xrpl.models import (
    GenericRequest,
    IssuedCurrency,
    Sidechain,
    Sign,
    SignerEntry,
    XChainDoorCreate,
)
from xrpl.wallet import Wallet

from sidechain_cli.utils import BridgeData
from sidechain_cli.utils import Currency as CurrencyDict
from sidechain_cli.utils import (
    add_bridge,
    check_bridge_exists,
    check_chain_exists,
    check_witness_exists,
    get_config,
)


def _str_to_currency(token: str) -> CurrencyDict:
    if token == "XRP":
        return "XRP"
    if token.count(".") != 1:
        raise Exception(
            f'Token {token} not a valid token. Must be "XRP" or of the form '
            '"BTC.issuer".'
        )
    currency, issuer = token.split(".")
    return cast(
        CurrencyDict, IssuedCurrency(currency=currency, issuer=issuer).to_dict()
    )


def _get_witness_json(name: str) -> Dict[str, Any]:
    config = get_config()
    for witness in config.witnesses:
        if witness["name"] == name:
            witness_config = witness["config"]
            with open(witness_config) as f:
                return cast(Dict[str, Any], json.load(f))

    raise Exception("No witness with that name.")


@click.command(name="create")
@click.option(
    "--name",
    required=True,
    prompt=True,
    help="The name of the bridge (used for differentiation purposes).",
)
@click.option(
    "--chains",
    required=True,
    nargs=2,
    type=str,
    help="The two chains that the bridge goes between.",
)
@click.option(
    "--witness",
    "witnesses",
    required=True,
    multiple=True,
    type=str,
    help="The witness servers that monitor the bridge.",
)
@click.option(
    "--verbose", is_flag=True, help="Whether or not to print more verbose information."
)
def create_bridge(
    name: str, chains: Tuple[str, str], witnesses: List[str], verbose: bool = True
) -> None:
    """
    Keep track of a bridge between a mainchain and sidechain.

    Args:
        name: The name of the bridge (used for differentiation purposes).
        chains: The two chains that the bridge goes between.
        witnesses: The witness server(s) that monitor the bridge.
        verbose: Whether or not to print more verbose information.
    """
    # check name
    if check_bridge_exists(name):
        print(f"Bridge named {name} already exists.")
        return
    # validate chains
    for chain in chains:
        if not check_chain_exists(chain):
            print(f"Chain {chain} is not running.")
            return
    # validate witnesses
    for witness in witnesses:
        if not check_witness_exists(witness):
            print(f"Witness {witness} is not running.")
            return

    config = _get_witness_json(witnesses[0])
    doors = (
        config["sidechain"]["src_chain_door"],
        config["sidechain"]["dst_chain_door"],
    )
    tokens = (
        config["sidechain"]["src_chain_issue"],
        config["sidechain"]["dst_chain_issue"],
    )

    bridge_data: BridgeData = {
        "name": name,
        "chains": chains,
        "witnesses": witnesses,
        "door_accounts": doors,
        "xchain_currencies": tokens,
    }

    add_bridge(bridge_data)


def _get_bridge(name: str) -> BridgeData:
    config = get_config()
    for bridge in config.bridges:
        if bridge["name"] == name:
            return cast(BridgeData, bridge)
    raise Exception(f"No bridge with name {name}.")


def _to_issued_currency(
    xchain_currency: Union[Literal["XRP"], CurrencyDict]
) -> Union[Literal["XRP"], IssuedCurrency]:
    return (
        cast(Literal["XRP"], "XRP")
        if xchain_currency == "XRP"
        else cast(
            IssuedCurrency,
            IssuedCurrency.from_dict(cast(Dict[str, Any], xchain_currency)),
        )
    )


@click.command(name="build")
@click.option(
    "--bridge", required=True, prompt=True, type=str, help="The bridge to build."
)
@click.option(
    "--bootstrap",
    required=True,
    prompt=True,
    type=click.Path(exists=True),
    help="The filepath to the bootstrap config file.",
)
def setup_bridge(bridge: str, bootstrap: str) -> None:
    """
    Set up a bridge between a mainchain and sidechain.

    Args:
        bridge: The bridge to build.
        bootstrap: The filepath to the bootstrap config file.
    """
    bridge_config = _get_bridge(bridge)
    with open(bootstrap) as f:
        bootstrap_config = json.load(f)

    signer_entries = []
    for witness in bridge_config["witnesses"]:
        witness_config = _get_witness_json(witness)
        account = Wallet(witness_config["signing_key_seed"], 0).classic_address
        signer_entries.append(SignerEntry(account=account, signer_weight=1))

    src_chain_issue = _to_issued_currency(bridge_config["xchain_currencies"][0])
    dst_chain_issue = _to_issued_currency(bridge_config["xchain_currencies"][1])

    create_tx1 = XChainDoorCreate(
        account=bridge_config["door_accounts"][0],
        sidechain=Sidechain(
            src_chain_door=bridge_config["door_accounts"][0],
            src_chain_issue=src_chain_issue,
            dst_chain_door=bridge_config["door_accounts"][1],
            dst_chain_issue=dst_chain_issue,
        ),
        signer_entries=signer_entries,
        signer_quorum=max(1, len(signer_entries)),
    )
    client1 = JsonRpcClient("http://localhost:5005")
    client1.request(
        Sign(transaction=create_tx1, secret=bootstrap_config["mainchain_door"]["seed"])
    )
    client1.request(GenericRequest(method="ledger_accept"))

    create_tx2 = XChainDoorCreate(
        account=bridge_config["door_accounts"][1],
        sidechain=Sidechain(
            src_chain_door=bridge_config["door_accounts"][0],
            src_chain_issue=src_chain_issue,
            dst_chain_door=bridge_config["door_accounts"][1],
            dst_chain_issue=dst_chain_issue,
        ),
        signer_entries=signer_entries,
        signer_quorum=max(1, len(signer_entries)),
    )
    client2 = JsonRpcClient("http://localhost:5006")
    client2.request(
        Sign(transaction=create_tx2, secret=bootstrap_config["sidechain_door"]["seed"])
    )
    client2.request(GenericRequest(method="ledger_accept"))
