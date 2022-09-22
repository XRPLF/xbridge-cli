import os
import shutil
import tempfile
import unittest
import unittest.mock
from typing import Any, Optional

tempdir: Optional[tempfile.TemporaryDirectory] = None
env_patcher: Optional[Any] = None


def setUpModule():
    global tempdir, env_patcher
    print("Hiiiiiii server")
    tempdir = tempfile.TemporaryDirectory()
    env_patcher = unittest.mock.patch.dict(
        os.environ,
        {
            **os.environ,
            "XCHAIN_CONFIG_DIR": tempdir.name,
        },
    )
    env_patcher.start()
    import pprint

    pprint.pprint(os.environ)


def tearDownModule():
    global tempdir, env_patcher
    env_patcher.stop()
    shutil.rmtree(tempdir.name)
