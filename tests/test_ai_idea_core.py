import unittest
from core.ai_idea_core import CommandError, validate_command
D={"schema_version":"ai-idea.command.v1","request_id":"DEMO-1","cabinet_type":"kitchen","dimensions_mm":{"width":600,"depth":560,"height":820}}
class TestCore(unittest.TestCase):
    def test_kitchen(self):
        a=validate_command(D)
        self.assertEqual((a["base_mm"],a["body_height_mm"]), (100,720))
        self.assertEqual(a["materials_mm"],{"panel":17,"back":7})
        self.assertFalse(a["manufacturing_approved"])
    def test_explicit_other_base(self):
        with self.assertRaises(CommandError): validate_command({**D,"cabinet_type":"wardrobe"})
        for b in (0,17,50):
            self.assertEqual(validate_command({**D,"cabinet_type":"wardrobe","base_mm":b})["base_mm"],b)
    def test_reject_bad_kitchen_base(self):
        with self.assertRaises(CommandError): validate_command({**D,"base_mm":50})
    def test_reject_invalid_dimensions(self):
        for w in (0,-1,20,True,float("nan")):
            with self.assertRaises(CommandError):
                validate_command({**D,"dimensions_mm":{"width":w,"height":820,"depth":560}})
    def test_reject_unknown_fields(self):
        with self.assertRaises(CommandError): validate_command({**D,"run_cnc":True})
    def test_reject_back_too_thick(self):
        with self.assertRaises(CommandError): validate_command({**D,"materials_mm":{"panel":17,"back":560}})
    def test_design_lock(self):
        self.assertTrue(validate_command({**D,"design_lock":True})["design_lock"])
    def test_reject_short_cabinet(self):
        with self.assertRaises(CommandError):
            validate_command({**D,"dimensions_mm":{"width":600,"depth":560,"height":80}})
if __name__ == "__main__": unittest.main()
