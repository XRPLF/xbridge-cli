import json
import os
import threading

import pytest
from xrpl.account import does_account_exist
from xrpl.clients import JsonRpcClient
from xrpl.models import AccountObjects, GenericRequest

from sidechain_cli.main import main


class SetInterval:
    def __init__(self, func, sec):
        def func_wrapper():
            self.t = threading.Timer(sec, func_wrapper)
            self.t.start()
            func()

        self.t = threading.Timer(sec, func_wrapper)
        self.t.start()

    def cancel(self):
        self.t.cancel()


def close_ledgers():
    JsonRpcClient("http://localhost:5005").request(
        GenericRequest(method="ledger_accept")
    )
    JsonRpcClient("http://localhost:5006").request(
        GenericRequest(method="ledger_accept")
    )


@pytest.mark.usefixtures("runner")
class TestBridgeProdBuild:
    def test_bridge_prod_build_xrp(self, runner):
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

        thread = SetInterval(close_ledgers, 1)

        # actually run build
        runner_result = runner.invoke(
            main,
            [
                "bridge",
                "prod-build",
                "--chains",
                locking_url,
                issuing_url,
                "--funding_seed",
                "snoPBrXtMeMyMHUVTgbuqAfg1SUTb",
                "--verbose",
            ],
        )
        assert runner_result.exit_code == 0, runner_result.output

        thread.cancel()

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
