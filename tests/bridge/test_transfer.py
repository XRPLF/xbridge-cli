import json
import os
import unittest

from click.testing import CliRunner

from sidechain_cli.main import main
from sidechain_cli.utils.config_file import _CONFIG_FILE


class TestBridgeTransfer(unittest.TestCase):
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

        # create bridge
        runner_result = cls.runner.invoke(
            main,
            [
                "bridge",
                "create",
                "--name=test_bridge",
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
                "--verbose",
            ],
        )
        assert runner_result.exit_code == 0, runner_result.output

        config_dir = os.path.abspath(os.getenv("XCHAIN_CONFIG_DIR"))
        with open(os.path.join(config_dir, "bridge_bootstrap.json")) as f:
            bootstrap = json.load(f)

        locking_door = bootstrap["locking_chain_door"]["id"]
        fund_result = cls.runner.invoke(
            main, ["fund", f"--account={locking_door}", "--chain=locking_chain"]
        )
        assert fund_result.exit_code == 0, fund_result.output

        runner_result = cls.runner.invoke(
            main, ["bridge", "build", "--bridge=test_bridge", "--verbose"]
        )
        assert runner_result.exit_code == 0, runner_result.output

    @classmethod
    def tearDownClass(cls):
        stop_result = cls.runner.invoke(main, ["server", "stop", "--all"])
        assert stop_result.exit_code == 0, stop_result.output

    def test_bridge_transfer(self):

        ###############################################################################
        # Part 3:
        # test bridge transfer

        # initialize accounts
        fund_result1 = self.runner.invoke(
            main,
            [
                "fund",
                "--account=raFcdz1g8LWJDJWJE2ZKLRGdmUmsTyxaym",
                "--chain=locking_chain",
            ],
        )
        self.assertEqual(fund_result1.exit_code, 0, fund_result1.output)
        fund_result2 = self.runner.invoke(
            main,
            [
                "fund",
                "--account=rJdTJRJZ6GXCCRaamHJgEqVzB7Zy4557Pi",
                "--chain=issuing_chain",
            ],
        )
        self.assertEqual(fund_result2.exit_code, 0, fund_result2.output)

        runner_result = self.runner.invoke(
            main,
            [
                "bridge",
                "transfer",
                "--bridge=test_bridge",
                "--src_chain=locking_chain",
                "--amount=10000000",
                "--from=snqs2zzXuMA71w9isKHPTrvFn1HaJ",
                "--to=snyEJjY2Xi5Dxdh81Jy9Mj3AiYRQM",
                "--verbose",
            ],
        )
        self.assertEqual(runner_result.exit_code, 0, runner_result.output)
