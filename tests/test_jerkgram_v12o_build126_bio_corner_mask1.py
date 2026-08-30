import importlib.util
from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts" / "apply_jerkgram_v12o_build126_bio_corner_mask1.py"


class Build126BioCornerMaskTests(unittest.TestCase):
    def load_patch(self):
        self.assertTrue(PATCH.is_file(), "Build126 bio-corner owner patch is missing")
        spec = importlib.util.spec_from_file_location("build126_bio_corner_mask", PATCH)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module

    def owner_fixture(self):
        return '''        let hasCorners = hasCorners && (topItem == nil || bottomItem == nil)
        let hasTopCorners = hasCorners && topItem == nil
        let hasBottomCorners = hasCorners && bottomItem == nil
        self.maskNode.image = hasCorners ? PresentationResourcesItemList.cornersImage(presentationData.theme, top: hasTopCorners, bottom: hasBottomCorners, glass: true) : nil
        transition.updateFrame(node: self.maskNode, frame: CGRect(origin: CGPoint(x: safeInsets.left, y: 0.0), size: CGSize(width: width - safeInsets.left - safeInsets.right, height: height)))
'''

    def test_glass_bio_uses_real_corner_radius_instead_of_translucent_corner_raster(self):
        module = self.load_patch()
        result = module.patch_text(self.owner_fixture())
        self.assertIn(module.MARKER, result)
        self.assertIn("GhostBaseGlassStyle.isEnabled", result)
        self.assertIn("self.maskNode.image = nil", result)
        self.assertIn("self.cornerRadius = hasCorners ? 26.0 : 0.0", result)
        self.assertIn("self.layer.maskedCorners", result)
        self.assertIn("glass: true", result)

    def test_patch_is_idempotent(self):
        module = self.load_patch()
        once = module.patch_text(self.owner_fixture())
        self.assertEqual(once, module.patch_text(once))


if __name__ == "__main__":
    unittest.main()
