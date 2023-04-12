"""Fund an account from the genesis account."""

import json
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
def fund_accounts(
    chain: str, accounts: List[str], amount: int = 1000, verbose: bool = False
) -> None:
    """
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


@click.command(name="fund-bootstrap")
@click.argument("chain", required=True, type=str)
@click.argument(
    "bootstrap",
    required=True,
    type=click.Path(exists=True),
)
@click.option(
    "--amount", type=int, default=1000, help="The amount to fund each account."
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Whether or not to print more verbose information.",
)
@click.pass_context
def fund_bootstrap_accounts(
    ctx: click.Context,
    chain: str,
    bootstrap: str,
    amount: int = 1000,
    verbose: bool = False,
) -> None:
    """
    Fund all the locking chain accounts in the bootstrap file from the genesis account.
    Only works on a normal standalone rippled node.
    \f

    Args:
        ctx: The click context.
        chain: The chain to fund an account on.
        bootstrap: The bootstrap file.
        amount: The amount to fund each account.
        verbose: Whether or not to print more verbose information.

    Raises:
        XBridgeCLIException: If the chain is the issuing chain.
    """  # noqa: D301
    with open(bootstrap) as f:
        bootstrap_config = json.load(f)

    bootstrap_locking = bootstrap_config["LockingChain"]
    accounts_to_fund = (
        [bootstrap_locking["DoorAccount"]["Address"]]
        + bootstrap_locking["WitnessRewardAccounts"]
        + bootstrap_locking["WitnessSubmitAccounts"]
    )
    ctx.invoke(
        fund_accounts,
        chain=chain,
        accounts=accounts_to_fund,
        amount=amount,
        verbose=verbose,
    )
