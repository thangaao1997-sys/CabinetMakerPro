import json
import tempfile
import unittest
from pathlib import Path
from bridge import process_one

CMD = {"schema_version":"ai-idea.command.v1","request_id":"CABINET/1","cabinet_type":"kitchen","dimensions_mm":{"width":600,"depth":560,"height":820}}

class BridgeTest(unittest.TestCase):
    def test_generate(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"input.json"
            p.write_text(json.dumps(CMD))
            result=process_one(p,Path(d)/"out")
            scene=json.loads(Path(result["scene"]).read_text())
            self.assertEqual(scene["schema_version"],"ai-idea.scene.v1")
            self.assertEqual(len(scene["objects"]),5)
            self.assertFalse(result["manufacturing_approved"])
            with self.assertRaises(FileExistsError):
                process_one(p,Path(d)/"out")
    def test_reject_wrong_extension(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"cmd.txt"
            p.write_text(json.dumps(CMD))
            with self.assertRaises(ValueError): process_one(p,Path(d)/"out")
    def test_reject_bad_command(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"bad.json"
            p.write_text(json.dumps({**CMD,"cabinet_type":"shoe"}))
            with self.assertRaises(ValueError): process_one(p,Path(d)/"out")
    def test_reject_oversized(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"big.json"
            p.write_text(" "*128001)
            with self.assertRaises(ValueError): process_one(p,Path(d)/"out")

if __name__=="__main__":
    unittest.main()
