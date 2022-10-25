import json
import os
import re
import signal
import subprocess
import time

import psutil
import pytest

import docker
from sidechain_cli.main import main
from sidechain_cli.server.start import _DOCKER_COMPOSE
from sidechain_cli.utils import get_config
from sidechain_cli.utils.config_file import CONFIG_FOLDER


@pytest.mark.usefixtures("runner")
class TestServer:
    def test_list(self, runner):
        server_list = runner.invoke(main, ["server", "list"])
        lines = server_list.output.split("\n")
        assert lines[0] == "Chains:"
        assert re.match(
            r"^ +name +\| +pid +\| +exe +\| +config +\| +ws_ip +\| +ws_port +\| +"
            r"http_ip +\| +http_port *$",
            lines[1],
        )
        assert re.match(r"^-+\+-+\+-+\+-+\+-+\+-+\+-+\+-+$", lines[2])
        assert re.match(
            r"^ *issuing_chain *\| *[0-9]+ *\| *[a-zA-Z0-9-_\.\/]+ *\| *"
            r"[a-zA-Z0-9-_\/\.]+ *\| *[0-9\.]+ *\| *[0-9]+ *\| *[0-9\.]+ *\| *[0-9]+"
            r" *$",
            lines[3],
        )
        assert re.match(
            r"^ *locking_chain *\| *[0-9]+ *\| *[a-zA-Z0-9-_\.\/]+ *\| *"
            r"[a-zA-Z0-9-_\/\.]+ *\| *[0-9\.]+ *\| *[0-9]+ *\| *[0-9\.]+ *\| *[0-9]+"
            r" *$",
            lines[4],
        )
        assert lines[5] == ""

        assert all([f"witness{i}" in server_list.output for i in range(5)])

        assert lines[6] == "Witnesses:"
        assert re.match(
            r"^ +name +\| +pid +\| +exe +\| +config +\| *ip *\| *rpc_port *$",
            lines[7],
        )
        assert re.match(r"^-+\+-+\+-+\+-+\+-+\+-+$", lines[8])
        assert re.match(
            r"^ *witness[0-9] *\| *[0-9]+ *\| *[a-zA-Z0-9-_\.\/]+ *\| *"
            r"[a-zA-Z0-9-_\/\.]+ *\| *[0-9\.]+ *\| *[0-9]+ *$",
            lines[9],
        )
        assert re.match(
            r"^ *witness[0-9] *\| *[0-9]+ *\| *[a-zA-Z0-9-_\.\/]+ *\| *"
            r"[a-zA-Z0-9-_\/\.]+ *\| *[0-9\.]+ *\| *[0-9]+ *$",
            lines[10],
        )
        assert re.match(
            r"^ *witness[0-9] *\| *[0-9]+ *\| *[a-zA-Z0-9-_\.\/]+ *\| *"
            r"[a-zA-Z0-9-_\/\.]+ *\| *[0-9\.]+ *\| *[0-9]+ *$",
            lines[11],
        )
        assert re.match(
            r"^ *witness[0-9] *\| *[0-9]+ *\| *[a-zA-Z0-9-_\.\/]+ *\| *"
            r"[a-zA-Z0-9-_\/\.]+ *\| *[0-9\.]+ *\| *[0-9]+ *$",
            lines[12],
        )
        assert re.match(
            r"^ *witness[0-9] *\| *[0-9]+ *\| *[a-zA-Z0-9-_\.\/]+ *\| *"
            r"[a-zA-Z0-9-_\/\.]+ *\| *[0-9\.]+ *\| *[0-9]+ *$",
            lines[13],
        )
        assert lines[14] == ""

    def test_list_dead_process(self, runner):
        # TODO: remove side effects of this test case
        # (witness2 is no longer running for subsequent tests)
        process_to_kill = "witness2"

        initial_list = runner.invoke(main, ["server", "list"])
        assert process_to_kill in initial_list.output

        if os.getenv("WITNESSD_EXE") == "docker":
            to_run = [*_DOCKER_COMPOSE, "stop", process_to_kill]
            subprocess.run(to_run, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            docker_client = docker.from_env()
            try:
                container = docker_client.containers.get(process_to_kill)
                assert container.status != "running"
            except docker.errors.NotFound:
                assert True
        else:
            witness = get_config().get_witness(process_to_kill)
            os.kill(witness.pid, signal.SIGINT)

            process = psutil.Process(pid=witness.pid)
            assert (
                not psutil.pid_exists(witness.pid)
                or process.status() == psutil.STATUS_ZOMBIE
            )
        time.sleep(0.2)  # wait for process to die

        final_list = runner.invoke(main, ["server", "list"])
        assert process_to_kill not in final_list.output

        with open(os.path.join(CONFIG_FOLDER, "config.json")) as f:
            config_file = json.load(f)

        assert (
            len(
                [
                    witness
                    for witness in config_file["witnesses"]
                    if witness["name"] == process_to_kill
                ]
            )
            == 0
        )

    def test_print_rippled(self, runner):
        server_list = runner.invoke(
            main, ["server", "print", "--name", "issuing_chain"]
        )
        if os.getenv("RIPPLED_EXE") == "docker":
            expected1 = subprocess.check_output(
                ["docker", "logs", "issuing_chain"]
            ).decode("utf-8")
        else:
            with open(os.path.join(CONFIG_FOLDER, "issuing_chain.out"), "r") as f:
                expected1 = f.read()

        assert server_list.output == expected1

        if os.getenv("RIPPLED_EXE") != "docker":
            config_dir = os.path.abspath(os.getenv("XCHAIN_CONFIG_DIR"))
            with open(os.path.join(config_dir, "issuing_chain", "debug.log")) as f:
                expected2 = f.read()

            lines = server_list.output.split("\n")
            assert "\n".join(lines[3:]) in expected2

    def test_print_witness(self, runner):
        server_list = runner.invoke(main, ["server", "print", "--name", "witness0"])

        if os.getenv("RIPPLED_EXE") == "docker":
            expected = subprocess.check_output(["docker", "logs", "witness0"]).decode(
                "utf-8"
            )
        else:
            with open(os.path.join(CONFIG_FOLDER, "witness0.out"), "r") as f:
                expected = f.read()

        assert server_list.output == expected

    def test_restart_rippled(self, runner):
        result = runner.invoke(main, ["server", "restart", "--name", "locking_chain"])
        assert result.exit_code == 0

    def test_restart_witness(self, runner):
        result = runner.invoke(main, ["server", "restart", "--name", "witness0"])
        assert result.exit_code == 0

    def test_request(self, runner):
        result = runner.invoke(
            main, ["server", "request", "--name", "locking_chain", "ping"]
        )
        import traceback
        traceback.print_exception(*result.exc_info)
        assert result.exit_code == 0

        expected = {"result": {"role": "admin", "status": "success"}}
        assert json.loads(result.output) == expected
