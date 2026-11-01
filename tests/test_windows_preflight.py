import tempfile
import unittest
import zipfile
from pathlib import Path

from tools.build_rbz import build, ROOT
from tools.windows_preflight import (
    PreflightError, inspect_host, inspect_rbz, make_report
)


class WindowsPreflightTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.rbz = self.root / "AI_IDEA_TEST.rbz"
        build(self.rbz)

    def test_packaged_rbz_and_source_parity(self):
        result = inspect_rbz(self.rbz, ROOT)
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["files"]), 5)
        self.assertTrue(result["source_parity_checked"])

    def test_host_without_sketchup(self):
        host = inspect_host(os_name="Windows", appdata=str(self.root),
                            program_files=str(self.root), python_version=(3, 11))
        self.assertTrue(host["windows"])
        self.assertFalse(host["sketchup_exe_detected"])
        self.assertFalse(host["actual_sketchup_execution_tested"])

    def test_simulated_executable_presence(self):
        exe = self.root / "SketchUp" / "SketchUp 2025" / "SketchUp.exe"
        exe.parent.mkdir(parents=True)
        exe.touch()
        host = inspect_host(os_name="Windows", appdata=str(self.root),
                            program_files=str(self.root), python_version=(3, 11))
        self.assertTrue(host["sketchup_exe_detected"])
        self.assertFalse(host["actual_sketchup_execution_tested"])

    def test_full_report_is_read_only(self):
        report = make_report(self.rbz, ROOT, os_name="Linux", appdata="",
                             program_files="", python_version=(3, 11))
        self.assertFalse(report["design_changes_performed"])
        self.assertFalse(report["software_installed"])
        self.assertFalse(report["network_access_started"])
        self.assertFalse(report["manufacturing_approved"])

    def test_reject_wrong_archive_layout(self):
        bad = self.root / "unexpected.rbz"
        with zipfile.ZipFile(bad, "w") as z:
            z.writestr("../evil.rb", "puts 'bad'")
        with self.assertRaises(PreflightError):
            inspect_rbz(bad)

    def test_reject_duplicate_entries(self):
        bad = self.root / "duplicate.rbz"
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(bad, "w") as z:
                z.writestr("ai_idea_v10.rb", "one")
                z.writestr("ai_idea_v10.rb", "two")
                z.writestr("ai_idea_v10/main.rb", "three")
        with self.assertRaises(PreflightError):
            inspect_rbz(bad)

    def test_reject_source_mismatch(self):
        fake_root = self.root / "different"
        (fake_root / "plugin" / "ai_idea_v10").mkdir(parents=True)
        for path in ("ai_idea_v10.rb", "ai_idea_v10/main.rb",
                     "ai_idea_v10/scene_importer.rb", "ai_idea_v10/diagnostics.rb", "ai_idea_v10/model_audit.rb"):
            target = fake_root / "plugin" / path
            target.write_text("incorrect source", encoding="utf-8")
        with self.assertRaises(PreflightError):
            inspect_rbz(self.rbz, fake_root)

    def test_reject_corrupt_archive(self):
        bad = self.root / "bad.rbz"
        bad.write_bytes(b"this is not zip")
        with self.assertRaises(PreflightError):
            inspect_rbz(bad)

    def test_python_version(self):
        old = inspect_host(os_name="Windows", python_version=(3, 10))
        self.assertFalse(old["python_compatible"])


if __name__ == "__main__":
    unittest.main()
