import json
import os

import pytest
from click.testing import CliRunner
from xrpl.account import does_account_exist
from xrpl.clients import JsonRpcClient
from xrpl.models import AccountObjects

from sidechain_cli.main import main
from sidechain_cli.tests.utils import SetInterval, close_ledgers
from sidechain_cli.utils import get_config
from sidechain_cli.utils.config_file import _CONFIG_FILE


@pytest.mark.usefixtures("bridge_build_setup")
class TestBridgeBuild:
    def test_bridge_build(self):
        runner = CliRunner()
        config_dir = os.path.abspath(os.getenv("XCHAIN_CONFIG_DIR"))
        with open(os.path.join(config_dir, "bridge_bootstrap.json")) as f:
            bootstrap = json.load(f)

        locking_door = bootstrap["LockingChain"]["DoorAccount"]["Address"]
        issuing_door = bootstrap["IssuingChain"]["DoorAccount"]["Address"]

        runner_result = runner.invoke(
            main,
            [
                "bridge",
                "build",
                "--name=test_bridge",
                "--close-ledgers",
                "--verbose",
            ],
        )
        assert runner_result.exit_code == 0, runner_result.output

        # check that the bridge was added properly to the CLI config file
        with open(_CONFIG_FILE) as f:
            config_result = json.load(f)

        expected_result = {
            "name": "test_bridge",
            "chains": ["http://0.0.0.0:5005", "http://0.0.0.0:5006"],
            "num_witnesses": 5,
            "door_accounts": [
                bootstrap["LockingChain"]["DoorAccount"]["Address"],
                bootstrap["IssuingChain"]["DoorAccount"]["Address"],
            ],
            "xchain_currencies": ["XRP", "XRP"],
            "signature_reward": "100",
            "create_account_amounts": ["5000000", "5000000"],
        }

        assert config_result["bridges"][0] == expected_result

        # check that the bridge was created properly on both chains
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
        assert bridge["XChainBridge"] == bridge_config.to_xrpl()
        signer_list = [
            obj for obj in locking_objects if obj["LedgerEntryType"] == "SignerList"
        ][0]
        assert len(signer_list["SignerEntries"]) == bridge_config.num_witnesses

        issuing_objects_result = issuing_client.request(
            AccountObjects(account=issuing_door)
        )
        issuing_objects = issuing_objects_result.result["account_objects"]
        bridge = [obj for obj in issuing_objects if obj["LedgerEntryType"] == "Bridge"][
            0
        ]
        assert bridge["XChainBridge"] == bridge_config.to_xrpl()
        signer_list = [
            obj for obj in issuing_objects if obj["LedgerEntryType"] == "SignerList"
        ][0]
        assert len(signer_list["SignerEntries"]) == bridge_config.num_witnesses

    def test_bridge_prod_build_xrp(self):
        runner = CliRunner()
        config_dir = os.path.abspath(os.getenv("XCHAIN_CONFIG_DIR"))
        with open(os.path.join(config_dir, "bridge_bootstrap.json")) as f:
            bootstrap = json.load(f)

        locking_door = bootstrap["LockingChain"]["DoorAccount"]["Address"]
        issuing_door = bootstrap["IssuingChain"]["DoorAccount"]["Address"]

        locking_url = "http://localhost:5005"
        issuing_url = "http://localhost:5006"

        # fund needed accounts on the locking chain
        accounts_locking_fund = set(
            [locking_door]
            + bootstrap["LockingChain"]["WitnessRewardAccounts"]
            + bootstrap["LockingChain"]["WitnessSubmitAccounts"]
        )
        for account in accounts_locking_fund:
            fund_result = runner.invoke(
                main, ["fund", f"--account={account}", "--chain=locking_chain"]
            )
            assert fund_result.exit_code == 0, fund_result.output

        close_ledgers()
        thread = SetInterval(close_ledgers, 1)

        # actually run build
        runner_result = runner.invoke(
            main,
            [
                "bridge",
                "build",
                "--name",
                "test_bridge",
                "--no-close-ledgers",
                "--funding_seed",
                "snoPBrXtMeMyMHUVTgbuqAfg1SUTb",
                "--verbose",
            ],
        )
        thread.cancel()
        assert runner_result.exit_code == 0, runner_result.output

        # check that the bridge was added properly to the CLI config file
        with open(_CONFIG_FILE) as f:
            config_result = json.load(f)

        expected_result = {
            "name": "test_bridge",
            "chains": ["http://0.0.0.0:5005", "http://0.0.0.0:5006"],
            "num_witnesses": 5,
            "door_accounts": [
                bootstrap["LockingChain"]["DoorAccount"]["Address"],
                bootstrap["IssuingChain"]["DoorAccount"]["Address"],
            ],
            "xchain_currencies": ["XRP", "XRP"],
            "signature_reward": "100",
            "create_account_amounts": ["5000000", "5000000"],
        }

        assert config_result["bridges"][0] == expected_result

        locking_client = JsonRpcClient(locking_url)
        issuing_client = JsonRpcClient(issuing_url)

        bridge_obj = {
            "LockingChainDoor": locking_door,
            "LockingChainIssue": "XRP",
            "IssuingChainDoor": issuing_door,
            "IssuingChainIssue": "XRP",
        }

        locking_objects_result = locking_client.request(
            AccountObjects(account=locking_door)
        )
        locking_objects = locking_objects_result.result["account_objects"]
        bridge = [obj for obj in locking_objects if obj["LedgerEntryType"] == "Bridge"][
            0
        ]
        assert bridge["XChainBridge"] == bridge_obj
        signer_list = [
            obj for obj in locking_objects if obj["LedgerEntryType"] == "SignerList"
        ][0]
        assert len(signer_list["SignerEntries"]) == len(
            bootstrap["Witnesses"]["SignerList"]
        )

        issuing_objects_result = issuing_client.request(
            AccountObjects(account=issuing_door)
        )
        issuing_objects = issuing_objects_result.result["account_objects"]
        bridge = [obj for obj in issuing_objects if obj["LedgerEntryType"] == "Bridge"][
            0
        ]
        assert bridge["XChainBridge"] == bridge_obj
        signer_list = [
            obj for obj in issuing_objects if obj["LedgerEntryType"] == "SignerList"
        ][0]
        assert len(signer_list["SignerEntries"]) == len(
            bootstrap["Witnesses"]["SignerList"]
        )

        accounts_issuing_check = set(
            bootstrap["IssuingChain"]["WitnessRewardAccounts"]
            + bootstrap["IssuingChain"]["WitnessSubmitAccounts"]
        )
        for account in accounts_issuing_check:
            assert does_account_exist(account, issuing_client)
