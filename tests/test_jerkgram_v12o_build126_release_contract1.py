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
        self.assertIn('base.BUILD = "128"', finalizer.read_text(encoding="utf-8"))
        verifier_text = verifier.read_text(encoding="utf-8")
        self.assertIn('base.EXPECTED_BUILD = "128"', verifier_text)
        self.assertIn("sideloadKeychainFix.dylib", verifier_text)
        self.assertIn("file_picker.FILE_PICKER_NAME", verifier_text)
        publisher_text = publisher.read_text(encoding="utf-8")
        self.assertIn("Jerkgram-Build128.ipa", publisher_text)

    def test_workflow_publishes_only_current_build128_artifact(self):
        workflow = (REPO / ".github/workflows/build.yml").read_text(encoding="utf-8")
        self.assertIn("Jerkgram 12.9.2 Build128", workflow)
        self.assertIn("jerkgram_finalize_build128_identity.py", workflow)
        self.assertIn("verify_jerkgram_v12s_build128_final_ipa.py", workflow)
        self.assertIn("jerkgram_publish_build128_artifact.py", workflow)
        self.assertIn("Jerkgram-Build128", workflow)


if __name__ == "__main__":
    unittest.main()
