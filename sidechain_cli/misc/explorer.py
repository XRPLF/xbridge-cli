"""Set up an Explorer connected to your nodes."""

import os
import webbrowser

import click


@click.command(name="explorer")
def launch_explorer() -> None:
    """Launch an Explorer connected to your nodes."""
    filepath = os.path.abspath(
        os.path.join(
            os.path.realpath(__file__),
            "..",
            "explorer.html",
        )
    )
    webbrowser.open(f"file://{filepath}")
