import json
import os
import tempfile
import time
import unittest
import unittest.mock
from typing import Any, Dict, List, Optional

import pytest
from click.testing import CliRunner

from sidechain_cli.main import main
from sidechain_cli.utils import get_config_folder

config_dir: Optional[tempfile.TemporaryDirectory] = None
mocked_home_dir: Optional[tempfile.TemporaryDirectory] = None
mocked_vars: List[Any] = []


def _is_docker():
    """Whether tests are running on docker."""
    return (
        os.getenv("RIPPLED_EXE") == "docker" and os.getenv("WITNESSD_EXE") == "docker"
    )


def pytest_configure(config):
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """
    global mocked_home_dir, config_dir, mocked_vars
    runner = CliRunner()
    runner.invoke(main, ["server", "stop", "--all"])

    print("before everything")
    if not _is_docker():
        print("shouldn't get this 1")
        config_dir = tempfile.TemporaryDirectory()
        env_vars = unittest.mock.patch.dict(
            os.environ,
            {
                "XCHAIN_CONFIG_DIR": config_dir.name,
            },
        )
        env_vars.start()
        mocked_vars.append(env_vars)

    print("before mocking the other stuff")
    print(os.getenv("GITHUB_CI"), type(os.getenv("GITHUB_CI")))
    if os.getenv("GITHUB_CI") != "True":
        print("shouldn't get this 2")
        mocked_home_dir = tempfile.TemporaryDirectory()
        config_var = unittest.mock.patch(
            "sidechain_cli.utils.config_file.CONFIG_FOLDER",
            mocked_home_dir.name,
        )
        config_var.start()
        mocked_vars.append(config_var)

        config_file = os.path.join(mocked_home_dir.name, "config.json")
        with open(config_file, "w") as f:
            data: Dict[str, List[Any]] = {"chains": [], "witnesses": [], "bridges": []}
            json.dump(data, f, indent=4)
        config_var2 = unittest.mock.patch(
            "sidechain_cli.utils.config_file._CONFIG_FILE",
            config_file,
        )
        config_var2.start()
        mocked_vars.append(config_var2)

    print("done with setup")


def pytest_unconfigure(config):
    """
    Called after whole test run finished, right before
    returning the exit status to the system.
    """
    global mocked_vars
    for var in mocked_vars:
        var.stop()
    mocked_vars = []


@pytest.fixture(scope="class")
def runner():
    # reset CLI config file
    config_file = os.path.join(get_config_folder(), "config.json")
    os.remove(config_file)
    with open(config_file, "w") as f:
        data = {"chains": [], "witnesses": [], "bridges": []}
        json.dump(data, f, indent=4)

    cli_runner = CliRunner()

    # create config files
    params = ["server", "create-config", "all"]
    if _is_docker():
        params.append("--docker")
    result = cli_runner.invoke(main, params)
    assert result.exit_code == 0

    # start servers
    start_result = cli_runner.invoke(main, ["server", "start-all", "--verbose"])
    assert start_result.exit_code == 0, start_result.output

    yield cli_runner

    # stop servers
    stop_result = cli_runner.invoke(main, ["server", "stop", "--all"])
    assert stop_result.exit_code == 0, stop_result.output


@pytest.fixture(scope="class")
def create_bridge():
    # reset CLI config file
    config_file = os.path.join(get_config_folder(), "config.json")
    os.remove(config_file)
    with open(config_file, "w") as f:
        data = {"chains": [], "witnesses": [], "bridges": []}
        json.dump(data, f, indent=4)

    cli_runner = CliRunner()

    # create config files
    params = ["server", "create-config", "all"]
    if _is_docker():
        params.append("--docker")
    result = cli_runner.invoke(main, params)
    assert result.exit_code == 0

    # start rippled servers
    start_result = cli_runner.invoke(
        main, ["server", "start-all", "--rippled-only", "--verbose"]
    )
    assert start_result.exit_code == 0, start_result.output
    time.sleep(1.5)

    # fund locking door
    config_dir = os.path.abspath(os.getenv("XCHAIN_CONFIG_DIR"))
    with open(os.path.join(config_dir, "bridge_bootstrap.json")) as f:
        bootstrap = json.load(f)

    locking_door = bootstrap["LockingChain"]["DoorAccount"]["Address"]

    # fund needed accounts on the locking chain
    accounts_locking_fund = set(
        [locking_door]
        + bootstrap["LockingChain"]["WitnessRewardAccounts"]
        + bootstrap["LockingChain"]["WitnessSubmitAccounts"]
    )
    for account in accounts_locking_fund:
        fund_result = cli_runner.invoke(
            main, ["fund", f"--account={account}", "--chain=locking_chain"]
        )
        assert fund_result.exit_code == 0, fund_result.output

    # build bridge
    build_result = cli_runner.invoke(
        main,
        [
            "bridge",
            "build",
            "--name=test_bridge",
            "--chains",
            "locking_chain",
            "issuing_chain",
            "--verbose",
        ],
    )
    assert build_result.exit_code == 0, build_result.output

    # start witness servers
    start_result = cli_runner.invoke(
        main, ["server", "start-all", "--witness-only", "--verbose"]
    )
    assert start_result.exit_code == 0, start_result.output
    time.sleep(0.2)

    yield

    # stop servers
    stop_result = cli_runner.invoke(main, ["server", "stop", "--all"])
    assert stop_result.exit_code == 0, stop_result.output


@pytest.fixture(scope="class")
def bridge_build_setup():
    # reset CLI config file
    config_file = os.path.join(get_config_folder(), "config.json")
    os.remove(config_file)
    with open(config_file, "w") as f:
        data = {"chains": [], "witnesses": [], "bridges": []}
        json.dump(data, f, indent=4)

    cli_runner = CliRunner()

    # create config files
    result = cli_runner.invoke(main, ["server", "create-config", "all"])
    assert result.exit_code == 0

    # start rippled servers
    start_result = cli_runner.invoke(
        main, ["server", "start-all", "--rippled-only", "--verbose"]
    )
    assert start_result.exit_code == 0, start_result.output
    time.sleep(1.5)

    # fund locking door
    config_dir = os.path.abspath(os.getenv("XCHAIN_CONFIG_DIR"))
    with open(os.path.join(config_dir, "bridge_bootstrap.json")) as f:
        bootstrap = json.load(f)

    locking_door = bootstrap["LockingChain"]["DoorAccount"]["Address"]

    # fund needed accounts on the locking chain
    accounts_locking_fund = set(
        [locking_door]
        + bootstrap["LockingChain"]["WitnessRewardAccounts"]
        + bootstrap["LockingChain"]["WitnessSubmitAccounts"]
    )
    for account in accounts_locking_fund:
        fund_result = cli_runner.invoke(
            main, ["fund", f"--account={account}", "--chain=locking_chain"]
        )
        assert fund_result.exit_code == 0, fund_result.output

    yield

    # stop servers
    stop_result = cli_runner.invoke(main, ["server", "stop", "--all"])
    assert stop_result.exit_code == 0, stop_result.output
