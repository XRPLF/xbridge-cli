import json
import os
import unittest

from click.testing import CliRunner
from xrpl.models import AccountObjects

from sidechain_cli.main import main
from sidechain_cli.utils import get_config
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

    def test_bridge(self):
        ###############################################################################
        # Part 1:
        # test bridge create
        runner_result = self.runner.invoke(
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
        self.assertEqual(runner_result.exit_code, 0, runner_result.output)
        with open(_CONFIG_FILE) as f:
            result = json.load(f)

        config_dir = os.path.abspath(os.getenv("XCHAIN_CONFIG_DIR"))
        with open(os.path.join(config_dir, "bridge_bootstrap.json")) as f:
            bootstrap = json.load(f)

        expected_result = {
            "name": "test_bridge",
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

        ###############################################################################
        # Part 2:
        # test bridge build
        config_dir = os.path.abspath(os.getenv("XCHAIN_CONFIG_DIR"))
        with open(os.path.join(config_dir, "bridge_bootstrap.json")) as f:
            bootstrap = json.load(f)

        locking_door = bootstrap["locking_chain_door"]["id"]
        issuing_door = bootstrap["issuing_chain_door"]["id"]
        fund_result = self.runner.invoke(
            main, ["fund", f"--account={locking_door}", "--chain=locking_chain"]
        )
        self.assertEqual(fund_result.exit_code, 0, fund_result.output)

        runner_result = self.runner.invoke(
            main, ["bridge", "build", "--bridge=test_bridge", "--verbose"]
        )
        self.assertEqual(runner_result.exit_code, 0, runner_result.output)

        locking_client = get_config().get_chain("locking_chain").get_client()
        issuing_client = get_config().get_chain("issuing_chain").get_client()
        bridge_config = get_config().get_bridge("test_bridge")

        locking_objects_result = locking_client.request(
            AccountObjects(account=locking_door)
        )
        locking_objects = locking_objects_result.result["account_objects"]
        bridge = [obj for obj in locking_objects if obj["LedgerEntryType"] == "Bridge"][
            0
        ]
        self.assertEqual(bridge["XChainBridge"], bridge_config.to_xrpl())
        signer_list = [
            obj for obj in locking_objects if obj["LedgerEntryType"] == "SignerList"
        ][0]
        self.assertEqual(
            len(signer_list["SignerEntries"]), len(bridge_config.witnesses)
        )

        issuing_objects_result = issuing_client.request(
            AccountObjects(account=issuing_door)
        )
        issuing_objects = issuing_objects_result.result["account_objects"]
        bridge = [obj for obj in issuing_objects if obj["LedgerEntryType"] == "Bridge"][
            0
        ]
        self.assertEqual(bridge["XChainBridge"], bridge_config.to_xrpl())
        signer_list = [
            obj for obj in issuing_objects if obj["LedgerEntryType"] == "SignerList"
        ][0]
        self.assertEqual(
            len(signer_list["SignerEntries"]), len(bridge_config.witnesses)
        )

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
