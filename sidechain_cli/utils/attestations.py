"""Helper methods regarding attestations."""

import time
from pprint import pformat
from typing import Optional

import click
from xrpl.clients import JsonRpcClient
from xrpl.models import GenericRequest, Ledger
from xrpl.wallet import Wallet

from sidechain_cli.exceptions import AttestationTimeoutException, SidechainCLIException
from sidechain_cli.utils.config_file import BridgeConfig

_ATTESTATION_TIME_LIMIT = 10  # in seconds
_WAIT_STEP_LENGTH = 0.05


def wait_for_attestations(
    is_transfer: bool,
    bridge_config: BridgeConfig,
    to_client: JsonRpcClient,
    from_wallet: Wallet,
    to_account: str,
    amount: str,
    xchain_claim_id: Optional[int] = None,
    verbose: int = 0,
) -> None:
    """
    Helper method to wait for attestations.

    Args:
        is_transfer: True if the attestation is for a transfer, False if it is for an
            account create.
        bridge_config: The bridge details.
        to_client: The client on the chain the transfer is going to.
        from_wallet: The account that the transfer is coming from.
        to_account: The account that the transfer is going to.
        amount: The amount that the transfer is for.
        xchain_claim_id: The XChainClaimID for a transfer (not needed for an account
            create).
        verbose: The verbosity of the output.

    Raises:
        AttestationTimeoutException: If the method times out while waiting for an
            attestation.
        SidechainCLIException: If the method is waiting for a transfer and there is no
            claim ID provided.
    """
    if is_transfer and xchain_claim_id is None:
        raise SidechainCLIException("Must have XChain Claim ID if is transfer.")

    if is_transfer:
        batch_name = "XChainClaimAttestationBatch"
    else:
        batch_name = "XChainCreateAccountAttestationBatch"

    time_count = 0.0
    attestation_count = 0
    while True:
        time.sleep(_WAIT_STEP_LENGTH)
        open_ledger = to_client.request(
            Ledger(ledger_index="current", transactions=True, expand=True)
        )
        open_txs = open_ledger.result["ledger"]["transactions"]
        for tx in open_txs:
            if tx["TransactionType"] == "XChainAddAttestation":
                batch = tx["XChainAttestationBatch"]
                if batch["XChainBridge"] != bridge_config.to_xrpl():
                    # make sure attestation is for this bridge
                    continue
                attestations = batch[batch_name]
                for attestation in attestations:
                    element = attestation[f"{batch_name}Element"]
                    # check that the attestation actually matches this transfer
                    if element["Account"] != from_wallet.classic_address:
                        continue
                    if element["Amount"] != amount:
                        continue
                    if element["Destination"] != to_account:
                        continue
                    if is_transfer:
                        if element["XChainClaimID"] != xchain_claim_id:
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

        quorum = max(1, bridge_config.num_witnesses - 1)
        if attestation_count >= quorum:
            # received enough attestations for quorum
            break

        if time_count > _ATTESTATION_TIME_LIMIT:
            raise AttestationTimeoutException()
