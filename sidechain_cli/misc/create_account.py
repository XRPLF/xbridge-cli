"""Create/fund an account via a cross-chain transfer."""

import time
from pprint import pformat

import click
from xrpl.clients import JsonRpcClient
from xrpl.models import (
    AccountInfo,
    GenericRequest,
    Ledger,
    Response,
    Transaction,
    Tx,
    XChainAccountCreateCommit,
)
from xrpl.wallet import Wallet

from sidechain_cli.utils import get_config, submit_tx

_ATTESTATION_TIME_LIMIT = 4  # in seconds
_WAIT_STEP_LENGTH = 0.05


def _submit_tx(
    tx: Transaction, client: JsonRpcClient, secret: str, verbose: int
) -> Response:
    result = submit_tx(tx, client, secret, verbose)
    tx_result = result.result.get("error") or result.result.get("engine_result")
    if tx_result != "tesSUCCESS":
        raise Exception(
            result.result.get("error_message")
            or result.result.get("engine_result_message")
        )
    tx_hash = result.result["tx_json"]["hash"]
    return client.request(Tx(transaction=tx_hash))


@click.command(name="create-account")
@click.option(
    "--chain",
    "from_chain",
    required=True,
    prompt=True,
    type=str,
    help="The chain to fund an account from.",
)
@click.option(
    "--bridge",
    required=True,
    prompt=True,
    type=str,
    help="The bridge across which to create the account.",
)
@click.option(
    "--from",
    "from_seed",
    required=True,
    prompt=True,
    type=str,
    help="The seed of the account that the funds come from.",
)
@click.option(
    "--to",
    "to_account",
    required=True,
    prompt=True,
    type=str,
    help="The account to fund on the opposite chain.",
)
@click.option(
    "-v",
    "--verbose",
    help="Whether or not to print more verbose information. Also supports `-vv`.",
    count=True,
)
def create_xchain_account(
    from_chain: str, bridge: str, from_seed: str, to_account: str, verbose: int = 0
) -> None:
    """
    Create an account on the opposite chain via a cross-chain transfer.
    \f

    Args:
        from_chain: The chain to fund an account from.
        bridge: The bridge across which to create the account.
        from_seed: The seed of the account that the funds come from.
        to_account: The chain to fund an account on.
        verbose: Whether or not to print more verbose information. Add more v's for
            more verbosity.
    """  # noqa: D301
    bridge_config = get_config().get_bridge(bridge)
    from_chain_config = get_config().get_chain(from_chain)
    from_client = from_chain_config.get_client()
    to_chain = [chain for chain in bridge_config.chains if chain != from_chain][0]
    to_chain_config = get_config().get_chain(to_chain)
    to_client = to_chain_config.get_client()
    create_account_amount = bridge_config.create_account_amounts[
        bridge_config.chains.index(from_chain)
    ]

    from_wallet = Wallet(from_seed, 0)

    if create_account_amount is None:
        click.secho(
            "Error: Cannot create a cross-chain account if the create account amount "
            "is not set.",
            fg="red",
        )
        return

    # submit XChainAccountCreate tx
    fund_tx = XChainAccountCreateCommit(
        account=from_wallet.classic_address,
        xchain_bridge=bridge_config.get_bridge(),
        signature_reward=bridge_config.signature_reward,
        destination=to_account,
        amount=create_account_amount,
    )
    submit_tx(fund_tx, from_client, from_wallet.seed, verbose)

    # wait for attestations
    time_count = 0.0
    attestation_count = 0
    while True:
        time.sleep(_WAIT_STEP_LENGTH)
        open_ledger = to_client.request(
            Ledger(ledger_index="current", transactions=True, expand=True)
        )
        open_txs = open_ledger.result["ledger"]["transactions"]
        for tx in open_txs:
            from pprint import pprint

            pprint(tx)
            if tx["TransactionType"] == "XChainAddAttestation":
                batch = tx["XChainAttestationBatch"]
                if batch["XChainBridge"] != bridge_config.to_xrpl():
                    # make sure attestation is for this bridge
                    continue
                attestations = batch["XChainCreateAccountAttestationBatch"]
                for attestation in attestations:
                    element = attestation["XChainCreateAccountAttestationBatchElement"]
                    # check that the attestation actually matches this transfer
                    if element["Account"] != from_wallet.classic_address:
                        continue
                    if element["Amount"] != create_account_amount:
                        continue
                    if element["Destination"] != to_account:
                        continue
                    attestation_count += 1
                    if verbose > 1:
                        click.echo(pformat(element))
                    if verbose > 0:
                        click.secho(
                            f"Received {attestation_count} attestations",
                            fg="bright_green",
                        )
        if len(open_txs) > 0:
            to_client.request(GenericRequest(method="ledger_accept"))
            time_count = 0
        else:
            time_count += _WAIT_STEP_LENGTH

        quorum = max(1, len(bridge_config.witnesses) - 1)
        if attestation_count >= quorum:
            # received enough attestations for quorum
            break

        if time_count > _ATTESTATION_TIME_LIMIT:
            click.secho("Error: Timeout on attestations.", fg="red")
            return

    if verbose > 0:
        click.echo(pformat(to_client.request(AccountInfo(account=to_account)).result))
