import unittest
from core.vi_intent import IntentError, parse_vietnamese

class VietnameseIntentTests(unittest.TestCase):
    def test_kitchen(self):
        d = parse_vietnamese("Tạo tủ bếp rộng 600 mm sâu 560 mm cao 820 mm")
        self.assertEqual(d["cabinet_type"], "kitchen")
        self.assertEqual(d["base_mm"], 100)
        self.assertEqual(d["body_height_mm"], 720)
        self.assertFalse(d["manufacturing_approved"])
    def test_wardrobe_explicit_base(self):
        d = parse_vietnamese("Tạo tủ áo rộng 1200 mm sâu 600 mm cao 2400 mm chân 50 mm")
        self.assertEqual(d["base_mm"], 50)
    def test_decimal(self):
        d = parse_vietnamese("tạo tủ bếp rộng 600,5 mm sâu 560 mm cao 820 mm")
        self.assertEqual(d["dimensions_mm"]["width"], 600.5)
    def test_whitespace(self):
        d = parse_vietnamese(" TẠO  TỦ BẾP  RỘNG 600 mm\n sâu 560 mm cao 820 mm ")
        self.assertEqual(d["dimensions_mm"]["depth"], 560)
    def test_missing_other_base(self):
        with self.assertRaises(IntentError):
            parse_vietnamese("tạo tủ giày rộng 700 mm sâu 340 mm cao 1600 mm")
    def test_explicit_other_base(self):
        d = parse_vietnamese("tạo tủ giày rộng 700 mm sâu 340 mm cao 1600 mm chân 17 mm")
        self.assertEqual(d["base_mm"], 17)
    def test_reject_mixed_prose(self):
        with self.assertRaises(IntentError):
            parse_vietnamese("tạo tủ bếp rộng 600 mm sâu 560 mm cao 820 mm và xuất cnc")
    def test_reject_edit_instruction(self):
        with self.assertRaises(IntentError):
            parse_vietnamese("chỉ sửa màu tủ bếp rộng 600 mm sâu 560 mm cao 820 mm")
    def test_reject_negative(self):
        with self.assertRaises(IntentError):
            parse_vietnamese("tạo tủ bếp rộng -600 mm sâu 560 mm cao 820 mm")
    def test_reject_nonstandard_base(self):
        with self.assertRaises(IntentError):
            parse_vietnamese("tạo tủ bếp rộng 600 mm sâu 560 mm cao 820 mm chân 50 mm")
    def test_reject_unknown_units(self):
        with self.assertRaises(IntentError):
            parse_vietnamese("tạo tủ bếp rộng 60 cm sâu 560 mm cao 820 mm")
    def test_reject_small_size(self):
        with self.assertRaises(IntentError):
            parse_vietnamese("tạo tủ bếp rộng 20 mm sâu 560 mm cao 820 mm")
if __name__ == "__main__":
    unittest.main()
