"""Register an existing bridge with the CLI."""

import json
from pprint import pformat
from typing import Any, Dict, List, Optional, Tuple, cast

import click
from xrpl.clients import JsonRpcClient
from xrpl.models import AccountObjects, AccountObjectType, ServerState

from xbridge_cli.exceptions import XBridgeCLIException
from xbridge_cli.utils import BridgeData, add_bridge, check_bridge_exists


def _get_account_objects(
    client: JsonRpcClient, account: str, obj_filter: Optional[AccountObjectType] = None
) -> List[Dict[str, Any]]:
    object_result = client.request(AccountObjects(account=account, type=obj_filter))
    return cast(List[Dict[str, Any]], object_result.result["account_objects"])


# TODO: add support for door accounts that have multiple bridges
def _get_bridge(
    client: JsonRpcClient, door_account: str, currency: str
) -> Dict[str, Any]:
    objects = _get_account_objects(client, door_account, AccountObjectType.BRIDGE)
    bridge_objects = [
        obj
        for obj in objects
        if obj["XChainBridge"]["LockingChainIssue"]["currency"] == currency
    ]
    assert len(bridge_objects) == 1
    return bridge_objects[0]


def _get_signers(client: JsonRpcClient, door_account: str) -> Dict[str, Any]:
    objects = _get_account_objects(client, door_account, AccountObjectType.SIGNER_LIST)
    assert len(objects) == 1
    return objects[0]


def _signers_equal(signers1: Dict[str, Any], signers2: Dict[str, Any]) -> bool:
    if len(signers1) != len(signers2):
        return False

    for signers in (signers1, signers2):
        del signers["PreviousTxnID"]
        del signers["PreviousTxnLgrSeq"]
        del signers["index"]
        del signers["SignerListID"]
        del signers["Flags"]
    return signers1 == signers2


def _get_bootstrap_chain_and_door(chain_json: Dict[str, Any]) -> Tuple[str, str]:
    endpoint = chain_json["Endpoint"]
    chain = f"http://{endpoint['Host']}:{endpoint['JsonRPCPort']}"
    door = chain_json["DoorAccount"]["Address"]
    return chain, door


@click.command(name="register")
@click.option(
    "--name",
    required=True,
    prompt=True,
    help="The name of the bridge (used for differentiation purposes).",
)
@click.option(
    "--bootstrap",
    type=click.Path(exists=True),
    help=(
        "The filepath to the bootstrap config file. Optional. If you don't have it, "
        "enter the info by hand."
    ),
)
@click.option(
    "--chains",
    nargs=2,
    type=str,
    help=(
        "The URLs for HTTP connections for the two chains that the bridge is between. "
        "Must be in the order (locking_chain, issuing_chain)."
    ),
)
@click.option(
    "--doors",
    nargs=2,
    type=str,
    help=(
        "The two door accounts. Must be in the order (locking_chain_door, "
        "issuing_chain_door)."
    ),
)
@click.option(
    "--currency",
    type=str,
    default="XRP",
    help=(
        "The currency that is being transferred across the bridge. The default is XRP."
    ),
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Whether or not to print more verbose information.",
)
def register_bridge(
    name: str,
    chains: Optional[Tuple[str, str]],
    doors: Optional[Tuple[str, str]],
    bootstrap: Optional[str],
    currency: str = "XRP",
    verbose: int = 0,
) -> None:
    """
    Register an existing bridge with the CLI and validate that it is set up correctly.
    \f

    Args:
        name: The name of the bridge (only used locally).
        chains: The locking chain and issuing chain.
        doors: The locking chain door and issuing chain door.
        currency: The currency that is being transferred across the bridge. The default
            is XRP.
        bootstrap: The bootstrap file.
        verbose: Whether or not to print more verbose information.

    Raises:
        XBridgeCLIException: If there are issues with the information passed in.
    """  # noqa: D301
    # check name
    if check_bridge_exists(name):
        raise XBridgeCLIException(f"Bridge named {name} already exists.")

    if bootstrap is not None:
        if chains is not None:
            raise XBridgeCLIException("Cannot have both `chains` and `bootstrap`.")
        if doors is not None:
            raise XBridgeCLIException("Cannot have both `doors` and `bootstrap`.")
        with open(bootstrap) as f:
            bootstrap_json = json.load(f)

        locking_chain, locking_door = _get_bootstrap_chain_and_door(
            bootstrap_json["LockingChain"]
        )
        issuing_chain, issuing_door = _get_bootstrap_chain_and_door(
            bootstrap_json["IssuingChain"]
        )
        chains = (locking_chain, issuing_chain)
        doors = (locking_door, issuing_door)
    else:
        if chains is None:
            raise XBridgeCLIException("Must have `chains` if no `bootstrap`.")
        if doors is None:
            raise XBridgeCLIException("Must have `doors` if no `bootstrap`.")

    locking_client = JsonRpcClient(chains[0])
    issuing_client = JsonRpcClient(chains[1])

    signer_list1 = _get_signers(locking_client, doors[0])
    signer_list2 = _get_signers(issuing_client, doors[1])
    if not _signers_equal(signer_list1, signer_list2):
        raise XBridgeCLIException(
            "The bridge was set up incorrectly. The Signer Lists are different on "
            "both chains."
        )

    quorum = signer_list1["SignerQuorum"]

    # TODO: determine whether the bridge was set up properly.
    bridge1 = _get_bridge(locking_client, doors[0], currency)
    bridge2 = _get_bridge(issuing_client, doors[1], currency)
    assert bridge1["XChainBridge"] == bridge2["XChainBridge"]
    assert bridge1["XChainAccountCreateCount"] == bridge2["XChainAccountClaimCount"]
    assert bridge2["XChainAccountCreateCount"] == bridge1["XChainAccountClaimCount"]

    server_state1 = locking_client.request(ServerState())
    min_create1 = server_state1.result["state"]["validated_ledger"]["reserve_base"]
    server_state2 = issuing_client.request(ServerState())
    min_create2 = server_state2.result["state"]["validated_ledger"]["reserve_base"]

    assert int(bridge1["MinAccountCreateAmount"]) == int(min_create2)
    assert int(bridge2["MinAccountCreateAmount"]) == int(min_create1)

    # add bridge to CLI config
    bridge_data: BridgeData = {
        "name": name,
        "chains": (chains[0], chains[1]),
        "quorum": quorum,
        "door_accounts": (doors[0], doors[1]),
        "xchain_currencies": (
            bridge1["XChainBridge"]["LockingChainIssue"],
            bridge1["XChainBridge"]["IssuingChainIssue"],
        ),
        "signature_reward": bridge1["SignatureReward"],
        "create_account_amounts": (str(min_create2), str(min_create1)),
    }

    if verbose:
        click.echo(pformat(bridge_data))
    add_bridge(bridge_data)
    return
