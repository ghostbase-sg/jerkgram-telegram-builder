import importlib.util
from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts" / "apply_jerkgram_v12q_build128_bio_corner_owner1.py"


class Build128BioCornerOwnerTests(unittest.TestCase):
    def load_patch(self):
        self.assertTrue(PATCH.is_file(), "Build128 bio-corner correction is missing")
        spec = importlib.util.spec_from_file_location("build128_bio_corner_owner", PATCH)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module

    def build126_fixture(self):
        return '''        // MARK: Jerkgram v1.2O BUILD126_PROFILE_BIO_CORNER_MASK1
        if GhostBaseGlassStyle.isEnabled {
            self.maskNode.image = nil
            self.cornerRadius = hasCorners ? 26.0 : 0.0
            self.clipsToBounds = hasCorners
            self.layer.maskedCorners = []
        } else {
            self.maskNode.image = hasCorners ? PresentationResourcesItemList.cornersImage(presentationData.theme, top: hasTopCorners, bottom: hasBottomCorners, glass: true) : nil
            self.cornerRadius = 0.0
            self.clipsToBounds = true
            self.layer.maskedCorners = []
        }
        transition.updateFrame(node: self.maskNode, frame: CGRect(origin: CGPoint(x: safeInsets.left, y: 0.0), size: CGSize(width: width - safeInsets.left - safeInsets.right, height: height)))
'''

    def test_glass_owner_removes_the_triangle_raster_without_adding_a_second_radius(self):
        module = self.load_patch()
        result = module.patch_text(self.build126_fixture())
        self.assertIn(module.MARKER, result)
        self.assertIn("if GhostBaseGlassStyle.isEnabled", result)
        self.assertIn("self.maskNode.image = nil", result)
        self.assertIn("PresentationResourcesItemList.cornersImage", result)
        self.assertNotIn("self.cornerRadius", result)
        self.assertNotIn("self.layer.maskedCorners", result)

    def test_is_idempotent(self):
        module = self.load_patch()
        once = module.patch_text(self.build126_fixture())
        self.assertEqual(once, module.patch_text(once))


if __name__ == "__main__":
    unittest.main()
