import os
from pprint import pformat

import pytest
from click.testing import CliRunner
from xrpl.account import does_account_exist, get_balance
from xrpl.models import LedgerData
from xrpl.wallet import Wallet

from xbridge_cli.main import main
from xbridge_cli.utils import get_config


@pytest.mark.usefixtures("create_bridge")
class TestRegister:
    def test_register(self):
        runner = CliRunner()
        bridge_config = get_config().get_bridge("test_bridge")
        bridge_name = "test_bridge2"

        # set up bridge
        register_result = runner.invoke(
            main,
            [
                "bridge",
                "register",
                "--name",
                bridge_name,
                "--chains",
                "http://localhost:5005",
                "http://localhost:5006",
                "--doors",
                bridge_config.door_accounts[0],
                bridge_config.door_accounts[1],
            ],
        )
        assert register_result.exit_code == 0, register_result.output

        send_wallet = Wallet.create()
        wallet_to_create = Wallet.create()

        #########
        # Test bridge to make sure it works

        # initialize account
        fund_result1 = runner.invoke(
            main,
            [
                "fund",
                "locking_chain",
                send_wallet.classic_address,
            ],
        )
        assert fund_result1.exit_code == 0, fund_result1.output

        locking_client = get_config().get_chain("locking_chain").get_client()
        issuing_client = get_config().get_chain("issuing_chain").get_client()
        initial_balance_locking = get_balance(
            send_wallet.classic_address, locking_client
        )
        assert (
            does_account_exist(wallet_to_create.classic_address, issuing_client)
            is False
        )

        runner_result = runner.invoke(
            main,
            [
                "bridge",
                "create-account",
                "--from_locking",
                "--bridge",
                bridge_name,
                "--from",
                send_wallet.seed,
                "--to",
                wallet_to_create.classic_address,
                "--verbose",
            ],
        )
        assert runner_result.exit_code == 0, runner_result.output

        final_balance_locking = get_balance(send_wallet.classic_address, locking_client)
        assert (
            final_balance_locking
            == initial_balance_locking
            - int(bridge_config.create_account_amounts[0])
            - int(bridge_config.signature_reward)
            - 10
        )
        assert (
            does_account_exist(wallet_to_create.classic_address, issuing_client) is True
        ), (
            runner_result.output
            + "\n" * 3
            + pformat(issuing_client.request(LedgerData()).result)
        )

    def test_register_bootstrap(self):
        runner = CliRunner()
        bridge_config = get_config().get_bridge("test_bridge")
        config_dir = os.path.abspath(os.getenv("XCHAIN_CONFIG_DIR"))
        bridge_name = "test_bridge3"

        # set up bridge
        register_result = runner.invoke(
            main,
            [
                "bridge",
                "register",
                "--name",
                bridge_name,
                "--bootstrap",
                os.path.join(config_dir, "bridge_bootstrap.json"),
            ],
        )
        assert register_result.exit_code == 0, register_result.output

        send_wallet = Wallet.create()
        wallet_to_create = Wallet.create()

        #########
        # Test bridge to make sure it works

        # initialize account
        fund_result1 = runner.invoke(
            main,
            [
                "fund",
                "locking_chain",
                send_wallet.classic_address,
            ],
        )
        assert fund_result1.exit_code == 0, fund_result1.output

        locking_client = get_config().get_chain("locking_chain").get_client()
        issuing_client = get_config().get_chain("issuing_chain").get_client()
        initial_balance_locking = get_balance(
            send_wallet.classic_address, locking_client
        )
        assert (
            does_account_exist(wallet_to_create.classic_address, issuing_client)
            is False
        )

        runner_result = runner.invoke(
            main,
            [
                "bridge",
                "create-account",
                "--from_locking",
                "--bridge",
                bridge_name,
                "--from",
                send_wallet.seed,
                "--to",
                wallet_to_create.classic_address,
                "--verbose",
            ],
        )
        assert runner_result.exit_code == 0, runner_result.output

        final_balance_locking = get_balance(send_wallet.classic_address, locking_client)
        assert (
            final_balance_locking
            == initial_balance_locking
            - int(bridge_config.create_account_amounts[0])
            - int(bridge_config.signature_reward)
            - 10
        )
        assert (
            does_account_exist(wallet_to_create.classic_address, issuing_client) is True
        ), (
            runner_result.output
            + "\n" * 3
            + pformat(issuing_client.request(LedgerData()).result)
        )
