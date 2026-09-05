from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[1]


class Build126ReleaseContractTests(unittest.TestCase):
    def test_build128_finalization_verifies_identity_and_exact_keychain_payload(self):
        finalizer = REPO / "scripts" / "jerkgram_finalize_build128_identity.py"
        verifier = REPO / "scripts" / "verify_jerkgram_v12s_build128_final_ipa.py"
        publisher = REPO / "scripts" / "jerkgram_publish_build128_artifact.py"
        for path in (finalizer, verifier, publisher):
            self.assertTrue(path.is_file(), f"missing Build126 release owner: {path.name}")

        build130_finalizer = (REPO / "scripts" / "jerkgram_finalize_build130_identity.py").read_text(encoding="utf-8")
        self.assertIn('base.base.BUILD = "130"', build130_finalizer)
        self.assertIn("import jerkgram_finalize_build132_esign_ready as build132", build130_finalizer)
        self.assertIn("build132.main()", build130_finalizer)

        build132_finalizer = (REPO / "scripts" / "jerkgram_finalize_build132_esign_ready.py").read_text(encoding="utf-8")
        self.assertIn('PROD_BASE = "com.jerkgram.ios"', build132_finalizer)
        self.assertIn('BUILD = "132"', build132_finalizer)
        self.assertIn('TELEGRAM_BASE_VERSION = "12.9.2"', build132_finalizer)

        build130_verifier = (REPO / "scripts" / "verify_jerkgram_v12s_build130_final_ipa.py").read_text(encoding="utf-8")
        self.assertIn('EXPECTED_BUILD = "132"', build130_verifier)
        self.assertIn('EXPECTED_DISPLAY_VERSION = "12.9.2"', build130_verifier)
        self.assertIn("base.base.EXPECTED_BUILD = EXPECTED_BUILD", build130_verifier)
        self.assertIn("base.base.EXPECTED_BUNDLE = bundle_base", build130_verifier)

        publisher130_text = (REPO / "scripts" / "jerkgram_publish_build130_artifact.py").read_text(encoding="utf-8")
        self.assertIn('base.EXPECTED_BUILD = "132"', publisher130_text)
        self.assertIn('.replace("Build=122", "Build=132")', publisher130_text)

        verifier_text = verifier.read_text(encoding="utf-8")
        self.assertIn("sideloadKeychainFix.dylib", verifier_text)
        self.assertIn("file_picker.FILE_PICKER_NAME", verifier_text)
        publisher_text = publisher.read_text(encoding="utf-8")
        self.assertIn("Jerkgram-Build130.ipa", publisher130_text)

    def test_workflow_publishes_only_current_build128_artifact(self):
        workflow = (REPO / ".github/workflows/build.yml").read_text(encoding="utf-8")
        self.assertIn("Jerkgram 12.9.2 Build130", workflow)
        self.assertIn("jerkgram_finalize_build128_identity.py", workflow)
        self.assertIn("verify_jerkgram_v12s_build128_final_ipa.py", workflow)
        self.assertIn("jerkgram_publish_build130_artifact.py", workflow)
        self.assertIn("Jerkgram-Build130", workflow)


if __name__ == "__main__":
    unittest.main()
