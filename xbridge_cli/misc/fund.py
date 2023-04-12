"""Fund an account from the genesis account."""

from pprint import pformat
from typing import List

import click
from xrpl.models import AccountInfo, Payment, Transaction
from xrpl.utils import xrp_to_drops
from xrpl.wallet import Wallet

from xbridge_cli.exceptions import XBridgeCLIException
from xbridge_cli.utils import get_config, submit_tx


@click.command(name="fund")
@click.argument("chain", required=True, type=str)
@click.argument(
    "accounts",
    required=True,
    type=str,
    nargs=-1,
)
@click.option(
    "--amount", type=int, default=1000, help="The amount to fund each account (in XRP)."
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Whether or not to print more verbose information.",
)
def fund_account(
    chain: str, accounts: List[str], amount: int = 1000, verbose: bool = False
) -> None:
    """
    Of the form `xbridge-cli fund CHAIN ACCOUNT1 [ACCOUNT2 ...].

    Fund an account from the genesis account. Only works on a normal standalone rippled
    node.
    \f

    Args:
        chain: The chain to fund an account on.
        accounts: The account(s) to fund.
        amount: The amount to fund each account (in XRP).
        verbose: Whether or not to print more verbose information.

    Raises:
        XBridgeCLIException: If the chain is the issuing chain.
    """  # noqa: D301
    if chain == "issuing_chain":
        raise XBridgeCLIException(
            "Cannot fund account on issuing chain. Must use `create-account`."
        )

    chain_config = get_config().get_chain(chain)
    client = chain_config.get_client()

    wallet = Wallet("snoPBrXtMeMyMHUVTgbuqAfg1SUTb", 0)
    payments: List[Transaction] = []
    for account in accounts:
        payments.append(
            Payment(
                account=wallet.classic_address,
                destination=account,
                amount=xrp_to_drops(amount),
            )
        )
    submit_tx(payments, client, wallet)
    if verbose:
        for account in accounts:
            click.echo(pformat(client.request(AccountInfo(account=account)).result))
