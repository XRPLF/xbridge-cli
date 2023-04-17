"""Create/fund an account via a cross-chain transfer."""

from pprint import pformat
from typing import Optional

import click
from xrpl import CryptoAlgorithm
from xrpl.models import AccountInfo, XChainAccountCreateCommit
from xrpl.utils import drops_to_xrp, xrp_to_drops
from xrpl.wallet import Wallet

from xbridge_cli.exceptions import XBridgeCLIException
from xbridge_cli.utils import (
    CryptoAlgorithmChoice,
    get_config,
    submit_tx,
    wait_for_attestations,
)
from xbridge_cli.utils.misc import is_standalone_network


@click.command(name="create-account")
@click.option(
    "--from_locking/--from_issuing",
    "from_locking",
    required=True,
    prompt=True,
    help=(
        "Whether funding from the locking chain or the issuing chain. "
        "Defaults to the locking chain."
    ),
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
    "--algorithm",
    type=CryptoAlgorithmChoice,
    help="The algorithm used to generate the keypair from the seed.",
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
    "--amount",
    default=None,
    type=int,
    help=(
        "The amount (in XRP) with which to fund the account. Must be greater than the "
        "account reserve. Defaults to the account reserve."
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
@click.option(
    "-s",
    "--silent",
    is_flag=True,
    help="Whether or not to print no information. Cannot be used with -v.",
)
def create_xchain_account(
    from_locking: bool,
    bridge: str,
    from_seed: str,
    to_account: str,
    algorithm: Optional[str] = None,
    amount: Optional[int] = None,
    close_ledgers: bool = True,
    verbose: int = 0,
    silent: bool = False,
) -> None:
    """
    Create an account on the opposite chain via a cross-chain transfer.
    \f

    Args:
        from_locking: Whether funding from the locking chain or the issuing chain.
            Defaults to the locking chain.
        bridge: The bridge across which to create the account.
        from_seed: The seed of the account that the funds come from.
        algorithm: The algorithm used to generate the keypair from the seed.
        to_account: The chain to fund an account on.
        amount: The amount with which to fund the account. Must be greater than the
            account reserve. Defaults to the account reserve.
        close_ledgers: Whether to close ledgers manually (via `ledger_accept`) or wait
            for ledgers to close automatically. A standalone node requires ledgers to
            be closed; an external network does not support ledger closing.
        verbose: Whether or not to print more verbose information. Add more v's for
            more verbosity.
        silent: Whether or not to print no information. Cannot be used with `-v`.

    Raises:
        XBridgeCLIException: Min create account isn't set or amount is less than the
            minimum account reserve, or timeout on attestations.
        AttestationTimeoutException: If there is a timeout when waiting for
            attestations.
    """  # noqa: D301
    if silent and verbose > 0:
        raise XBridgeCLIException("Cannot have verbose and silent flags.")
    verbosity = 0 if silent else 1 + verbose
    bridge_config = get_config().get_bridge(bridge)
    locking_client, issuing_client = bridge_config.get_clients()
    if from_locking:
        from_client = locking_client
        to_client = issuing_client
    else:
        from_client = issuing_client
        to_client = locking_client

    if not is_standalone_network(locking_client) and close_ledgers:
        raise XBridgeCLIException(
            "Must use `--no-close-ledgers` on a non-standalone node."
        )

    min_create_account_amount = bridge_config.create_account_amounts[
        0 if from_locking else 1
    ]
    if min_create_account_amount is None:
        raise XBridgeCLIException(
            "Cannot create a cross-chain account if the create account amount "
            "is not set."
        )

    if amount is None:
        create_amount = min_create_account_amount
    else:
        create_amount_xrp = drops_to_xrp(min_create_account_amount)
        if amount < create_amount_xrp:
            raise XBridgeCLIException(
                f"Amount must be greater than account reserve of {create_amount_xrp} "
                "XRP."
            )
        create_amount = xrp_to_drops(amount)

    wallet_algorithm = CryptoAlgorithm(algorithm) if algorithm else None
    from_wallet = Wallet(from_seed, 0, algorithm=wallet_algorithm)

    # submit XChainAccountCreate tx
    fund_tx = XChainAccountCreateCommit(
        account=from_wallet.classic_address,
        xchain_bridge=bridge_config.get_bridge(),
        signature_reward=bridge_config.signature_reward,
        destination=to_account,
        amount=create_amount,
    )
    submit_tx(fund_tx, from_client, from_wallet, verbosity, close_ledgers)

    # wait for attestations
    if verbosity > 0:
        click.secho(
            f"Waiting for attestations from the witness servers on {to_client.url}...",
            fg="blue",
        )

    wait_for_attestations(
        False,
        bridge_config,
        to_client,
        from_wallet,
        to_account,
        create_amount,
        None,
        close_ledgers,
        verbosity,
    )

    if verbosity > 1:
        click.echo(pformat(to_client.request(AccountInfo(account=to_account)).result))
