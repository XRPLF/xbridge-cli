"""CLI command for setting up a bridge."""

import json
import os
from pprint import pformat
from typing import List, Optional

import click
from xrpl import CryptoAlgorithm
from xrpl.account import does_account_exist
from xrpl.clients import JsonRpcClient
from xrpl.models import (
    XRP,
    AccountSet,
    AccountSetFlag,
    Currency,
    IssuedCurrency,
    Payment,
    ServerState,
    SignerEntry,
    SignerListSet,
    Transaction,
    TrustSet,
    XChainBridge,
    XChainCreateBridge,
)
from xrpl.wallet import Wallet

from xbridge_cli.exceptions import XBridgeCLIException
from xbridge_cli.utils import (
    BridgeData,
    CryptoAlgorithmChoice,
    add_bridge,
    check_bridge_exists,
    submit_tx,
)
from xbridge_cli.utils.misc import is_standalone_network

_GENESIS_ACCOUNT = "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh"
_GENESIS_SEED = "snoPBrXtMeMyMHUVTgbuqAfg1SUTb"
_GENESIS_WALLET = Wallet(_GENESIS_SEED, 0)


@click.command(name="build")
@click.option(
    "--name",
    required=True,
    prompt=True,
    help="The name of the bridge (used for differentiation purposes).",
)
@click.option(
    "--bootstrap",
    envvar="XCHAIN_CONFIG_DIR",
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
    "--funding_seed",
    help=(
        "The master key of an account on the locking chain that can fund accounts on "
        "the issuing chain. This is only needed for an XRP-XRP bridge."
    ),
)
@click.option(
    "--funding_algorithm",
    type=CryptoAlgorithmChoice,
    help="The algorithm used to generate the keypair from the funding seed.",
)
@click.option(
    "--close-ledgers/--no-close-ledgers",
    "close_ledgers",
    default=True,
    help=(
        "Whether to close ledgers manually (via `ledger_accept`) or wait for ledgers "
        "to close automatically. A standalone node requires ledgers to be closed; an "
        "external network does not support ledger closing."
    ),
)
@click.option(
    "-v",
    "--verbose",
    help="Whether or not to print more verbose information. Also supports `-vv`.",
    count=True,
)
def setup_bridge(
    name: str,
    bootstrap: str,
    signature_reward: str,
    funding_seed: Optional[str] = None,
    funding_algorithm: Optional[str] = None,
    close_ledgers: bool = True,
    verbose: int = 0,
) -> None:
    """
    Keep track of a bridge between a locking chain and issuing chain.
    \f

    Args:
        name: The name of the bridge (used for differentiation purposes).
        bootstrap: The filepath to the bootstrap config file.
        signature_reward: The reward for witnesses providing a signature.
        funding_seed: The master key of an account on the locking chain that can fund
            accounts on the issuing chain. This is only needed for an XRP-XRP bridge.
            If not provided, uses the genesis seed.
        funding_algorithm: The algorithm used to generate the keypair from the funding
            seed.
        close_ledgers: Whether to close ledgers manually (via `ledger_accept`) or wait
            for ledgers to close automatically. A standalone node requires ledgers to
            be closed; an external network does not support ledger closing.
        verbose: Whether or not to print more verbose information. Add more v's for
            more verbosity.

    Raises:
        XBridgeCLIException: If an account on the locking chain doesn't exist
            (namely, the witness reward or submit accounts or the door account).
    """  # noqa: D301
    # check name
    if check_bridge_exists(name):
        raise XBridgeCLIException(f"Bridge named {name} already exists.")

    if bootstrap == os.getenv("XCHAIN_CONFIG_DIR"):
        bootstrap = os.path.join(bootstrap, "bridge_bootstrap.json")

    with open(bootstrap) as f:
        bootstrap_config = json.load(f)

    bootstrap_locking = bootstrap_config["LockingChain"]
    bootstrap_issuing = bootstrap_config["IssuingChain"]

    locking_endpoint = bootstrap_locking["Endpoint"]
    locking_url = f"http://{locking_endpoint['Host']}:{locking_endpoint['JsonRPCPort']}"
    locking_client = JsonRpcClient(locking_url)

    issuing_endpoint = bootstrap_issuing["Endpoint"]
    issuing_url = f"http://{issuing_endpoint['Host']}:{issuing_endpoint['JsonRPCPort']}"
    issuing_client = JsonRpcClient(issuing_url)

    if not is_standalone_network(locking_client) and close_ledgers:
        raise XBridgeCLIException(
            "Must use `--no-close-ledgers` on a non-standalone node."
        )

    locking_door = bootstrap_locking["DoorAccount"]["Address"]
    locking_issue = bootstrap_locking["BridgeIssue"]
    issuing_door = bootstrap_issuing["DoorAccount"]["Address"]
    issuing_issue = bootstrap_issuing["BridgeIssue"]

    if locking_issue == {"currency": "XRP"}:
        locking_chain_issue: Currency = XRP()
    else:
        locking_chain_issue = IssuedCurrency.from_dict(locking_issue)
    if issuing_issue == {"currency": "XRP"}:
        issuing_chain_issue: Currency = XRP()
    else:
        issuing_chain_issue = IssuedCurrency.from_dict(issuing_issue)

    bridge_obj = XChainBridge(
        locking_chain_door=locking_door,
        locking_chain_issue=locking_chain_issue,
        issuing_chain_door=issuing_door,
        issuing_chain_issue=issuing_chain_issue,
    )

    is_xrp_bridge = locking_chain_issue == XRP()

    if funding_seed is None:
        if bridge_obj.issuing_chain_issue == XRP() and funding_seed is None:
            if close_ledgers:
                funding_seed = "snoPBrXtMeMyMHUVTgbuqAfg1SUTb"
            else:
                raise XBridgeCLIException(
                    "Must include `funding_seed` for external XRP-XRP bridge."
                )

    accounts_locking_check = set(
        [locking_door]
        + bootstrap_locking["WitnessRewardAccounts"]
        + bootstrap_locking["WitnessSubmitAccounts"]
    )
    accounts_issuing_check = set(
        bootstrap_issuing["WitnessRewardAccounts"]
        + bootstrap_issuing["WitnessSubmitAccounts"]
    )

    # check locking chain for accounts that should already exist
    for account in accounts_locking_check:
        if not does_account_exist(account, locking_client):
            raise XBridgeCLIException(
                f"Account {account} does not exist on the locking chain."
            )
    # make sure issuing door account exists
    if not does_account_exist(issuing_door, issuing_client):
        raise XBridgeCLIException(
            f"Issuing chain door {issuing_door} does not exist on the locking chain."
        )
    if bridge_obj.issuing_chain_issue != XRP():
        # if a bridge is an XRP bridge, then the accounts need to be created via the
        # bridge (the bridge that doesn't exist yet)
        # so we only check if accounts already exist on the issuing chain for IOU
        # bridges
        for account in accounts_issuing_check:
            if not does_account_exist(account, issuing_client):
                raise XBridgeCLIException(
                    f"Account {account} does not exist on the issuing chain."
                )

    # get min create account amount values
    if is_xrp_bridge:
        server_state1 = locking_client.request(ServerState())
        min_create1 = server_state1.result["state"]["validated_ledger"]["reserve_base"]
        server_state2 = issuing_client.request(ServerState())
        min_create2 = server_state2.result["state"]["validated_ledger"]["reserve_base"]
    else:
        min_create1 = None
        min_create2 = None

    # set up signer entries for multisign on the door accounts
    signer_entries = []
    for witness_entry in bootstrap_config["Witnesses"]["SignerList"]:
        signer_entries.append(
            SignerEntry(
                account=witness_entry["Account"], signer_weight=witness_entry["Weight"]
            )
        )

    locking_door_seed = bootstrap_locking["DoorAccount"]["Seed"]
    locking_door_seed_algo = bootstrap_locking["DoorAccount"]["KeyType"]
    locking_door_wallet = Wallet(
        locking_door_seed, 0, algorithm=CryptoAlgorithm(locking_door_seed_algo)
    )
    issuing_door_seed = bootstrap_issuing["DoorAccount"]["Seed"]
    issuing_door_seed_algo = bootstrap_issuing["DoorAccount"]["KeyType"]
    issuing_door_wallet = Wallet(
        issuing_door_seed, 0, algorithm=CryptoAlgorithm(issuing_door_seed_algo)
    )

    ###################################################################################
    # set up locking chain
    transactions: List[Transaction] = []

    # create the trustline (if IOU)
    if bridge_obj.locking_chain_issue != XRP():
        assert isinstance(bridge_obj.locking_chain_issue, IssuedCurrency)
        transactions.append(
            TrustSet(
                account=locking_door,
                limit_amount=bridge_obj.locking_chain_issue.to_amount("1000000000"),
            )
        )

    # create the bridge
    min_create2_rippled = str(min_create2) if min_create2 is not None else None
    transactions.append(
        XChainCreateBridge(
            account=locking_door,
            xchain_bridge=bridge_obj,
            signature_reward=signature_reward,
            min_account_create_amount=min_create2_rippled,
        )
    )

    # set up multisign on the door account
    transactions.append(
        SignerListSet(
            account=locking_door,
            signer_quorum=max(1, len(signer_entries) - 1),
            signer_entries=signer_entries,
        )
    )

    # disable the master key
    transactions.append(
        AccountSet(account=locking_door, set_flag=AccountSetFlag.ASF_DISABLE_MASTER)
    )

    # submit transactions
    submit_tx(
        transactions,
        locking_client,
        locking_door_wallet,
        verbose,
        close_ledgers,
    )

    ###################################################################################
    # set up issuing chain

    # create the bridge
    min_create1_rippled = str(min_create1) if min_create2 is not None else None
    create_tx2 = XChainCreateBridge(
        account=issuing_door,
        xchain_bridge=bridge_obj,
        signature_reward=signature_reward,
        min_account_create_amount=min_create1_rippled,
    )
    submit_tx(create_tx2, issuing_client, issuing_door_wallet, verbose, close_ledgers)

    if bridge_obj.issuing_chain_issue == XRP():
        # we need to create the witness reward + submission accounts

        assert funding_seed is not None  # for typing purposes - checked earlier
        funding_wallet_algo = (
            CryptoAlgorithm(funding_algorithm) if funding_algorithm else None
        )
        funding_wallet = Wallet(funding_seed, 0, algorithm=funding_wallet_algo)

        # TODO: add param to customize amount
        amount = str(min_create2 * 2)  # submit accounts need spare funds
        total_amount = 0

        # create the accounts
        acct_txs: List[Transaction] = []
        # send the funds for the accounts on the issuing chain from the genesis account
        for account in accounts_issuing_check:
            acct_txs.append(
                Payment(
                    account=_GENESIS_ACCOUNT,
                    destination=account,
                    amount=amount,
                )
            )
            total_amount += int(amount)
        submit_tx(acct_txs, issuing_client, _GENESIS_WALLET, verbose, close_ledgers)

        # set up the attestations for the commit
        for account in accounts_issuing_check:
            door_payment = Payment(
                account=funding_wallet.classic_address,
                destination=locking_door,
                amount=str(total_amount),
            )
            submit_tx(
                door_payment, locking_client, funding_wallet, verbose, close_ledgers
            )

    # set up multisign on the door account
    signer_tx2 = SignerListSet(
        account=issuing_door,
        signer_quorum=max(1, len(signer_entries) - 1),
        signer_entries=signer_entries,
    )

    # disable the master key
    disable_master_tx2 = AccountSet(
        account=issuing_door, set_flag=AccountSetFlag.ASF_DISABLE_MASTER
    )

    # submit transactions
    submit_tx(
        [signer_tx2, disable_master_tx2],
        issuing_client,
        issuing_door_wallet,
        verbose,
        close_ledgers,
    )

    # add bridge to CLI config
    bridge_data: BridgeData = {
        "name": name,
        "chains": (locking_url, issuing_url),
        "quorum": max(1, len(signer_entries) - 1),
        "door_accounts": (locking_door, issuing_door),
        "xchain_currencies": (locking_issue, issuing_issue),
        "signature_reward": signature_reward,
        "create_account_amounts": (str(min_create2), str(min_create1)),
    }

    if verbose:
        click.echo(pformat(bridge_data))
    add_bridge(bridge_data)
