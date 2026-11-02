import unittest

from core.command_center import plan_request


KITCHEN = "Tạo tủ bếp rộng 600 mm sâu 560 mm cao 820 mm"
WARDROBE = "Tạo tủ áo rộng 1200 mm sâu 600 mm cao 2400 mm chân 50 mm"


class CommandCenterTests(unittest.TestCase):
    def test_kitchen_preview(self):
        result = plan_request(KITCHEN)
        self.assertEqual(result["status"], "draft_preview_ready")
        self.assertEqual(result["schema_version"], "ai-idea.workplan.v1")
        self.assertEqual(result["preview"]["command"]["base_mm"], 100)
        self.assertEqual(len(result["preview"]["scene"]["objects"]), 5)
        self.assertFalse(result["manufacturing_approved"])
        self.assertFalse(result["model_write_allowed"])
        self.assertFalse(result["cnc_export_allowed"])
        self.assertEqual(result["side_effects"], [])

    def test_wardrobe_explicit_base(self):
        result = plan_request(WARDROBE)
        self.assertEqual(result["preview"]["command"]["base_mm"], 50)
        self.assertIn("joinery", result["preview"]["missing_decisions"])

    def test_locked_design_blocks(self):
        result = plan_request(KITCHEN, target_model_locked=True)
        self.assertEqual(result["status"], "blocked_locked_design")
        self.assertIsNone(result["preview"])
        self.assertFalse(result["model_write_allowed"])

    def test_rejects_unapproved_cnc_request(self):
        result = plan_request(KITCHEN + " xuất CNC")
        self.assertEqual(result["status"], "rejected")
        self.assertIsNone(result["preview"])

    def test_rejects_ambiguous_cabinet_base(self):
        result = plan_request("Tạo tủ áo rộng 1200 mm sâu 600 mm cao 2400 mm")
        self.assertEqual(result["status"], "rejected")

    def test_rejects_unrelated_edits(self):
        result = plan_request("chỉ sửa cánh tủ sang be")
        self.assertEqual(result["status"], "rejected")

    def test_deterministic_command_hash(self):
        a = plan_request(KITCHEN)
        b = plan_request("  TẠO   TỦ BẾP RỘNG 600 mm sâu 560 mm cao 820 mm ")
        self.assertEqual(a["command_sha256"], b["command_sha256"])

    def test_distinct_geometry_hash(self):
        a = plan_request(KITCHEN)
        b = plan_request("Tạo tủ bếp rộng 650 mm sâu 560 mm cao 820 mm")
        self.assertNotEqual(a["command_sha256"], b["command_sha256"])

    def test_rejects_unknown_type(self):
        self.assertEqual(
            plan_request("Tạo tủ bàn rộng 600 mm sâu 560 mm cao 820 mm")["status"],
            "rejected",
        )

    def test_rejects_non_boolean_lock(self):
        with self.assertRaises(TypeError):
            plan_request(KITCHEN, target_model_locked="false")

    def test_rejects_invalid_request_id(self):
        with self.assertRaises(ValueError):
            plan_request(KITCHEN, request_id="")

    def test_no_production_flag(self):
        result = plan_request(KITCHEN)
        self.assertFalse(result["preview"]["scene"]["manufacturing_approved"])
        self.assertFalse(result["preview"]["cutting_preview"]["production_ready"])
        self.assertTrue(result["requires_workshop_approval"])


if __name__ == "__main__":
    unittest.main()
