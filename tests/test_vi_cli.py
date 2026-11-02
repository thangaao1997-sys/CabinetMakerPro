import unittest
from core.vi_cli import preview_sentence
from core.vi_intent import IntentError

class VietnamesePipelineTests(unittest.TestCase):
    def test_preview(self):
        result=preview_sentence("Tạo tủ bếp rộng 600 mm sâu 560 mm cao 820 mm")
        self.assertEqual(result["scene"]["schema_version"],"ai-idea.scene.v1")
        self.assertEqual(len(result["scene"]["objects"]),5)
        self.assertFalse(result["manufacturing_approved"])
        self.assertFalse(result["cutting_preview"]["production_ready"])
        self.assertTrue(result["audit"]["valid_geometry"])
    def test_wardrobe(self):
        result=preview_sentence("Tạo tủ áo rộng 1200 mm sâu 600 mm cao 2400 mm chân 50 mm")
        self.assertEqual(result["scene"]["envelope_mm"]["width"],1200)
        self.assertEqual(len(result["scene"]["objects"]),5)
    def test_prohibit_cnc_request(self):
        with self.assertRaises(IntentError):
            preview_sentence("Tạo tủ bếp rộng 600 mm sâu 560 mm cao 820 mm, xuất CNC")
    def test_reject_unspecified_base(self):
        with self.assertRaises(IntentError):
            preview_sentence("Tạo tủ áo rộng 1200 mm sâu 600 mm cao 2400 mm")
if __name__=="__main__":
    unittest.main()
