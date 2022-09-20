import os
import shutil
import tempfile
import unittest
import unittest.mock

from click.testing import CliRunner

from sidechain_cli.main import main


class TestBasicCreation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tempdir = tempfile.TemporaryDirectory()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tempdir.name)

    def test_create_config(self):
        with unittest.mock.patch.dict(
            os.environ,
            {
                **os.environ,
                "XCHAIN_CONFIG_DIR": self.tempdir.name,
            },
        ):
            runner = CliRunner()
            create_result = runner.invoke(main, ["server", "create-config", "all"])
            self.assertEqual(create_result.exit_code, 0)

            for name in ["locking_chain", "issuing_chain"]:
                self.assertIn(name, os.listdir(self.tempdir.name))
                subfolder = os.path.join(self.tempdir.name, name)
                self.assertTrue(os.path.isdir(subfolder))

                self.assertIn("db", os.listdir(subfolder))
                self.assertTrue(os.path.isdir(os.path.join(subfolder, "db")))

                self.assertIn("rippled.cfg", os.listdir(subfolder))
                self.assertTrue(os.path.isfile(os.path.join(subfolder, "rippled.cfg")))

            for name in [f"witness{i}" for i in range(5)]:
                self.assertIn(name, os.listdir(self.tempdir.name))
                subfolder = os.path.join(self.tempdir.name, name)
                self.assertTrue(os.path.isdir(subfolder))

                self.assertIn("db", os.listdir(subfolder))
                self.assertTrue(os.path.isdir(os.path.join(subfolder, "db")))

                self.assertIn("witness.json", os.listdir(subfolder))
                self.assertTrue(os.path.isfile(os.path.join(subfolder, "witness.json")))
