import importlib.util
from pathlib import Path
import unittest

REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts" / "apply_jerkgram_v12n_build125_circle_viewed1.py"

class Build125CircleViewedTests(unittest.TestCase):
    def load_patch(self):
        spec = importlib.util.spec_from_file_location("build125_circle", PATCH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_adds_distinct_outgoing_viewed_check(self):
        module = self.load_patch()
        duration = module.patch_duration_text(module.duration_fixture())
        instant = module.patch_instant_text(module.instant_fixture())
        self.assertIn("BUILD125_CIRCLE_VIEWED_CHECK1", duration)
        self.assertIn("public var showsViewedCheck", duration)
        self.assertIn("showsViewedCheck: self.showsViewedCheck", duration)
        self.assertIn("else if parameters.showsViewedCheck", duration)
        self.assertIn("durationNode.showsViewedCheck = jerkgramOutgoingOneTimeCircleViewed", instant)

    def test_is_idempotent(self):
        module = self.load_patch()
        duration = module.patch_duration_text(module.duration_fixture())
        instant = module.patch_instant_text(module.instant_fixture())
        self.assertEqual(duration, module.patch_duration_text(duration))
        self.assertEqual(instant, module.patch_instant_text(instant))

if __name__ == "__main__":
    unittest.main()
