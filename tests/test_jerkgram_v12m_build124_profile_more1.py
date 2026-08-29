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
        }

        var expandBackgroundFrame = expandFrame
        expandBackgroundFrame.origin.x -= 50.0
        expandBackgroundFrame.size.width += 50.0
        self.expandBackgroundNode.frame = expandBackgroundFrame
        // MARK: Jerkgram v1.2L BUILD123_DESCRIPTION_EXPAND_GLASS1
        let expandSurfaceColor: UIColor
        if GhostBaseGlassStyle.isEnabled {
            expandSurfaceColor = UIColor(
                white: presentationData.theme.overallDarkAppearance ? 0.0 : 1.0,
                alpha: presentationData.theme.overallDarkAppearance ? 0.26 : 0.18
            )
        } else {
            expandSurfaceColor = presentationData.theme.list.itemBlocksBackgroundColor
        }
        self.expandBackgroundNode.image = generateExpandBackground(size: expandBackgroundFrame.size, color: expandSurfaceColor)
'''

    def test_more_reserves_text_layout_space_instead_of_covering_glyphs(self):
        module = self.load_patch()
        result = module.patch_text(self.fixture())
        self.assertIn("BUILD124_PROFILE_MORE_CUTOUT1", result)
        self.assertIn("TextNodeCutout(bottomRight:", result)
        self.assertIn("expandSize.width", result)
        self.assertIn("self.textNode.cutout = nil", result)
        self.assertIn("textLayout = self.textNode.updateLayoutInfo", result)
        self.assertIn("BUILD124_PROFILE_MORE_NO_OVERLAY1", result)
        self.assertIn("self.expandBackgroundNode.image = nil", result)
        self.assertNotIn("expandBackgroundFrame.origin.x -= 50.0", result)

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
