import pytest
from xrpl.models import AccountInfo
from xrpl.utils import xrp_to_drops
from xrpl.wallet import Wallet

from xbridge_cli.main import main
from xbridge_cli.utils import get_config


@pytest.mark.usefixtures("runner")
class TestFund:
    def test_fund(self, runner):
        client = get_config().get_chain("locking_chain").get_client()

        test_account = Wallet.create().classic_address
        initial_account_info = client.request(AccountInfo(account=test_account))
        assert initial_account_info.status.value == "error"
        assert initial_account_info.result["error"] == "actNotFound"

        fund_result = runner.invoke(main, ["fund", "locking_chain", test_account])
        assert fund_result.exit_code == 0, fund_result.output

        final_account_info = client.request(AccountInfo(account=test_account))
        assert final_account_info.status.value == "success"
        assert final_account_info.result["account_data"]["Account"] == test_account

    def test_fund_multiple_accounts(self, runner):
        client = get_config().get_chain("locking_chain").get_client()

        test_accounts = [Wallet.create().classic_address for _ in range(4)]
        for account in test_accounts:
            initial_account_info = client.request(AccountInfo(account=account))
            assert initial_account_info.status.value == "error"
            assert initial_account_info.result["error"] == "actNotFound"

        fund_result = runner.invoke(main, ["fund", "locking_chain", *test_accounts])
        assert fund_result.exit_code == 0, fund_result.output

        for account in test_accounts:
            final_account_info = client.request(AccountInfo(account=account))
            assert final_account_info.status.value == "success"
            assert final_account_info.result["account_data"]["Account"] == account

    def test_fund_custom_amounts(self, runner):
        client = get_config().get_chain("locking_chain").get_client()

        test_account = Wallet.create().classic_address
        initial_account_info = client.request(AccountInfo(account=test_account))
        assert initial_account_info.status.value == "error"
        assert initial_account_info.result["error"] == "actNotFound"

        amount = 100
        fund_result = runner.invoke(
            main, ["fund", "locking_chain", test_account, "--amount", str(amount)]
        )
        assert fund_result.exit_code == 0, fund_result.output

        final_account_info = client.request(AccountInfo(account=test_account))
        assert final_account_info.status.value == "success"
        assert final_account_info.result["account_data"]["Account"] == test_account
        assert final_account_info.result["account_data"]["Balance"] == xrp_to_drops(
            amount
        )
