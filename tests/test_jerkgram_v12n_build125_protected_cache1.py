import importlib.util
from pathlib import Path
import unittest

REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts" / "apply_jerkgram_v12n_build125_protected_cache1.py"

class Build125ProtectedCacheTests(unittest.TestCase):
    def test_uses_completed_local_resource_before_network_fetch(self):
        spec = importlib.util.spec_from_file_location("build125_protected_cache", PATCH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result = module.patch_text(module.fixture())
        self.assertIn("BUILD125_PROTECTED_FORWARD_CACHE_FIRST1", result)
        self.assertIn("if cachedData.isComplete", result)
        self.assertLess(result.index("if cachedData.isComplete"), result.index("context.engine.resources.fetch"))

    def test_is_idempotent(self):
        spec = importlib.util.spec_from_file_location("build125_protected_cache", PATCH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        once = module.patch_text(module.fixture())
        self.assertEqual(once, module.patch_text(once))

if __name__ == "__main__":
    unittest.main()
