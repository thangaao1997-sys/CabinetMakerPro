import tempfile
import unittest
import zipfile
from pathlib import Path

from tools.build_rbz import build as build_rbz
from tools.build_windows_bundle import build_bundle


class WindowsStarterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.rbz = self.root / "sample.rbz"
        build_rbz(self.rbz)

    def test_bundle_contents(self):
        output = self.root / "starter.zip"
        report = build_bundle(output, self.rbz)
        self.assertTrue(report["read_only"])
        with zipfile.ZipFile(output) as bundle:
            self.assertIn("AI_IDEA_V1_ALPHA.rbz", bundle.namelist())
            self.assertIn("AI_IDEA_CHECK.cmd", bundle.namelist())
            self.assertIn("tools/windows_preflight.py", bundle.namelist())
            self.assertIn("core/command_center.py", bundle.namelist())
            self.assertEqual(bundle.read("AI_IDEA_V1_ALPHA.rbz"), self.rbz.read_bytes())
            self.assertIsNone(bundle.testzip())

    def test_reproducible(self):
        first = build_bundle(self.root / "a.zip", self.rbz)
        second = build_bundle(self.root / "b.zip", self.rbz)
        self.assertEqual(first["sha256"], second["sha256"])

    def test_prevent_overwrite(self):
        output = self.root / "starter.zip"
        build_bundle(output, self.rbz)
        with self.assertRaises(FileExistsError):
            build_bundle(output, self.rbz)

    def test_reject_invalid_rbz(self):
        damaged = self.root / "damaged.rbz"
        damaged.write_bytes(b"not an rbz")
        with self.assertRaises((ValueError, OSError)):
            build_bundle(self.root / "bad.zip", damaged)

if __name__ == "__main__":
    unittest.main()
