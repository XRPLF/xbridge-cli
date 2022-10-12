import json
import os
import re

import pytest

from sidechain_cli.main import main
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

    def test_print_rippled(self, runner):
        server_list = runner.invoke(
            main, ["server", "print", "--name", "issuing_chain"]
        )
        with open(os.path.join(CONFIG_FOLDER, "issuing_chain.out"), "r") as f:
            expected_output1 = f.read()

        config_dir = os.path.abspath(os.getenv("XCHAIN_CONFIG_DIR"))
        with open(os.path.join(config_dir, "issuing_chain", "debug.log")) as f:
            expected_output2 = f.read()

        assert server_list.output == expected_output1

        lines = server_list.output.split("\n")
        assert "\n".join(lines[3:]) in expected_output2

    def test_print_witness(self, runner):
        server_list = runner.invoke(main, ["server", "print", "--name", "witness0"])
        with open(os.path.join(CONFIG_FOLDER, "witness0.out"), "r") as f:
            expected_output = f.read()

        assert server_list.output == expected_output

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
        assert result.exit_code == 0

        expected = {"result": {"role": "admin", "status": "success"}}
        assert json.loads(result.output) == expected
