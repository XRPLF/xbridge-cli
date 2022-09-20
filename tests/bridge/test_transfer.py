import json
import os
import unittest

from click.testing import CliRunner
from xrpl.account import get_balance
from xrpl.utils import xrp_to_drops

from sidechain_cli.main import main
from sidechain_cli.utils import get_config
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
        assert start_result.exit_code == 0, start_result.exception

        # create bridge
        create_result = cls.runner.invoke(
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
        assert create_result.exit_code == 0, create_result.output

        config_dir = os.path.abspath(os.getenv("XCHAIN_CONFIG_DIR"))
        with open(os.path.join(config_dir, "bridge_bootstrap.json")) as f:
            bootstrap = json.load(f)

        locking_door = bootstrap["locking_chain_door"]["id"]
        fund_result = cls.runner.invoke(
            main, ["fund", f"--account={locking_door}", "--chain=locking_chain"]
        )
        assert fund_result.exit_code == 0, fund_result.output

        build_result = cls.runner.invoke(
            main, ["bridge", "build", "--bridge=test_bridge", "--verbose"]
        )
        assert build_result.exit_code == 0, build_result.output

    @classmethod
    def tearDownClass(cls):
        stop_result = cls.runner.invoke(main, ["server", "stop", "--all"])
        assert stop_result.exit_code == 0, stop_result.output

    def test_bridge_transfer(self):
        bridge_config = get_config().get_bridge("test_bridge")

        send_account = "raFcdz1g8LWJDJWJE2ZKLRGdmUmsTyxaym"
        receive_account = "rJdTJRJZ6GXCCRaamHJgEqVzB7Zy4557Pi"
        amount = xrp_to_drops(10)

        # initialize accounts
        fund_result1 = self.runner.invoke(
            main,
            [
                "fund",
                f"--account={send_account}",
                "--chain=locking_chain",
            ],
        )
        self.assertEqual(fund_result1.exit_code, 0, fund_result1.output)
        fund_result2 = self.runner.invoke(
            main,
            [
                "fund",
                f"--account={receive_account}",
                "--chain=issuing_chain",
            ],
        )
        self.assertEqual(fund_result2.exit_code, 0, fund_result2.output)

        locking_client = get_config().get_chain("locking_chain").get_client()
        issuing_client = get_config().get_chain("issuing_chain").get_client()
        initial_balance_locking = get_balance(send_account, locking_client)
        initial_balance_issuing = get_balance(receive_account, issuing_client)

        runner_result = self.runner.invoke(
            main,
            [
                "bridge",
                "transfer",
                "--bridge=test_bridge",
                "--src_chain=locking_chain",
                f"--amount={amount}",
                "--from=snqs2zzXuMA71w9isKHPTrvFn1HaJ",
                "--to=snyEJjY2Xi5Dxdh81Jy9Mj3AiYRQM",
                "-vv",
            ],
        )
        self.assertEqual(runner_result.exit_code, 0, runner_result.output)

        final_balance_locking = get_balance(send_account, locking_client)
        final_balance_issuing = get_balance(receive_account, issuing_client)
        self.assertEqual(
            (final_balance_locking), initial_balance_locking - int(amount) - 10
        )
        self.assertEqual(
            final_balance_issuing,
            initial_balance_issuing
            + int(amount)
            - 10
            - int(bridge_config.signature_reward),
            runner_result.output,
        )
