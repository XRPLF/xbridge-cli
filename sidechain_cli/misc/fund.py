"""Fund an account from the genesis account."""

from pprint import pprint
from typing import cast

import click
from xrpl.clients import JsonRpcClient
from xrpl.models import AccountInfo, GenericRequest, Payment
from xrpl.transaction import safe_sign_and_autofill_transaction, submit_transaction
from xrpl.utils import xrp_to_drops
from xrpl.wallet import Wallet

from sidechain_cli.utils import ChainData, get_config


def _get_chain(name: str) -> ChainData:
    config = get_config()
    for chain in config.chains:
        if chain["name"] == name:
            return cast(ChainData, chain)
    raise Exception(f"No chain with name {name}.")


@click.command(name="fund")
@click.option(
    "--chain",
    required=True,
    prompt=True,
    type=str,
    help="The chain to fund an account on.",
)
@click.option(
    "--account",
    required=True,
    prompt=True,
    type=str,
    help="The account to fund.",
)
@click.option(
    "--verbose", is_flag=True, help="Whether or not to print more verbose information."
)
def fund_account(chain: str, account: str, verbose: bool = False) -> None:
    """
    Fund an account from the genesis account. Only works on a normal standalone rippled
    node.
    \f

    Args:
        chain: The chain to fund an account on.
        account: The chain to fund an account on.
        verbose: Whether or not to print more verbose information.
    """  # noqa: D301
    chain_config = _get_chain(chain)
    client = JsonRpcClient(
        f"http://{chain_config['http_ip']}:{chain_config['http_port']}"
    )

    wallet = Wallet("snoPBrXtMeMyMHUVTgbuqAfg1SUTb", 0)
    payment = Payment(
        account=wallet.classic_address, destination=account, amount=xrp_to_drops(1000)
    )
    signed = safe_sign_and_autofill_transaction(payment, wallet, client)
    submit_transaction(signed, client)
    client.request(GenericRequest(method="ledger_accept"))
    if verbose:
        pprint(client.request(AccountInfo(account=account)).result)
