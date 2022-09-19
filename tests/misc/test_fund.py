import unittest

from click.testing import CliRunner
from xrpl.models import AccountInfo

from sidechain_cli.main import main
from sidechain_cli.utils import get_config


class TestBridgeSetup(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = CliRunner()
        start_result = cls.runner.invoke(main, ["server", "start-all", "--verbose"])
        assert start_result.exit_code == 0, start_result.output

    @classmethod
    def tearDownClass(cls):
        stop_result = cls.runner.invoke(main, ["server", "stop", "--all"])
        assert stop_result.exit_code == 0, stop_result.output

    def test_fund(self):
        client = get_config().get_chain("locking_chain").get_client()

        test_account = "rHvgvEAy1npZ2kCde6mM5anjXo7Gpqxi78"
        initial_account_info = client.request(AccountInfo(account=test_account))
        self.assertEqual(initial_account_info.status.value, "error")
        self.assertEqual(initial_account_info.result["error"], "actNotFound")

        fund_result = self.runner.invoke(
            main, ["fund", f"--account={test_account}", "--chain=locking_chain"]
        )
        self.assertEqual(fund_result.exit_code, 0, fund_result.output)

        final_account_info = client.request(AccountInfo(account=test_account))
        self.assertEqual(final_account_info.status.value, "success")
        self.assertEqual(
            final_account_info.result["account_data"]["Account"], test_account
        )
