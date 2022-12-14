"""CLI command for setting up a bridge."""

import json
import os
from pprint import pformat
from typing import Any, Dict, List, Optional, Tuple

import click
from xrpl.account import does_account_exist
from xrpl.clients import JsonRpcClient
from xrpl.core.binarycodec import encode
from xrpl.core.keypairs import sign
from xrpl.models import (
    XRP,
    AccountSet,
    AccountSetFlag,
    Currency,
    IssuedCurrency,
    ServerState,
    SignerEntry,
    SignerListSet,
    Transaction,
    TrustSet,
    XChainAccountCreateCommit,
    XChainAddAttestation,
    XChainBridge,
    XChainCreateBridge,
)
from xrpl.models.transactions.transaction import transaction_json_to_binary_codec_form
from xrpl.models.transactions.xchain_add_attestation import (
    XChainAttestationBatch,
    XChainCreateAccountAttestationBatchElement,
)
from xrpl.wallet import Wallet

from sidechain_cli.exceptions import SidechainCLIException
from sidechain_cli.utils import BridgeData, add_bridge, check_bridge_exists, submit_tx

_ATTESTATION_ENCODE_ORDER: List[Tuple[str, int]] = [
    ("account", 4),
    ("amount", 2),
    ("signature_reward", 4),
    ("attestation_reward_account", 6),
    ("was_locking_chain_send", 0),
    ("xchain_account_create_count", 4),
    ("destination", 4),
]


def _sign_attestation(
    attestation: XChainCreateAccountAttestationBatchElement,
    bridge: XChainBridge,
    private_key: str,
) -> XChainCreateAccountAttestationBatchElement:
    attestation_dict = attestation.to_dict()[
        "xchain_create_account_attestation_batch_element"
    ]
    # TODO: use this instead once it's been implemented
    # attestation_xrpl = transaction_json_to_binary_codec_form(attestation_dict)
    # encoded_obj = encode(attestation_xrpl)
    bridge_dict: Dict[str, Any] = {"xchain_bridge": bridge.to_dict()}
    encoded_obj = encode(transaction_json_to_binary_codec_form(bridge_dict))[4:]
    for key, prefix in _ATTESTATION_ENCODE_ORDER:
        value = attestation_dict[key]
        if key == "was_locking_chain_send":
            encoded_obj += "0" + str(value)
        else:
            xrpl_attestation = transaction_json_to_binary_codec_form({key: value})
            encoded_obj += encode(xrpl_attestation)[prefix:]
    signature = sign(bytes.fromhex(encoded_obj), private_key)
    attestation_dict["signature"] = signature
    signed_attestation = XChainCreateAccountAttestationBatchElement.from_dict(
        attestation_dict
    )
    return signed_attestation


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
@click.pass_context
def setup_bridge(
    ctx: click.Context,
    name: str,
    bootstrap: str,
    signature_reward: str,
    funding_seed: Optional[str] = None,
    close_ledgers: bool = True,
    verbose: int = 0,
) -> None:
    """
    Keep track of a bridge between a locking chain and issuing chain.
    \f

    Args:
        ctx: The click context.
        name: The name of the bridge (used for differentiation purposes).
        bootstrap: The filepath to the bootstrap config file.
        signature_reward: The reward for witnesses providing a signature.
        funding_seed: The master key of an account on the locking chain that can fund
            accounts on the issuing chain. This is only needed for an XRP-XRP bridge.
            If not provided, uses the genesis seed.
        close_ledgers: Whether to close ledgers manually (via `ledger_accept`) or wait
            for ledgers to close automatically. A standalone node requires ledgers to
            be closed; an external network does not support ledger closing.
        verbose: Whether or not to print more verbose information. Add more v's for
            more verbosity.

    Raises:
        SidechainCLIException: If an account on the locking chain doesn't exist
            (namely, the witness reward or submit accounts or the door account).
    """  # noqa: D301
    # check name
    if check_bridge_exists(name):
        raise SidechainCLIException(f"Bridge named {name} already exists.")

    if bootstrap == os.getenv("XCHAIN_CONFIG_DIR"):
        bootstrap = os.path.join(bootstrap, "bridge_bootstrap.json")

    with open(bootstrap) as f:
        bootstrap_config = json.load(f)

    locking_door = bootstrap_config["LockingChain"]["DoorAccount"]["Address"]
    locking_issue = bootstrap_config["LockingChain"]["BridgeIssue"]
    issuing_door = bootstrap_config["IssuingChain"]["DoorAccount"]["Address"]
    issuing_issue = bootstrap_config["IssuingChain"]["BridgeIssue"]

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
                raise SidechainCLIException(
                    "Must include `funding_seed` for external XRP-XRP bridge."
                )

    locking_endpoint = bootstrap_config["LockingChain"]["Endpoint"]
    locking_url = f"http://{locking_endpoint['IP']}:{locking_endpoint['JsonRPCPort']}"
    locking_client = JsonRpcClient(locking_url)

    issuing_endpoint = bootstrap_config["IssuingChain"]["Endpoint"]
    issuing_url = f"http://{issuing_endpoint['IP']}:{issuing_endpoint['JsonRPCPort']}"
    issuing_client = JsonRpcClient(issuing_url)

    accounts_locking_check = set(
        [locking_door]
        + bootstrap_config["LockingChain"]["WitnessRewardAccounts"]
        + bootstrap_config["LockingChain"]["WitnessSubmitAccounts"]
    )
    accounts_issuing_check = set(
        bootstrap_config["IssuingChain"]["WitnessRewardAccounts"]
        + bootstrap_config["IssuingChain"]["WitnessSubmitAccounts"]
    )

    # check locking chain for accounts that should already exist
    for account in accounts_locking_check:
        if not does_account_exist(account, locking_client):
            raise SidechainCLIException(
                f"Account {account} does not exist on the locking chain."
            )
    # make sure issuing door account exists
    if not does_account_exist(issuing_door, issuing_client):
        raise SidechainCLIException(
            f"Issuing chain door {issuing_door} does not exist on the locking chain."
        )
    if bridge_obj.issuing_chain_issue != XRP():
        # if a bridge is an XRP bridge, then the accounts need to be created via the
        # bridge (the bridge that doesn't exist yet)
        # so we only check if accounts already exist on the issuing chain for IOU
        # bridges
        for account in accounts_issuing_check:
            if not does_account_exist(account, issuing_client):
                raise SidechainCLIException(
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

    locking_door_seed = bootstrap_config["LockingChain"]["DoorAccount"]["Seed"]
    issuing_door_seed = bootstrap_config["IssuingChain"]["DoorAccount"]["Seed"]

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
        locking_door_seed,
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
    submit_tx(create_tx2, issuing_client, issuing_door_seed, verbose, close_ledgers)

    if bridge_obj.issuing_chain_issue == XRP():
        # we need to create the witness reward + submission accounts via the bridge

        # helper function for submitting the attestations
        def _submit_attestations(
            attestations: List[XChainCreateAccountAttestationBatchElement],
        ) -> None:
            attestation_tx = XChainAddAttestation(
                account=issuing_door,
                xchain_attestation_batch=XChainAttestationBatch(
                    xchain_bridge=bridge_obj,
                    xchain_claim_attestation_batch=[],
                    xchain_create_account_attestation_batch=attestations,
                ),
            )
            submit_tx(
                attestation_tx,
                issuing_client,
                issuing_door_seed,
                verbose,
                close_ledgers,
            )

        issuing_wallet = Wallet(issuing_door_seed, 0)

        assert funding_seed is not None  # for typing purposes - checked earlier
        funding_wallet = Wallet(funding_seed, 0)

        amount = str(min_create2 * 2)  # submit accounts need spare funds
        attestations = []
        count = 1

        # create the accounts
        acct_txs: List[Transaction] = []
        # commit the funds for the account
        for account in accounts_issuing_check:
            acct_txs.append(
                XChainAccountCreateCommit(
                    account=funding_wallet.classic_address,
                    xchain_bridge=bridge_obj,
                    signature_reward=signature_reward,
                    destination=account,
                    amount=amount,
                )
            )
        submit_tx(acct_txs, locking_client, funding_seed, verbose, close_ledgers)

        # set up the attestations for the commit
        for account in accounts_issuing_check:
            init_attestation = XChainCreateAccountAttestationBatchElement(
                account=funding_wallet.classic_address,
                amount=amount,
                attestation_reward_account=issuing_door,
                destination=account,
                public_key=issuing_wallet.public_key,
                signature="",
                signature_reward=signature_reward,
                was_locking_chain_send=1,
                xchain_account_create_count=str(count),
            )
            signed_attestation = _sign_attestation(
                init_attestation, bridge_obj, issuing_wallet.private_key
            )
            attestations.append(signed_attestation)
            count += 1

            # we can only have 8 attestations in an XChainAddAttestation tx
            if len(attestations) == 8:
                _submit_attestations(attestations)
                attestations = []

        _submit_attestations(attestations)

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
        issuing_door_seed,
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
