import json
import os

import pytest
from xrpl.models import AccountObjects

from sidechain_cli.main import main
from sidechain_cli.utils import get_config


@pytest.mark.usefixtures("runner")
class TestBridgeBuild:
    def test_bridge_build(self, runner):
        ###############################################################################
        # Part 1:
        # test bridge create
        runner_result = runner.invoke(
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

        ###############################################################################
        # Actual test: bridge build
        config_dir = os.path.abspath(os.getenv("XCHAIN_CONFIG_DIR"))
        with open(os.path.join(config_dir, "bridge_bootstrap.json")) as f:
            bootstrap = json.load(f)

        locking_door = bootstrap["LockingChain"]["DoorAccount"]["Address"]
        issuing_door = bootstrap["IssuingChain"]["DoorAccount"]["Address"]
        fund_result = runner.invoke(
            main, ["fund", f"--account={locking_door}", "--chain=locking_chain"]
        )
        assert fund_result.exit_code == 0, fund_result.output

        runner_result = runner.invoke(
            main, ["bridge", "build", "--bridge=test_bridge", "--verbose"]
        )
        assert runner_result.exit_code == 0, runner_result.output

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
        assert len(signer_list["SignerEntries"]) == len(bridge_config.witnesses)

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
        assert len(signer_list["SignerEntries"]) == len(bridge_config.witnesses)
