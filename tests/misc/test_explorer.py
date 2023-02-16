import os
import unittest.mock

from click.testing import CliRunner

from xbridge_cli.main import main


class TestExplorer:
    def test_explorer(self):
        runner = CliRunner()
        with unittest.mock.patch("webbrowser.open") as mock_open:
            explorer_result = runner.invoke(main, "explorer")
            assert explorer_result.exit_code == 0, explorer_result.output
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
