import unittest
from core.pipeline import generate
from core.ai_idea_core import CommandError
from core.audit import AuditError, audit_draft, export_scene

D={"schema_version":"ai-idea.command.v1","request_id":"IDEA-1","cabinet_type":"kitchen","dimensions_mm":{"width":600,"depth":560,"height":820}}
class IntegrationTests(unittest.TestCase):
    def test_end_to_end(self):
        b=generate(D)
        self.assertEqual(len(b["parts"]["parts"]),5)
        self.assertEqual(b["scene"]["schema_version"],"ai-idea.scene.v1")
        self.assertEqual(b["scene"]["envelope_mm"],D["dimensions_mm"])
        self.assertFalse(b["cutting_preview"]["production_ready"])
        self.assertTrue(b["audit"]["valid_geometry"])
    def test_non_kitchen_needs_base(self):
        with self.assertRaises(CommandError): generate({**D,"cabinet_type":"wardrobe"})
    def test_collision_rejected(self):
        b=generate(D);p=b["parts"];p["parts"][1]["origin_mm"]["x"]=10
        self.assertFalse(audit_draft(p)["valid_geometry"])
        with self.assertRaises(AuditError): export_scene(p)
    def test_back_thickness_override(self):
        b=generate({**D,"materials_mm":{"panel":18,"back":9}})
        self.assertEqual(b["parts"]["parts"][-1]["size_mm"]["y"],9)
if __name__=="__main__": unittest.main()
