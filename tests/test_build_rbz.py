import tempfile
import unittest
import zipfile
from pathlib import Path
from tools.build_rbz import build, ROOT

class RBZBuildTests(unittest.TestCase):
    def test_build_layout(self):
        with tempfile.TemporaryDirectory() as td:
            output=Path(td)/"AI_IDEA.rbz"
            result=build(output)
            self.assertEqual(result["files"],7)
            self.assertEqual(len(result["sha256"]),64)
            with zipfile.ZipFile(output) as z:
                self.assertEqual(sorted(z.namelist()),sorted([
                    "ai_idea_v10.rb","ai_idea_v10/main.rb","ai_idea_v10/scene_importer.rb","ai_idea_v10/diagnostics.rb","ai_idea_v10/model_audit.rb","ai_idea_v10/geometry_fingerprint.rb","ai_idea_v10/self_test.rb"]))
                self.assertIsNone(z.testzip())
                self.assertIn(b"SketchupExtension.new",z.read("ai_idea_v10.rb"))
    def test_reproducible_archive(self):
        with tempfile.TemporaryDirectory() as td:
            a=build(Path(td)/"a.rbz")
            b=build(Path(td)/"b.rbz")
            self.assertEqual(a["sha256"],b["sha256"])
    def test_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            output=Path(td)/"existing.rbz"
            build(output)
            with self.assertRaises(FileExistsError):
                build(output)
    def test_missing_file(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                build(Path(td)/"out.rbz",Path(td))
if __name__=="__main__":
    unittest.main()
