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
        print(server_list.output)
        self.assertEqual(lines[0], "Chains:")
        self.assertRegex(
            lines[1],
            r"^ +name +\| +pid +\| +rippled +\| +config +\| +ws_ip +\| +ws_port +\| +http_ip +\| +http_port *$",
        )
        self.assertRegex(lines[2], r"^-+\+-+\+-+\+-+\+-+\+-+\+-+\+-+$")
        self.assertRegex(
            lines[3],
            r"^ *issuing_chain *\| *[0-9]+ *\| *[a-zA-Z0-9-_\.\/]+ *\| *[a-zA-Z0-9-_\/\.]+ *\| *[0-9\.]+ *\| *[0-9]+ *\| *[0-9\.]+ *\| *[0-9]+ *$",
        )
        self.assertRegex(
            lines[4],
            r"^ *locking_chain *\| *[0-9]+ *\| *[a-zA-Z0-9-_\.\/]+ *\| *[a-zA-Z0-9-_\/\.]+ *\| *[0-9\.]+ *\| *[0-9]+ *\| *[0-9\.]+ *\| *[0-9]+ *$",
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
            r"^ *witness[0-9] *\| *[0-9]+ *\| *[a-zA-Z0-9-_\.\/]+ *\| *[a-zA-Z0-9-_\/\.]+ *\| *[0-9\.]+ *\| *[0-9]+ *$",
        )
        self.assertRegex(
            lines[10],
            r"^ *witness[0-9] *\| *[0-9]+ *\| *[a-zA-Z0-9-_\.\/]+ *\| *[a-zA-Z0-9-_\/\.]+ *\| *[0-9\.]+ *\| *[0-9]+ *$",
        )
        self.assertRegex(
            lines[11],
            r"^ *witness[0-9] *\| *[0-9]+ *\| *[a-zA-Z0-9-_\.\/]+ *\| *[a-zA-Z0-9-_\/\.]+ *\| *[0-9\.]+ *\| *[0-9]+ *$",
        )
        self.assertRegex(
            lines[12],
            r"^ *witness[0-9] *\| *[0-9]+ *\| *[a-zA-Z0-9-_\.\/]+ *\| *[a-zA-Z0-9-_\/\.]+ *\| *[0-9\.]+ *\| *[0-9]+ *$",
        )
        self.assertRegex(
            lines[13],
            r"^ *witness[0-9] *\| *[0-9]+ *\| *[a-zA-Z0-9-_\.\/]+ *\| *[a-zA-Z0-9-_\/\.]+ *\| *[0-9\.]+ *\| *[0-9]+ *$",
        )
        self.assertEqual(lines[14], "")


#          name          |   pid | rippled                                           | config                                                              | ws_ip     |   ws_port | http_ip   |   http_port
# ---------------+-------+---------------------------------------------------+---------------------------------------------------------------------+-----------+-----------+-----------+-------------
#  issuing_chain | 64225 | /Users/mvadari/Documents/rippled/mybuild2/rippled | /Users/mvadari/Documents/sidechain-config/issuing_chain/rippled.cfg | 127.0.0.1 |      6008 | 127.0.0.1 |        5006
#  locking_chain | 64226 | /Users/mvadari/Documents/rippled/mybuild2/rippled | /Users/mvadari/Documents/sidechain-config/locking_chain/rippled.cfg | 127.0.0.1 |      6006 | 127.0.0.1 |        5005


# Witnesses:
#  name     |   pid | witnessd                                                           | config                                                          | ip        |   rpc_port
# ----------+-------+--------------------------------------------------------------------+-----------------------------------------------------------------+-----------+------------
#  witness3 | 64227 | /Users/mvadari/Documents/xbridge_witness/my_build/xbridge_witnessd | /Users/mvadari/Documents/sidechain-config/witness3/witness.json | 127.0.0.1 |       6013
#  witness4 | 64228 | /Users/mvadari/Documents/xbridge_witness/my_build/xbridge_witnessd | /Users/mvadari/Documents/sidechain-config/witness4/witness.json | 127.0.0.1 |       6014
#  witness2 | 64229 | /Users/mvadari/Documents/xbridge_witness/my_build/xbridge_witnessd | /Users/mvadari/Documents/sidechain-config/witness2/witness.json | 127.0.0.1 |       6012
#  witness0 | 64230 | /Users/mvadari/Documents/xbridge_witness/my_build/xbridge_witnessd | /Users/mvadari/Documents/sidechain-config/witness0/witness.json | 127.0.0.1 |       6010
#  witness1 | 64231 | /Users/mvadari/Documents/xbridge_witness/my_build/xbridge_witnessd | /Users/mvadari/Documents/sidechain-config/witness1/witness.json | 127.0.0.1 |       6011
