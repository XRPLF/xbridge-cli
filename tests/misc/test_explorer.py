import os
import unittest.mock

from click.testing import CliRunner

from sidechain_cli.main import main


class TestExplorer:
    def test_explorer(self):
        runner = CliRunner()
        with unittest.mock.patch("webbrowser.open") as mock_open:
            runner.invoke(main, "explorer")
            expected_path = os.path.abspath(
                os.path.join(
                    os.path.realpath(__file__),
                    "..",
                    "..",
                    "..",
                    "sidechain_cli",
                    "misc",
                    "explorer.html",
                )
            )
            assert mock_open.call_args[0][0] == f"file://{expected_path}"
