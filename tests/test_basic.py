import unittest

from click.testing import CliRunner

from sidechain_cli.main import main


class TestBasicCreation(unittest.TestCase):
    def test_startup_close(self):
        runner = CliRunner()
        no_chains_list_output = "No chains running.\n\n\nNo witnesses running.\n"

        start_result = runner.invoke(main, ["server", "start-all"])
        assert start_result.exit_code == 0
        start_list = runner.invoke(main, ["server", "list"])
        assert start_list.output != no_chains_list_output

        stop_result = runner.invoke(main, ["server", "stop", "--all"])
        assert stop_result.exit_code == 0
        stop_list = runner.invoke(main, ["server", "list"])
        assert stop_list.output == no_chains_list_output
