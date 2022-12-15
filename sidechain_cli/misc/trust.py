"""Fund an account from the genesis account."""

from typing import List

import click
from xrpl.models import IssuedCurrencyAmount, Transaction, TrustSet
from xrpl.wallet import Wallet

from sidechain_cli.utils import get_config, submit_tx


@click.command(name="trust")
@click.argument(
    "chain",
    required=True,
    type=str,
)
@click.argument(
    "currency",
    required=True,
    type=str,
)
@click.argument(
    "accounts",
    required=True,
    type=str,
    nargs=-1,
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Whether or not to print more verbose information.",
)
def set_trustline(
    chain: str, currency: str, accounts: List[str], verbose: bool = False
) -> None:
    """
    Of the form `sidechain-cli trust CHAIN CURRENCY ACCOUNT1 [ACCOUNT2 ...].

    Set a trustline for a currency from an account or accounts.
    \f

    Args:
        chain: The chain to set the trustline on.
        currency: The currency of the trustline.
        accounts: The seeds of the account(s) setting the trustline.
        verbose: Whether or not to print more verbose information.
    """  # noqa: D301
    token, issuer = currency.split(".")

    chain_config = get_config().get_chain(chain)
    client = chain_config.get_client()

    trust_sets: List[Transaction] = []
    for account in accounts:
        wallet = Wallet(account, 0)
        trust_sets.append(
            TrustSet(
                account=wallet.classic_address,
                limit_amount=IssuedCurrencyAmount(
                    currency=token, issuer=issuer, value="10000000"
                ),
            )
        )
    submit_tx(trust_sets, client, wallet.seed)
    if verbose:
        pass
