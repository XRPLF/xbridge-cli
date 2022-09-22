import json
import os

import pytest
from xrpl.account import does_account_exist, get_balance

from sidechain_cli.main import main
from sidechain_cli.utils import get_config


@pytest.fixture(autouse=True)
def create_bridge(runner):
    # create bridge
    create_result = runner.invoke(
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
    fund_result = runner.invoke(
        main, ["fund", f"--account={locking_door}", "--chain=locking_chain"]
    )
    assert fund_result.exit_code == 0, fund_result.output

    build_result = runner.invoke(
        main, ["bridge", "build", "--bridge=test_bridge", "--verbose"]
    )
    assert build_result.exit_code == 0, build_result.output


class TestCreateAccount:
    def test_create_account(self, runner):
        bridge_config = get_config().get_bridge("test_bridge")

        send_account = "raFcdz1g8LWJDJWJE2ZKLRGdmUmsTyxaym"
        account_to_create = "rfTi2cbUVbt3xputSqyhgKc1nXFvi7cnvu"

        # initialize account
        fund_result1 = runner.invoke(
            main,
            [
                "fund",
                f"--account={send_account}",
                "--chain=locking_chain",
            ],
        )
        assert fund_result1.exit_code == 0, fund_result1.output

        locking_client = get_config().get_chain("locking_chain").get_client()
        issuing_client = get_config().get_chain("issuing_chain").get_client()
        initial_balance_locking = get_balance(send_account, locking_client)
        assert does_account_exist(account_to_create, issuing_client) is False

        runner_result = runner.invoke(
            main,
            [
                "create-account",
                "--chain",
                "locking_chain",
                "--bridge",
                "test_bridge",
                "--from",
                "snqs2zzXuMA71w9isKHPTrvFn1HaJ",
                "--to",
                f"{account_to_create}",
            ],
        )
        assert runner_result.exit_code == 0, runner_result.output

        final_balance_locking = get_balance(send_account, locking_client)
        assert (
            final_balance_locking
            == initial_balance_locking
            - int(bridge_config.create_account_amounts[0])
            - int(bridge_config.signature_reward)
            - 10
        )
        assert does_account_exist(account_to_create, issuing_client) is True
