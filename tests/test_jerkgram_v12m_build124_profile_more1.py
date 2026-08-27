from pathlib import Path
import importlib.util
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts/apply_jerkgram_v12m_build124_profile_more1.py"


class Build124ProfileMoreTests(unittest.TestCase):
    def load_patch(self):
        spec = importlib.util.spec_from_file_location("build124_profile_more", PATCH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def fixture(self) -> str:
        return '''        let textLayout = self.textNode.updateLayoutInfo(CGSize(width: width - sideInset * 2.0 - additionalSideInset, height: .greatestFiniteMagnitude))
        let textSize = textLayout.size
        
        let additionalTextSize = self.additionalTextNode.updateLayout(CGSize(width: width - sideInset * 2.0, height: .greatestFiniteMagnitude))
        
        var displayMore = false
        if !self.isExpanded {
            if textLayout.truncated || text.count < item.text.count {
                displayMore = true
            }
        }
        
        if case .multiLine = item.textBehavior, displayMore {
            self.expandBackgroundNode.isHidden = false
            self.expandNode.isHidden = false
            self.expandButonNode.isHidden = false
        } else {
            self.expandBackgroundNode.isHidden = true
            self.expandNode.isHidden = true
            self.expandButonNode.isHidden = true
        }'''

    def test_more_reserves_text_layout_space_instead_of_covering_glyphs(self):
        module = self.load_patch()
        result = module.patch_text(self.fixture())
        self.assertIn("BUILD124_PROFILE_MORE_CUTOUT1", result)
        self.assertIn("TextNodeCutout(bottomRight:", result)
        self.assertIn("expandSize.width", result)
        self.assertIn("self.textNode.cutout = nil", result)
        self.assertIn("textLayout = self.textNode.updateLayoutInfo", result)

    def test_cutout_only_applies_to_collapsed_multiline_with_more(self):
        module = self.load_patch()
        result = module.patch_text(self.fixture())
        self.assertIn("if case .multiLine = item.textBehavior, displayMore", result)
        self.assertIn("TextNodeCutout(bottomRight:", result)
        self.assertLess(
            result.index("if case .multiLine = item.textBehavior, displayMore"),
            result.index("TextNodeCutout(bottomRight:")
        )

    def test_patch_is_idempotent(self):
        module = self.load_patch()
        once = module.patch_text(self.fixture())
        self.assertEqual(once, module.patch_text(once))


if __name__ == "__main__":
    unittest.main()
