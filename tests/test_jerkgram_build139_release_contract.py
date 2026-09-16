import importlib.util
from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[1]


def load(path: Path, name: str):
    if not path.is_file():
        raise AssertionError(f"missing Build139 release component: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class Build139ReleaseContract(unittest.TestCase):
    def test_canonical_source_order_materializes_notification_foundation_before_bazel(self):
        hook = load(REPO / "scripts/install_jerkgram_v12w_build133_probe_hook.py", "build139_hook")
        ordered = (
            "apply_jerkgram_v13a_build139_notifications_foundation1.py",
            "verify_jerkgram_v13a_build139_notifications_foundation1.py",
            "apply_jerkgram_v13b_build139_notifications_settings1.py",
            "verify_jerkgram_v13b_build139_notifications_settings1.py",
            "apply_jerkgram_v13c_build139_release_identity1.py",
            "verify_jerkgram_v13c_build139_release_identity1.py",
        )
        for name in ordered:
            self.assertIn(name, hook.SOURCE_ORDERED)
        positions = [hook.SOURCE_ORDERED.index(name) for name in ordered]
        self.assertEqual(positions, sorted(positions))

    def test_final_identity_is_build139_without_changing_telegram_version_or_bundle(self):
        finalizer = load(REPO / "scripts/jerkgram_finalize_build139_identity.py", "build139_finalizer")
        verifier = load(REPO / "scripts/verify_jerkgram_build139_final_ipa.py", "build139_verifier")

        self.assertEqual(finalizer.BUILD, "139")
        self.assertEqual(finalizer.PUBLIC_BUNDLE, "com.jerkgram.ios")
        self.assertEqual(finalizer.TELEGRAM_VERSION, "12.9.2")
        self.assertEqual(finalizer.JERKGRAM_DISPLAY_VERSION, "1.0.2")
        self.assertEqual(finalizer.JERKGRAM_TECHNICAL_VERSION, "1.0.2")
        self.assertEqual(verifier.EXPECTED_BUILD, "139")
        self.assertEqual(verifier.EXPECTED_BUNDLE, "com.jerkgram.ios")
        self.assertEqual(verifier.EXPECTED_TELEGRAM_VERSION, "12.9.2")

        hook = load(REPO / "scripts/install_jerkgram_v12w_build133_probe_hook.py", "build139_hook_final")
        self.assertEqual(
            hook.FINAL_ORDERED,
            ("jerkgram_finalize_build139_identity.py", "verify_jerkgram_build139_final_ipa.py"),
        )

    def test_materialized_release_identity_reports_build139_to_about_and_telemetry(self):
        patcher = load(REPO / "scripts/apply_jerkgram_v13c_build139_release_identity1.py", "build139_release_patch")
        fixture = '''public enum JerkgramReleaseIdentity {\n    public static let displayVersion = "1.0.2"\n    public static let technicalVersion = "1.0.2"\n    public static let build = "138"\n    public static let telegramBase = "12.9.2"\n}\n'''
        patched = patcher.patch_strings_text(fixture)
        self.assertIn('public static let build = "139"', patched)
        self.assertNotIn('public static let build = "138"', patched)
        self.assertIn('public static let telegramBase = "12.9.2"', patched)
        self.assertIn('public static let displayVersion = "1.0.2"', patched)

    def test_workflow_builds_and_publishes_build139_ipa_on_development_branch(self):
        workflow = (REPO / ".github/workflows/build.yml").read_text(encoding="utf-8")
        for token in (
            "name: Jerkgram 12.9.2 Build139",
            "dev/build139-notifications-foundation",
            "tests.test_jerkgram_build139_release_contract",
            "scripts/jerkgram_publish_build139_artifact.py",
            "name: Jerkgram-Build139",
            "artifacts/Jerkgram-Build139.ipa",
        ):
            self.assertIn(token, workflow)

        publisher = load(REPO / "scripts/jerkgram_publish_build139_artifact.py", "build139_publisher")
        self.assertEqual(publisher.base.EXPECTED_BUILD, "139")
        self.assertEqual(publisher.base.OUTPUT_IPA, Path("artifacts/Jerkgram-Build139.ipa"))


if __name__ == "__main__":
    unittest.main()
