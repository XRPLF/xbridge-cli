"""The main CLI call."""

import click


@click.group()
def main() -> None:
    """The main CLI call."""
    pass


@main.group()
def start() -> None:
    """Start a node."""
    pass


@start.command("chain")
@click.argument("rippled")
@click.argument("config")
def start_chain(rippled: str, config: str) -> None:
    """
    Start a standalone node of rippled.

    Args:
        rippled: The filepath to the rippled node.
        config: The filepath to the rippled config file.
    """
    print(rippled)
    print(config)


@main.group()
@click.argument("name")
def goodbye(name: str) -> None:
    """
    Say goodbye.

    Args:
        name: The name to say goodbye to.
    """
    print("Goodbye, {0}!".format(name))


if __name__ == "__main__":
    main()
