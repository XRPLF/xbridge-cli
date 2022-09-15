import json
import os
import unittest

from click.testing import CliRunner

from sidechain_cli.main import main
from sidechain_cli.utils.config_file import _CONFIG_FILE


class TestBridgeSetup(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # reset config file
        os.remove(_CONFIG_FILE)
        with open(_CONFIG_FILE, "w") as f:
            data = {"chains": [], "witnesses": [], "bridges": []}
            json.dump(data, f, indent=4)

        cls.runner = CliRunner()
        start_result = cls.runner.invoke(main, ["server", "start-all", "--verbose"])
        assert start_result.exit_code == 0, start_result.output

    @classmethod
    def tearDownClass(cls):
        stop_result = cls.runner.invoke(main, ["server", "stop", "--all"])
        assert stop_result.exit_code == 0, stop_result.output

    def test_bridge_create(self):
        runner_result = self.runner.invoke(
            main,
            [
                "bridge",
                "create",
                "--name=bridge",
                "--chains",
                "locking_chain",
                "issuing_chain",
                "--witness",
                "witness0",
                "--witness",
                "witness1",
                "--witness",
                "witness2",
                "--witness",
                "witness3",
                "--witness",
                "witness4",
            ],
        )
        print(runner_result.output)
        self.assertEqual(runner_result.exit_code, 0, runner_result.output)
        with open(_CONFIG_FILE) as f:
            result = json.load(f)

        config_dir = os.path.abspath(os.getenv("XCHAIN_CONFIG_DIR"))
        with open(os.path.join(config_dir, "bridge_bootstrap.json")) as f:
            bootstrap = json.load(f)

        expected_result = {
            "name": "bridge",
            "chains": ["locking_chain", "issuing_chain"],
            "witnesses": ["witness0", "witness1", "witness2", "witness3", "witness4"],
            "door_accounts": [
                bootstrap["locking_chain_door"]["id"],
                bootstrap["issuing_chain_door"]["id"],
            ],
            "xchain_currencies": ["XRP", "XRP"],
            "signature_reward": "100",
            "create_account_amounts": ["5000000", "5000000"],
        }

        self.assertEqual(result["bridges"][0], expected_result)
