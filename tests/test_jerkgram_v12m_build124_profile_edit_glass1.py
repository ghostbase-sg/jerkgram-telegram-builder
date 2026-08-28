from pathlib import Path
import importlib.util
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts/apply_jerkgram_v12m_build124_profile_edit_glass1.py"


class Build124ProfileEditGlassTests(unittest.TestCase):
    def load_patch(self):
        spec = importlib.util.spec_from_file_location("build124_profile_edit_glass", PATCH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def fixture(self) -> str:
        return '''        let ghostBaseGlassEnabled = GhostBaseGlassStyle.isEnabled
        if self.theme !== presentationData.theme {
            self.theme = presentationData.theme
            
            self.backgroundNode.backgroundColor = presentationData.theme.list.itemBlocksBackgroundColor
            
            let textColor = presentationData.theme.list.itemPrimaryTextColor'''

    def test_glass_enabled_uses_translucent_profile_surface(self):
        module = self.load_patch()
        result = module.patch_text(self.fixture(), "single")
        self.assertIn("BUILD124_PROFILE_EDIT_SURFACE1", result)
        self.assertIn("GhostBaseGlassStyle.isEnabled", result)
        self.assertIn("withAlphaComponent", result)
        self.assertIn("overallDarkAppearance", result)

    def test_glass_off_keeps_stock_telegram_background(self):
        module = self.load_patch()
        result = module.patch_text(self.fixture(), "multi")
        self.assertIn(": presentationData.theme.list.itemBlocksBackgroundColor", result)

    def test_opaque_direct_assignment_is_removed_from_owner(self):
        module = self.load_patch()
        result = module.patch_text(self.fixture(), "single")
        self.assertNotIn("self.backgroundNode.backgroundColor = presentationData.theme.list.itemBlocksBackgroundColor", result)

    def test_patch_is_idempotent(self):
        module = self.load_patch()
        once = module.patch_text(self.fixture(), "single")
        self.assertEqual(once, module.patch_text(once, "single"))

    def test_missing_build123_glass_owner_is_rejected(self):
        module = self.load_patch()
        stale = self.fixture().replace("        let ghostBaseGlassEnabled = GhostBaseGlassStyle.isEnabled\n", "")
        with self.assertRaisesRegex(RuntimeError, "Build123 glass owner missing"):
            module.patch_text(stale, "stale")


if __name__ == "__main__":
    unittest.main()
