import pytest
from xrpl.account import get_balance
from xrpl.utils import xrp_to_drops

from sidechain_cli.main import main
from sidechain_cli.utils import get_config


@pytest.mark.usefixtures("runner", "create_bridge")
class TestBridgeTransfer:
    def test_bridge_transfer(self, runner):
        bridge_config = get_config().get_bridge("test_bridge")

        send_account = "raFcdz1g8LWJDJWJE2ZKLRGdmUmsTyxaym"
        receive_account = "rJdTJRJZ6GXCCRaamHJgEqVzB7Zy4557Pi"
        amount = xrp_to_drops(10)

        # initialize accounts
        fund_result1 = runner.invoke(
            main,
            [
                "fund",
                f"--account={send_account}",
                "--chain=locking_chain",
            ],
        )
        assert fund_result1.exit_code == 0, fund_result1.output
        fund_result2 = runner.invoke(
            main,
            [
                "fund",
                f"--account={receive_account}",
                "--chain=issuing_chain",
            ],
        )
        assert fund_result2.exit_code == 0, fund_result2.output

        locking_client = get_config().get_chain("locking_chain").get_client()
        issuing_client = get_config().get_chain("issuing_chain").get_client()
        initial_balance_locking = get_balance(send_account, locking_client)
        initial_balance_issuing = get_balance(receive_account, issuing_client)

        runner_result = runner.invoke(
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
        assert runner_result.exit_code == 0, runner_result.output

        final_balance_locking = get_balance(send_account, locking_client)
        final_balance_issuing = get_balance(receive_account, issuing_client)
        assert final_balance_locking == initial_balance_locking - int(amount) - 10
        assert final_balance_issuing == initial_balance_issuing + int(
            amount
        ) - 10 - int(bridge_config.signature_reward), runner_result.output
