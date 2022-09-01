"""The main CLI call."""

import click

from sidechain_cli.bridge import bridge
from sidechain_cli.misc.create_account import create_xchain_account
from sidechain_cli.misc.fund import fund_account
from sidechain_cli.server import server


@click.group()
def main() -> None:
    """The Sidechain Command-Line Interface. Do everything with sidechains."""
    pass


main.add_command(server)
main.add_command(bridge)
main.add_command(fund_account)
main.add_command(create_xchain_account)


if __name__ == "__main__":
    main()
