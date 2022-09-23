import json
import os

import pytest

from sidechain_cli.main import main
from sidechain_cli.utils.config_file import _CONFIG_FILE


@pytest.mark.usefixtures("runner")
class TestBridgeCreate:
    def test_bridge_create(self, runner):
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
        assert create_result.exit_code == 0
        with open(_CONFIG_FILE) as f:
            result = json.load(f)

        config_dir = os.path.abspath(os.getenv("XCHAIN_CONFIG_DIR"))
        with open(os.path.join(config_dir, "bridge_bootstrap.json")) as f:
            bootstrap = json.load(f)

        expected_result = {
            "name": "test_bridge",
            "chains": ["locking_chain", "issuing_chain"],
            "witnesses": ["witness0", "witness1", "witness2", "witness3", "witness4"],
            "door_accounts": [
                bootstrap["locking_chain_door"]["id"],
                bootstrap["issuing_chain_door"]["id"],
            ],
            "xchain_currencies": ["XRP", "XRP"],
            "signature_reward": "100",
            "create_account_amounts": ["5000000", "5000000"],
        }

        assert result["bridges"][0] == expected_result
