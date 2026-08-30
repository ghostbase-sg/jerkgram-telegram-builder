from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[1]


class Build126ReleaseContractTests(unittest.TestCase):
    def test_build126_finalization_verifies_identity_and_exact_keychain_payload(self):
        finalizer = REPO / "scripts" / "jerkgram_finalize_build126_identity.py"
        verifier = REPO / "scripts" / "verify_jerkgram_v12o_build126_final_ipa.py"
        publisher = REPO / "scripts" / "jerkgram_publish_build126_artifact.py"
        for path in (finalizer, verifier, publisher):
            self.assertTrue(path.is_file(), f"missing Build126 release owner: {path.name}")
        self.assertIn('base.BUILD = "126"', finalizer.read_text(encoding="utf-8"))
        verifier_text = verifier.read_text(encoding="utf-8")
        self.assertIn('base.EXPECTED_BUILD = "126"', verifier_text)
        self.assertIn("sideloadKeychainFix.dylib", verifier_text)
        self.assertIn("EXPECTED_SHA256", verifier_text)
        publisher_text = publisher.read_text(encoding="utf-8")
        self.assertIn("Jerkgram-Build126-canary.ipa", publisher_text)

    def test_workflow_moves_only_current_canary_to_build126(self):
        workflow = (REPO / ".github/workflows/build.yml").read_text(encoding="utf-8")
        self.assertIn("Jerkgram 12.9.2 Build126 Canary", workflow)
        self.assertIn("jerkgram_finalize_build126_identity.py", workflow)
        self.assertIn("verify_jerkgram_v12o_build126_final_ipa.py", workflow)
        self.assertIn("jerkgram_publish_build126_artifact.py", workflow)
        self.assertIn("Jerkgram-Build126-canary", workflow)


if __name__ == "__main__":
    unittest.main()
