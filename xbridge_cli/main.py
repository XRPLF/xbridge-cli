"""The main CLI call."""

import click

from xbridge_cli.bridge import bridge
from xbridge_cli.misc.explorer import launch_explorer
from xbridge_cli.misc.fund import fund_accounts, fund_bootstrap_accounts
from xbridge_cli.misc.trust import set_trustline
from xbridge_cli.server import server

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(context_settings=CONTEXT_SETTINGS)
def main() -> None:
    """The XBridge Command-Line Interface. Do everything with XRPL-XRPL bridges."""
    pass


main.add_command(server)
main.add_command(bridge)

main.add_command(fund_accounts)
main.add_command(fund_bootstrap_accounts)
main.add_command(launch_explorer)
main.add_command(set_trustline)


if __name__ == "__main__":
    main()
