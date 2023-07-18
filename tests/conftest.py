import json
import os
import tempfile
import traceback
import unittest
import unittest.mock
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

import pytest
from click.testing import CliRunner

from xbridge_cli.main import main
from xbridge_cli.utils import get_config_folder

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
    if os.getenv("RIPPLED_EXE") is None:
        raise Exception("Environment variable `RIPPLED_EXE` is not defined.")
    if os.getenv("WITNESSD_EXE") is None:
        raise Exception("Environment variable `WITNESSD_EXE` is not defined.")

    if os.getenv("CI") != "True":
        config_dir = tempfile.TemporaryDirectory()
        env_vars = unittest.mock.patch.dict(
            os.environ,
            {
                "XCHAIN_CONFIG_DIR": config_dir.name,
            },
        )
        env_vars.start()
        mocked_vars.append(env_vars)

        mocked_home_dir = tempfile.TemporaryDirectory()
        config_var = unittest.mock.patch(
            "xbridge_cli.utils.config_file.config_file.CONFIG_FOLDER",
            mocked_home_dir.name,
        )
        config_var.start()
        mocked_vars.append(config_var)

        config_file = os.path.join(mocked_home_dir.name, "config.json")
        with open(config_file, "w") as f:
            data: Dict[str, List[Any]] = {"chains": [], "witnesses": [], "bridges": []}
            json.dump(data, f, indent=4)
        config_var2 = unittest.mock.patch(
            "xbridge_cli.utils.config_file.config_file._CONFIG_FILE",
            config_file,
        )
        config_var2.start()
        mocked_vars.append(config_var2)


def pytest_unconfigure(config):
    """
    Called after whole test run finished, right before
    returning the exit status to the system.
    """
    global mocked_vars
    for var in mocked_vars:
        var.stop()
    mocked_vars = []


def _reset_cli_config() -> None:
    config_file = os.path.join(get_config_folder(), "config.json")
    os.remove(config_file)
    with open(config_file, "w") as f:
        data: Dict[str, List[Any]] = {"chains": [], "witnesses": [], "bridges": []}
        json.dump(data, f, indent=4)


def _create_config_files() -> None:
    cli_runner = CliRunner()

    # create config files
    params = ["server", "create-config", "all"]
    if _is_docker():
        params.append("--docker")
    result = cli_runner.invoke(main, params)
    assert result.exit_code == 0, result.output


@contextmanager
def _base_fixture():
    _reset_cli_config()
    _create_config_files()

    cli_runner = CliRunner()

    # start servers
    start_result = cli_runner.invoke(main, ["server", "start-all", "--verbose"])
    if start_result.exit_code != 0:
        print(start_result.output)
        traceback.print_exception(start_result.exception)
        assert start_result.exit_code == 0

    try:
        yield cli_runner
    finally:
        # stop servers
        stop_result = cli_runner.invoke(main, ["server", "stop", "--all"])
        assert stop_result.exit_code == 0, stop_result.output


@pytest.fixture(scope="class")
def runner():
    with _base_fixture() as cli_runner:
        yield cli_runner


@pytest.fixture(scope="class")
def create_bridge():
    with _base_fixture() as cli_runner:
        # build bridge
        build_result = cli_runner.invoke(
            main,
            [
                "bridge",
                "build",
                "--name=test_bridge",
                "--fund-locking",
                "--verbose",
            ],
        )
        assert build_result.exit_code == 0, build_result.output

        yield


@pytest.fixture(scope="function")
def bridge_build_setup():
    with _base_fixture():
        yield
