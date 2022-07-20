"""CLI command for setting up a bridge."""

import json
from typing import List, Tuple, cast

import click
from xrpl.models import (
    GenericRequest,
    IssuedCurrency,
    SignerEntry,
    SignerListSet,
    XChainCreateBridge,
)

from sidechain_cli.utils import BridgeData
from sidechain_cli.utils import Currency as CurrencyDict
from sidechain_cli.utils import (
    add_bridge,
    check_bridge_exists,
    check_chain_exists,
    check_witness_exists,
    get_config,
    submit_tx,
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

    config = get_config().get_witness((witnesses[0])).get_config()
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
@click.option(
    "--signature_reward",
    default="100",
    help="The reward for witnesses providing a signature.",
)
@click.option(
    "--verbose", is_flag=True, help="Whether or not to print more verbose information."
)
def setup_bridge(
    bridge: str, bootstrap: str, signature_reward: str, verbose: bool = False
) -> None:
    """
    Set up a bridge between a mainchain and sidechain.

    Args:
        bridge: The bridge to build.
        bootstrap: The filepath to the bootstrap config file.
        signature_reward: The reward for witnesses providing a signature.
        verbose: Whether or not to print more verbose information.
    """
    bridge_config = get_config().get_bridge(bridge)
    with open(bootstrap) as f:
        bootstrap_config = json.load(f)

    chain1 = get_config().get_chain(bridge_config.chains[0])
    client1 = chain1.get_client()
    chain2 = get_config().get_chain(bridge_config.chains[1])
    client2 = chain2.get_client()

    signer_entries = []
    for witness in bridge_config.witnesses:
        witness_config = get_config().get_witness((witness)).get_config()
        # TODO: refactor to avoid using wallet_propose
        wallet_propose = GenericRequest(
            method="wallet_propose",
            seed=witness_config["signing_key_seed"],
            key_type="ed25519",
        )
        account = client1.request(wallet_propose).result["account_id"]
        signer_entries.append(SignerEntry(account=account, signer_weight=1))
    bridge_obj = bridge_config.get_bridge()

    create_tx1 = XChainCreateBridge(
        account=bridge_config.door_accounts[0],
        xchain_bridge=bridge_obj,
        signature_reward=signature_reward
        # TODO: add support for the create account amount
    )
    submit_tx(create_tx1, client1, bootstrap_config["mainchain_door"]["seed"], verbose)

    signer_tx1 = SignerListSet(
        account=bridge_config.door_accounts[0],
        signer_quorum=max(1, len(signer_entries) - 1),
        signer_entries=signer_entries,
    )
    submit_tx(signer_tx1, client1, bootstrap_config["mainchain_door"]["seed"], verbose)

    # TODO: disable master key

    create_tx2 = XChainCreateBridge(
        account=bridge_config.door_accounts[1],
        xchain_bridge=bridge_obj,
        signature_reward=signature_reward
        # TODO: add support for the create account amount
    )
    submit_tx(create_tx2, client2, bootstrap_config["sidechain_door"]["seed"], verbose)

    signer_tx2 = SignerListSet(
        account=bridge_config.door_accounts[1],
        signer_quorum=max(1, len(signer_entries) - 1),
        signer_entries=signer_entries,
    )
    submit_tx(signer_tx2, client2, bootstrap_config["sidechain_door"]["seed"], verbose)

    # TODO: disable master key
