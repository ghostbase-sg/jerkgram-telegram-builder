import importlib.util
from pathlib import Path
import re
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    path = REPO_ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Build116WiringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.installer = load_script("install_jerkgram_v12e_build116_probe_hook.py")

    def test_probe_order_is_build115_then_three_build116_layers_then_bazel(self):
        probe = '''
python3 ../../scripts/apply_jerkgram_v12d_build115_numeric_links1.py
python3 ../../scripts/verify_jerkgram_v12d_build115_numeric_links1.py
# END MARK: GhostBase v1.1G unified recovery
"$BAZEL_BIN" build //Telegram:Telegram
'''
        patched = self.installer.patch_probe(probe)
        names = self.installer.ORDERED_SCRIPTS
        for name in names:
            self.assertEqual(patched.count(name), 1)
        positions = [patched.index("verify_jerkgram_v12d_build115_numeric_links1.py")]
        positions += [patched.index(name) for name in names]
        positions.append(patched.index('"$BAZEL_BIN" build'))
        self.assertEqual(positions, sorted(positions))

    def test_active_workflows_retain_build116_layer_under_build117(self):
        workflows = sorted((REPO_ROOT / ".github/workflows").glob("build*.yml"))
        self.assertTrue(workflows)
        for path in workflows:
            text = path.read_text(encoding="utf-8")
            match = re.search(r"Jerkgram 12\.9\.2 Build(\d+)", text)
            self.assertIsNotNone(match)
            self.assertGreaterEqual(int(match.group(1)), 117)
            for name in self.installer.ORDERED_SCRIPTS:
                self.assertIn(name, text)
            self.assertNotIn("jerkgram_publish_build116_artifact.py", text)

    def test_publisher_uses_build116_outputs(self):
        text = (REPO_ROOT / "scripts/jerkgram_publish_build116_artifact.py").read_text(encoding="utf-8")
        self.assertIn('OUTPUT_IPA = OUTPUT_DIR / "Jerkgram-build116.ipa"', text)
        self.assertIn('"Build=116\\n"', text)


if __name__ == "__main__":
    unittest.main()
