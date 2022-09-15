import unittest

from click.testing import CliRunner

from sidechain_cli.main import main


class TestServer(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        start_result = self.runner.invoke(main, ["server", "start-all"])
        assert start_result.exit_code == 0

    def tearDown(self):
        stop_result = self.runner.invoke(main, ["server", "stop", "--all"])
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
