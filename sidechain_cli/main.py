"""The main CLI call."""

import click

from sidechain_cli.bridge import setup_bridge
from sidechain_cli.start import start


@click.group()
def main() -> None:
    """The main CLI call."""
    pass


main.add_command(start)
main.add_command(setup_bridge, name="bridge")


if __name__ == "__main__":
    main()
