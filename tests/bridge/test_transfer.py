import pytest
from click.testing import CliRunner
from xrpl.account import get_balance
from xrpl.utils import xrp_to_drops
from xrpl.wallet import Wallet

from tests.utils import SetInterval, close_ledgers
from xbridge_cli.main import main
from xbridge_cli.utils import get_config


@pytest.mark.usefixtures("create_bridge")
class TestBridgeTransfer:
    def test_bridge_transfer(self):
        runner = CliRunner()
        bridge_config = get_config().get_bridge("test_bridge")

        send_wallet = Wallet.create()
        receive_wallet = Wallet.create()
        xrp_amount = 10
        amount = xrp_to_drops(xrp_amount)

        # initialize accounts
        fund_result1 = runner.invoke(
            main,
            [
                "fund",
                "locking_chain",
                send_wallet.classic_address,
            ],
        )
        assert fund_result1.exit_code == 0, fund_result1.output
        fund_result2 = runner.invoke(
            main,
            [
                "bridge",
                "create-account",
                "--from_locking",
                "--bridge",
                "test_bridge",
                "--from",
                send_wallet.seed,
                "--to",
                receive_wallet.classic_address,
                "--amount",
                "10",
                "--verbose",
            ],
        )
        assert fund_result2.exit_code == 0, fund_result2.output

        locking_client = get_config().get_chain("locking_chain").get_client()
        issuing_client = get_config().get_chain("issuing_chain").get_client()
        initial_balance_locking = get_balance(
            send_wallet.classic_address, locking_client
        )
        initial_balance_issuing = get_balance(
            receive_wallet.classic_address, issuing_client
        )

        runner_result = runner.invoke(
            main,
            [
                "bridge",
                "transfer",
                "--bridge=test_bridge",
                "--from_locking",
                f"--amount={xrp_amount}",
                f"--from={send_wallet.seed}",
                f"--to={receive_wallet.seed}",
                "-vv",
            ],
        )
        assert runner_result.exit_code == 0, runner_result.output

        final_balance_locking = get_balance(send_wallet.classic_address, locking_client)
        final_balance_issuing = get_balance(
            receive_wallet.classic_address, issuing_client
        )
        assert final_balance_locking == initial_balance_locking - int(amount) - 10
        assert final_balance_issuing == initial_balance_issuing + int(
            amount
        ) - 10 - int(bridge_config.signature_reward), runner_result.output

    def test_bridge_transfer_prod(self):
        runner = CliRunner()
        bridge_config = get_config().get_bridge("test_bridge")

        send_wallet = Wallet.create()
        receive_wallet = Wallet.create()
        xrp_amount = 10
        amount = xrp_to_drops(xrp_amount)

        # initialize accounts
        fund_result1 = runner.invoke(
            main,
            [
                "fund",
                "locking_chain",
                send_wallet.classic_address,
            ],
        )
        assert fund_result1.exit_code == 0, fund_result1.output
        fund_result2 = runner.invoke(
            main,
            [
                "bridge",
                "create-account",
                "--from_locking",
                "--bridge",
                "test_bridge",
                "--from",
                send_wallet.seed,
                "--to",
                receive_wallet.classic_address,
                "--amount",
                "10",
                "--verbose",
            ],
        )
        assert fund_result2.exit_code == 0, fund_result2.output

        locking_client = get_config().get_chain("locking_chain").get_client()
        issuing_client = get_config().get_chain("issuing_chain").get_client()
        initial_balance_locking = get_balance(
            send_wallet.classic_address, locking_client
        )
        initial_balance_issuing = get_balance(
            receive_wallet.classic_address, issuing_client
        )

        close_ledgers()
        thread = SetInterval(close_ledgers, 3)

        runner_result = runner.invoke(
            main,
            [
                "bridge",
                "transfer",
                "--bridge=test_bridge",
                "--from_locking",
                f"--amount={xrp_amount}",
                f"--from={send_wallet.seed}",
                f"--to={receive_wallet.seed}",
                "-vv",
                "--no-close-ledgers",
            ],
        )
        thread.cancel()
        assert runner_result.exit_code == 0, runner_result.output

        final_balance_locking = get_balance(send_wallet.classic_address, locking_client)
        final_balance_issuing = get_balance(
            receive_wallet.classic_address, issuing_client
        )
        assert final_balance_locking == initial_balance_locking - int(amount) - 10
        assert final_balance_issuing == initial_balance_issuing + int(
            amount
        ) - 10 - int(bridge_config.signature_reward), runner_result.output
