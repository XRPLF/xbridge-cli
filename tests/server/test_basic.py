from click.testing import CliRunner

from xbridge_cli.main import main


class TestBasicCreation:
    def test_start_stop(self):
        runner = CliRunner()
        no_chains_list_output = "No chains running.\n\nNo witnesses running.\n"

        start_result = runner.invoke(main, ["server", "start-all", "-v"])
        assert start_result.exit_code == 0, start_result.exception
        start_list = runner.invoke(main, ["server", "list"])
        assert start_list.output != no_chains_list_output, start_result.exception

        stop_result = runner.invoke(main, ["server", "stop", "--all"])
        assert stop_result.exit_code == 0, stop_result.exception
        stop_list = runner.invoke(main, ["server", "list"])
        assert stop_list.output == no_chains_list_output, stop_result.exception
