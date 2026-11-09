"""Test archive extraction safety with isolated fixtures."""

import io
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.setup_node import bootstrap_lock, check_digest, extract

WORK = Path(__file__).resolve().parents[1] / ".work"


def setUpModule():
    WORK.mkdir(exist_ok=True)


class ArchiveTests(unittest.TestCase):
    def test_only_one_bootstrap_can_hold_the_installation_lock(self):
        with tempfile.TemporaryDirectory(dir=WORK) as temporary:
            tools = Path(temporary)
            with bootstrap_lock(tools):
                with self.assertRaisesRegex(RuntimeError, "already running"):
                    with bootstrap_lock(tools):
                        self.fail("A second bootstrap acquired the same lock")
            with self.assertRaisesRegex(ValueError, "interrupted"):
                with bootstrap_lock(tools):
                    raise ValueError("interrupted")
            self.assertFalse((tools / ".setup-node.lock").exists())

    def test_corrupt_download_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "checksum"):
            check_digest(b"wrong archive", "sha256", "00" * 32)

    def test_zip_traversal_is_rejected_before_extraction(self):
        data = io.BytesIO()
        with zipfile.ZipFile(data, "w") as archive:
            archive.writestr("../escaped.txt", "bad")
        with tempfile.TemporaryDirectory(dir=WORK) as temporary:
            target = Path(temporary) / "extract"
            with self.assertRaisesRegex(ValueError, "Unsafe"):
                extract(data.getvalue(), target, zipped=True)
            self.assertFalse((Path(temporary) / "escaped.txt").exists())


if __name__ == "__main__":
    unittest.main()
