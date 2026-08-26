import importlib.util
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load(name):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name[:-3], path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Build117WiringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.installer = load("install_jerkgram_v12f_build117_probe_hook.py")

    def test_build117_layers_run_after_build116_and_before_bazel(self):
        probe = '''python3 ../../scripts/verify_jerkgram_v12e_build116_foundation1.py
# END MARK: GhostBase v1.1G unified recovery
"$BAZEL_BIN" build //Telegram:Telegram
'''
        patched = cls_patch = self.installer.patch_probe(probe)
        self.assertLess(cls_patch.index("verify_jerkgram_v12e_build116_foundation1.py"), cls_patch.index("apply_jerkgram_v12f_build117_profile_scope1.py"))
        self.assertLess(cls_patch.index("verify_jerkgram_v12f_build117_release_readiness1.py"), cls_patch.index('"$BAZEL_BIN" build'))

    def test_active_workflows_publish_one_build117_artifact(self):
        workflows = sorted((ROOT / ".github/workflows").glob("build*.yml"))
        self.assertTrue(workflows)
        for path in workflows:
            text = path.read_text()
            match = re.search(r"Jerkgram 12\.9\.2 Build(\d+)", text)
            self.assertIsNotNone(match)
            current_build = int(match.group(1))
            self.assertGreaterEqual(current_build, 117)
            self.assertIn("jerkgram_publish_build117_artifact.py", text)
            self.assertIn(f"name: Jerkgram-build{current_build}", text)
            self.assertEqual(text.count("uses: actions/upload-artifact@v4"), 1)
            self.assertNotIn("Jerkgram-build117-output", text)

    def test_release_verifier_protects_foundations_and_packaging(self):
        text = (ROOT / "scripts/verify_jerkgram_v12f_build117_release_readiness1.py").read_text()
        for token in (
            "BUILD116_SETTINGS_FOUNDATION1",
            "BUILD116_ARCHIVE_FOUNDATION1",
            "Settings schemaVersion",
            "Archive schemaVersion",
            're.findall(r"Jerkgram-build(\\d+)"',
            "max(artifact_builds) >= 118",
            "Whitegram",
            "exactly one success artifact",
        ):
            self.assertIn(token, text)

        workflows = sorted((ROOT / ".github/workflows").glob("build*.yml"))
        self.assertTrue(workflows)
        for path in workflows:
            workflow = path.read_text()
            self.assertIn("apply_jerkgram_v12f_build117_profile_localization1.py", workflow)
            self.assertIn("verify_jerkgram_v12f_build117_profile_localization1.py", workflow)

    def test_publisher_names_build117_and_keeps_byte_identity(self):
        text = (ROOT / "scripts/jerkgram_publish_build117_artifact.py").read_text()
        self.assertIn('OUTPUT_IPA = OUTPUT_DIR / "Jerkgram-build117.ipa"', text)
        self.assertIn('"Build=117\\n"', text)
        self.assertIn("sha256(source) == output_hash", text)


if __name__ == "__main__":
    unittest.main()
