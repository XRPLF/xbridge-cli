import pytest
from xrpl.models import AccountInfo
from xrpl.wallet import Wallet

from sidechain_cli.main import main
from sidechain_cli.utils import get_config


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
