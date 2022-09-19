import os
import unittest

from click.testing import CliRunner

from sidechain_cli.main import main
from sidechain_cli.utils.config_file import CONFIG_FOLDER


class TestServer(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        cls.runner = CliRunner()
        start_result = cls.runner.invoke(main, ["server", "start-all"])
        assert start_result.exit_code == 0

    @classmethod
    def tearDownClass(cls):
        stop_result = cls.runner.invoke(main, ["server", "stop", "--all"])
        assert stop_result.exit_code == 0

    def test_list(self):
        server_list = self.runner.invoke(main, ["server", "list"])
        lines = server_list.output.split("\n")
        self.assertEqual(lines[0], "Chains:")
        self.assertRegex(
            lines[1],
            r"^ +name +\| +pid +\| +rippled +\| +config +\| +ws_ip +\| +ws_port +\| +"
            r"http_ip +\| +http_port *$",
        )
        self.assertRegex(lines[2], r"^-+\+-+\+-+\+-+\+-+\+-+\+-+\+-+$")
        self.assertRegex(
            lines[3],
            r"^ *issuing_chain *\| *[0-9]+ *\| *[a-zA-Z0-9-_\.\/]+ *\| *"
            r"[a-zA-Z0-9-_\/\.]+ *\| *[0-9\.]+ *\| *[0-9]+ *\| *[0-9\.]+ *\| *[0-9]+"
            r" *$",
        )
        self.assertRegex(
            lines[4],
            r"^ *locking_chain *\| *[0-9]+ *\| *[a-zA-Z0-9-_\.\/]+ *\| *"
            r"[a-zA-Z0-9-_\/\.]+ *\| *[0-9\.]+ *\| *[0-9]+ *\| *[0-9\.]+ *\| *[0-9]+"
            r" *$",
        )
        self.assertEqual(lines[5], "")

        self.assertEqual(lines[6], "Witnesses:")
        self.assertRegex(
            lines[7],
            r"^ +name +\| +pid +\| +witnessd +\| +config +\| *ip *\| *rpc_port *$",
        )
        self.assertRegex(lines[8], r"^-+\+-+\+-+\+-+\+-+\+-+$")
        self.assertRegex(
            lines[9],
            r"^ *witness[0-9] *\| *[0-9]+ *\| *[a-zA-Z0-9-_\.\/]+ *\| *"
            r"[a-zA-Z0-9-_\/\.]+ *\| *[0-9\.]+ *\| *[0-9]+ *$",
        )
        self.assertRegex(
            lines[10],
            r"^ *witness[0-9] *\| *[0-9]+ *\| *[a-zA-Z0-9-_\.\/]+ *\| *"
            r"[a-zA-Z0-9-_\/\.]+ *\| *[0-9\.]+ *\| *[0-9]+ *$",
        )
        self.assertRegex(
            lines[11],
            r"^ *witness[0-9] *\| *[0-9]+ *\| *[a-zA-Z0-9-_\.\/]+ *\| *"
            r"[a-zA-Z0-9-_\/\.]+ *\| *[0-9\.]+ *\| *[0-9]+ *$",
        )
        self.assertRegex(
            lines[12],
            r"^ *witness[0-9] *\| *[0-9]+ *\| *[a-zA-Z0-9-_\.\/]+ *\| *"
            r"[a-zA-Z0-9-_\/\.]+ *\| *[0-9\.]+ *\| *[0-9]+ *$",
        )
        self.assertRegex(
            lines[13],
            r"^ *witness[0-9] *\| *[0-9]+ *\| *[a-zA-Z0-9-_\.\/]+ *\| *"
            r"[a-zA-Z0-9-_\/\.]+ *\| *[0-9\.]+ *\| *[0-9]+ *$",
        )
        self.assertEqual(lines[14], "")

    def test_print_rippled(self):
        server_list = self.runner.invoke(
            main, ["server", "print", "--name", "issuing_chain"]
        )
        with open(os.path.join(CONFIG_FOLDER, "issuing_chain.out"), "r") as f:
            expected_output1 = f.read()

        config_dir = os.path.abspath(os.getenv("XCHAIN_CONFIG_DIR"))
        with open(os.path.join(config_dir, "issuing_chain", "debug.log")) as f:
            expected_output2 = f.read()

        self.assertEqual(server_list.output, expected_output1)

        lines = server_list.output.split("\n")
        self.assertIn("\n".join(lines[3:]), expected_output2)

    def test_print_witness(self):
        server_list = self.runner.invoke(
            main, ["server", "print", "--name", "witness0"]
        )
        with open(os.path.join(CONFIG_FOLDER, "witness0.out"), "r") as f:
            expected_output = f.read()

        self.assertEqual(server_list.output, expected_output)

    def test_restart_rippled(self):
        result = self.runner.invoke(
            main, ["server", "restart", "--name", "locking_chain"]
        )
        assert result.exit_code == 0

    def test_restart_witness(self):
        result = self.runner.invoke(main, ["server", "restart", "--name", "witness0"])
        assert result.exit_code == 0
