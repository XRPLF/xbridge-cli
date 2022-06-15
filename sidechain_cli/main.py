"""The main CLI call."""

import click

from sidechain_cli.bridge import bridge
from sidechain_cli.chain import chain
from sidechain_cli.misc.fund import fund_account
from sidechain_cli.witness import witness


@click.group()
def main() -> None:
    """The Sidechain Command-Line Interface. Do everything with sidechains."""
    pass


main.add_command(chain)
main.add_command(witness)
main.add_command(bridge)
main.add_command(fund_account)


if __name__ == "__main__":
    main()
