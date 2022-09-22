import os

from sidechain_cli.main import main


class TestBasicCreation:
    def test_create_config(self, runner):
        tempdir = os.getenv("XCHAIN_CONFIG_DIR")
        create_result = runner.invoke(main, ["server", "create-config", "all"])
        assert create_result.exit_code == 0

        for name in ["locking_chain", "issuing_chain"]:
            assert name in os.listdir(tempdir)
            subfolder = os.path.join(tempdir, name)
            assert os.path.isdir(subfolder) is True

            assert "db" in os.listdir(subfolder)
            assert os.path.isdir(os.path.join(subfolder, "db")) is True

            assert "rippled.cfg" in os.listdir(subfolder)
            assert os.path.isfile(os.path.join(subfolder, "rippled.cfg")) is True

        for name in [f"witness{i}" for i in range(5)]:
            assert name in os.listdir(tempdir)
            subfolder = os.path.join(tempdir, name)
            assert os.path.isdir(subfolder) is True

            assert "db" in os.listdir(subfolder)
            assert os.path.isdir(os.path.join(subfolder, "db")) is True

            assert "witness.json" in os.listdir(subfolder)
            assert os.path.isfile(os.path.join(subfolder, "witness.json")) is True
