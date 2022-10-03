import json
import os

import pytest
from xrpl.models import AccountObjects

from sidechain_cli.main import main
from sidechain_cli.utils import get_config
from sidechain_cli.utils.config_file import _CONFIG_FILE


@pytest.mark.usefixtures("runner")
class TestBridgeBuild:
    def test_bridge_build(self, runner):
        config_dir = os.path.abspath(os.getenv("XCHAIN_CONFIG_DIR"))
        with open(os.path.join(config_dir, "bridge_bootstrap.json")) as f:
            bootstrap = json.load(f)

        locking_door = bootstrap["LockingChain"]["DoorAccount"]["Address"]
        issuing_door = bootstrap["IssuingChain"]["DoorAccount"]["Address"]

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

        runner_result = runner.invoke(
            main,
            [
                "bridge",
                "build",
                "--name=test_bridge",
                "--chains",
                "locking_chain",
                "issuing_chain",
                "--verbose",
            ],
        )
        assert runner_result.exit_code == 0, runner_result.output

        # check that the bridge was added properly to the CLI config file
        with open(_CONFIG_FILE) as f:
            config_result = json.load(f)

        expected_result = {
            "name": "test_bridge",
            "chains": ["locking_chain", "issuing_chain"],
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
