"""The main CLI call."""

import click

from sidechain_cli.bridge import bridge
from sidechain_cli.misc.explorer import launch_explorer
from sidechain_cli.misc.fund import fund_account
from sidechain_cli.misc.trust import set_trustline
from sidechain_cli.server import server

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(context_settings=CONTEXT_SETTINGS)
def main() -> None:
    """The Sidechain Command-Line Interface. Do everything with sidechains."""
    pass


main.add_command(server)
main.add_command(bridge)

main.add_command(fund_account)
main.add_command(launch_explorer)
main.add_command(set_trustline)


if __name__ == "__main__":
    main()
