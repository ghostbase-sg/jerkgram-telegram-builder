import importlib.util
from pathlib import Path
import unittest

REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts" / "apply_jerkgram_v12n_build125_links_bounds1.py"

class Build125LinksBoundsTests(unittest.TestCase):
    def test_links_material_can_not_cover_the_full_list_view(self):
        spec = importlib.util.spec_from_file_location("build125_links", PATCH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        source = '''// MARK: Jerkgram v1.2M BUILD124_LINKS_INTRINSIC_MATERIAL1
let linksFrame = CGRect(
 height: max(1.0, self.listNode.bounds.size.height - distanceToTop - self.listNode.insets.bottom)
)
'''
        result = module.patch_text(source)
        self.assertIn("BUILD125_LINKS_LOCAL_CARD_BOUNDS1", result)
        self.assertIn("BUILD125_LINKS_REMOVE_VIEWPORT_CARD2", result)
        self.assertIn("height: 1.0", result)
        self.assertNotIn("min(300.0", result)
        self.assertNotIn("height: max(1.0, self.listNode.bounds.size.height", result)

    def test_patch_is_idempotent(self):
        spec = importlib.util.spec_from_file_location("build125_links", PATCH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        source = '''// MARK: Jerkgram v1.2M BUILD124_LINKS_INTRINSIC_MATERIAL1
height: max(1.0, self.listNode.bounds.size.height - distanceToTop - self.listNode.insets.bottom)
'''
        self.assertEqual(module.patch_text(source), module.patch_text(module.patch_text(source)))

if __name__ == "__main__":
    unittest.main()
