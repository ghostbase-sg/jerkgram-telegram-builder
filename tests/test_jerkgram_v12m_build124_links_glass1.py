import importlib.util
from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts" / "apply_jerkgram_v12m_build124_links_glass1.py"
VERIFY = REPO / "scripts" / "verify_jerkgram_v12m_build124_links_glass1.py"


class Build124LinksGlassTests(unittest.TestCase):
    def load_patch(self):
        spec = importlib.util.spec_from_file_location("build124_links_glass", PATCH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def build123_owner(self) -> str:
        return '''        // MARK: Jerkgram v1.2D BUILD115_LINKS_READABILITY_OWNER1
        // PeerInfoListPaneNode is the actual visible owner for Links.
        // Keep dark profile sources transparent. On bright sources,
        // add one local neutral black readability surface only here.
        if self.jerkgramLinksReadabilityEnabled {
            let luminance = (
                UserDefaults.standard.object(
                    forKey: "Jerkgram.ProfileBackdrop.SourceLuminance"
                ) as? NSNumber
            )?.doubleValue ?? 0.0

            let lightness = max(
                0.0,
                min(
                    1.0,
                    (CGFloat(luminance) - 0.55) / 0.45
                )
            )

            let readabilityColor = UIColor.black.withAlphaComponent(
                0.26 * lightness
            )

            self.backgroundColor = readabilityColor
            self.listNode.backgroundColor = readabilityColor
        }

        // MARK: Jerkgram v1.2L BUILD123_LINKS_INTRINSIC_GLASS1
        if self.ghostBaseGlassEnabled && !self.jerkgramLinksReadabilityEnabled {
            self.glassBackgroundView.isHidden = false
        } else {
            self.glassBackgroundView.isHidden = true
            transition.updateFrame(
                view: self.glassBackgroundView,
                frame: self.jerkgramLinksReadabilityEnabled ? .zero : self.glassBackgroundView.frame
            )
        }
'''

    def test_links_material_uses_a_bounded_links_card_not_the_pane_background(self):
        module = self.load_patch()
        result = module.patch_text(self.build123_owner())
        self.assertIn("BUILD124_LINKS_INTRINSIC_MATERIAL1", result)
        self.assertIn("let linksFrame = CGRect", result)
        self.assertIn("UIVisualEffectView", result)
        self.assertIn("visibleContentOffset", result)
        self.assertIn("CGFloat(topOffset)", result)
        self.assertIn("self.listNode.insets.bottom", result)
        self.assertIn("self.listNode.bounds.size.width", result)
        self.assertIn("self.listNode.bounds.size.height", result)
        self.assertNotIn("self.listNode.visibleSize", result)
        self.assertNotIn("visibleBottomContentOffset", result)
        self.assertNotIn("0.26 * lightness", result)
        self.assertNotIn("self.backgroundColor = readabilityColor", result)
        self.assertNotIn("self.listNode.backgroundColor = readabilityColor", result)

    def test_links_material_is_theme_aware_and_glass_gated(self):
        module = self.load_patch()
        result = module.patch_text(self.build123_owner())
        self.assertIn("if self.ghostBaseGlassEnabled", result)
        self.assertIn(".systemMaterialDark", result)
        self.assertIn(".systemMaterialLight", result)
        self.assertIn("self.backgroundColor = .clear", result)
        self.assertIn("self.listNode.backgroundColor = .clear", result)

    def test_does_not_restore_viewport_glass_plate_for_links(self):
        module = self.load_patch()
        result = module.patch_text(self.build123_owner())
        build123 = result[result.index("BUILD123_LINKS_INTRINSIC_GLASS1"):]
        self.assertIn("else if !self.jerkgramLinksReadabilityEnabled", build123)
        self.assertNotIn("&& self.jerkgramLinksReadabilityEnabled", build123)

    def test_patch_is_idempotent(self):
        module = self.load_patch()
        once = module.patch_text(self.build123_owner())
        twice = module.patch_text(once)
        self.assertEqual(once, twice)
        self.assertEqual(once.count("BUILD124_LINKS_INTRINSIC_MATERIAL1"), 1)

    def test_verifier_uses_the_protocol_safe_links_contract(self):
        verifier = VERIFY.read_text(encoding="utf-8")
        self.assertIn("visibleContentOffset", verifier)
        self.assertIn("self.listNode.bounds.size", verifier)
        self.assertIn('"visibleBottomContentOffset" not in owner', verifier)


if __name__ == "__main__":
    unittest.main()
