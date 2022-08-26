"""Create/fund an account via a cross-chain transfer."""

from pprint import pformat

import click
import httpx
from xrpl.clients import JsonRpcClient
from xrpl.models import (
    AccountInfo,
    Response,
    SidechainXChainAccountCreate,
    Transaction,
    Tx,
    XChainAddAttestation,
)
from xrpl.models.transactions.xchain_add_attestation import (
    XChainAttestationBatch,
    XChainCreateAccountAttestationBatchElement,
)
from xrpl.wallet import Wallet

from sidechain_cli.utils import get_config, submit_tx


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
    "--verbose", is_flag=True, help="Whether or not to print more verbose information."
)
def create_xchain_account(
    from_chain: str, bridge: str, from_seed: str, to_account: str, verbose: bool = False
) -> None:
    """
    Create an account on the opposite chain via a cross-chain transfer.
    \f

    Args:
        from_chain: The chain to fund an account from.
        bridge: The bridge across which to create the account.
        from_seed: The seed of the account that the funds come from.
        to_account: The chain to fund an account on.
        verbose: Whether or not to print more verbose information.
    """  # noqa: D301
    tutorial = True
    print_level = 2

    bridge_config = get_config().get_bridge(bridge)
    from_chain_config = get_config().get_chain(from_chain)
    from_client = from_chain_config.get_client()
    to_chain = [chain for chain in bridge_config.chains if chain != from_chain][0]
    to_chain_config = get_config().get_chain(to_chain)
    to_client = to_chain_config.get_client()

    from_door = bridge_config.door_accounts[bridge_config.chains.index(from_chain)]

    from_wallet = Wallet(from_seed, 0)

    if bridge_config.create_account_amount is None:
        click.secho(
            "Error: Cannot create a cross-chain account if the create account amount "
            "is not set.",
            fg="red",
        )
        return

    # submit XChainAccountCreate tx
    fund_tx = SidechainXChainAccountCreate(
        account=from_wallet.classic_address,
        xchain_bridge=bridge_config.get_bridge(),
        signature_reward=bridge_config.signature_reward,
        destination=to_account,
        amount=bridge_config.create_account_amount,
    )
    submit_tx(fund_tx, from_client, from_wallet.seed, print_level)

    # fetch attestations
    proofs = []

    for witness in bridge_config.witnesses:
        witness_config = get_config().get_witness(witness)

        if tutorial:
            click.pause(
                info=click.style(
                    f"\nRetrieving the proofs from witness {witness_config.name}...",
                    fg="blue",
                )
            )

        witness_url = f"http://{witness_config.ip}:{witness_config.rpc_port}"
        proof_request = {
            "method": "witness_account_create",
            "params": [
                {
                    "sending_account": from_wallet.classic_address,
                    "sending_amount": bridge_config.create_account_amount,
                    "door": from_door,
                    "bridge": bridge_config.to_xrpl(),
                    "reward_amount": bridge_config.signature_reward,
                    "destination": to_account,
                    "reward_account": "rGcwshLFWRu3vXxGQagvKZDCSEH9rKcdZC",
                    "create_count": 1,
                }
            ],
        }

        proof_result = httpx.post(witness_url, json=proof_request).json()
        if print_level > 1:
            click.echo(pformat(proof_result))
        elif print_level > 0:
            click.echo(f"Proof from {witness_config.name} successfully received.")

        if "error" in proof_result:
            error_message = proof_result["error"]["error"]
            click.secho(f"Error: Request for proof failed: {error_message}", fg="red")
            return

        proof = proof_result["result"]["XChainAttestationBatch"][
            "XChainCreateAccountAttestationBatch"
        ][0]
        proofs.append(XChainCreateAccountAttestationBatchElement.from_xrpl(proof))

    attestation_tx = XChainAddAttestation(
        account="rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
        xchain_attestation_batch=XChainAttestationBatch(
            xchain_bridge=bridge_config.get_bridge(),
            xchain_claim_attestation_batch=[],
            xchain_create_account_attestation_batch=proofs,
        ),
    )

    # submit attestation
    _submit_tx(
        attestation_tx,
        to_client,
        "snoPBrXtMeMyMHUVTgbuqAfg1SUTb",
        print_level,
    )

    if verbose:
        click.echo(pformat(to_client.request(AccountInfo(account=to_account)).result))
