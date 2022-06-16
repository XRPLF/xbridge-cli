"""Fund an account from the genesis account."""

from pprint import pprint

import click
from xrpl.models import AccountInfo, GenericRequest, Payment, SignAndSubmit
from xrpl.utils import xrp_to_drops
from xrpl.wallet import Wallet

from sidechain_cli.utils import get_config


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
    chain_config = get_config().get_chain(chain)
    client = chain_config.get_client()

    wallet = Wallet("snoPBrXtMeMyMHUVTgbuqAfg1SUTb", 0)
    payment = Payment(
        account=wallet.classic_address, destination=account, amount=xrp_to_drops(1000)
    )
    client.request(SignAndSubmit(transaction=payment, secret=wallet.seed))
    client.request(GenericRequest(method="ledger_accept"))
    if verbose:
        pprint(client.request(AccountInfo(account=account)).result)
