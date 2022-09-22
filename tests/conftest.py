import json
import os
import shutil
import tempfile
import unittest
import unittest.mock

import pytest
from click.testing import CliRunner

from sidechain_cli.main import main
from sidechain_cli.utils.config_file import _CONFIG_FILE


@pytest.fixture(autouse=True)
def runner():
    print("Hiiiiiiiasdufhas8dfoasdijfak")
    with tempfile.TemporaryDirectory() as tempdir:
        with unittest.mock.patch.dict(
            os.environ,
            {
                "XCHAIN_CONFIG_DIR": tempdir,
            },
        ):
            # reset CLI config file
            os.remove(_CONFIG_FILE)
            with open(_CONFIG_FILE, "w") as f:
                data = {"chains": [], "witnesses": [], "bridges": []}
                json.dump(data, f, indent=4)

            cli_runner = CliRunner()

            # create config files
            result = cli_runner.invoke(main, ["server", "create-config", "all"])
            assert result.exit_code == 0

            # start servers
            start_result = cli_runner.invoke(main, ["server", "start-all", "--verbose"])
            print(start_result.output)
            assert start_result.exit_code == 0, start_result.output

            yield cli_runner

            # stop servers
            stop_result = cli_runner.invoke(main, ["server", "stop", "--all"])
            assert stop_result.exit_code == 0, stop_result.output

        shutil.rmtree(tempdir)
