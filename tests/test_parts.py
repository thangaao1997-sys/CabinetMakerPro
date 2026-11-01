import unittest
from core.parts import draft_parts,draft_cut_list
from core.ai_idea_core import CommandError

CMD={"schema_version":"ai-idea.command.v1","request_id":"T-001","cabinet_type":"kitchen",
     "dimensions_mm":{"width":600,"depth":560,"height":820}}
class PartsTest(unittest.TestCase):
    def test_envelope(self):
        a=draft_parts(CMD)
        self.assertEqual(len(a["parts"]),5)
        self.assertEqual(a["parts"][0]["size_mm"],{"x":17,"y":553,"z":720})
        self.assertEqual(a["parts"][4]["origin_mm"],{"x":0,"y":553,"z":100})
        self.assertFalse(a["manufacturing_approved"])
    def test_cut_rows(self):
        rows=draft_cut_list(draft_parts(CMD))
        self.assertEqual(sum(r["quantity"] for r in rows),5)
        self.assertEqual(sorted(r["quantity"] for r in rows),[1,2,2])
    def test_other_base(self):
        a=draft_parts({**CMD,"cabinet_type":"wardrobe","base_mm":50})
        self.assertEqual(a["parts"][0]["size_mm"]["z"],770)
    def test_missing_other_base(self):
        with self.assertRaises(CommandError): draft_parts({**CMD,"cabinet_type":"other"})
    def test_unknown_layout(self):
        with self.assertRaises(CommandError): draft_parts(CMD,"unknown")
    def test_short_body(self):
        with self.assertRaises(CommandError):
            draft_parts({**CMD,"dimensions_mm":{"width":600,"depth":560,"height":120}})
    def test_material_override(self):
        a=draft_parts({**CMD,"materials_mm":{"panel":18,"back":9}})
        self.assertEqual(a["parts"][0]["size_mm"]["x"],18)
        self.assertEqual(a["parts"][0]["size_mm"]["y"],551)
    def test_no_false_approval(self):
        a=draft_parts(CMD)
        a["manufacturing_approved"]=True
        with self.assertRaises(CommandError): draft_cut_list(a)
if __name__=="__main__": unittest.main()
