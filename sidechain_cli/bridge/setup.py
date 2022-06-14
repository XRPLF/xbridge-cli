"""CLI command for setting up a bridge."""

import json
from typing import Any, Dict, List, Tuple, cast

import click
from xrpl.models import IssuedCurrency

from sidechain_cli.utils import BridgeData
from sidechain_cli.utils import Currency as CurrencyDict
from sidechain_cli.utils import (
    add_bridge,
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
                return json.load(f)

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
    help="The chains that the bridge goes between.",
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
    """Set up a bridge between a mainchain and sidechain."""
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


@click.command(name="build")
@click.argument("bridge", type=str)
def setup_bridge(bridge: str) -> None:
    """Set up a bridge between a mainchain and sidechain."""
    print("BUILDING BRIDGE", bridge)
