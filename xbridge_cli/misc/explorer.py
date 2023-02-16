"""Set up an Explorer connected to your nodes."""

import os
import webbrowser

import click

_EXPLORER_HTML_PATH = os.path.abspath(
    os.path.join(
        os.path.realpath(__file__),
        "..",
        "explorer.html",
    )
)


@click.command(name="explorer")
def launch_explorer() -> None:
    """Launch an Explorer connected to your nodes."""
    webbrowser.open(f"file://{_EXPLORER_HTML_PATH}")
