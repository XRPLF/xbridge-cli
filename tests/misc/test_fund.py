import pytest
from xrpl.models import AccountInfo

from sidechain_cli.main import main
from sidechain_cli.utils import get_config


@pytest.mark.usefixtures("runner")
class TestFund:
    def test_fund(self, runner):
        client = get_config().get_chain("locking_chain").get_client()

        test_account = "rHvgvEAy1npZ2kCde6mM5anjXo7Gpqxi78"
        initial_account_info = client.request(AccountInfo(account=test_account))
        assert initial_account_info.status.value == "error"
        assert initial_account_info.result["error"] == "actNotFound"

        fund_result = runner.invoke(
            main, ["fund", f"--account={test_account}", "--chain=locking_chain"]
        )
        assert fund_result.exit_code == 0, fund_result.output

        final_account_info = client.request(AccountInfo(account=test_account))
        assert final_account_info.status.value == "success"
        assert final_account_info.result["account_data"]["Account"] == test_account
