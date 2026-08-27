from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[1]
FINAL_VERIFY = REPO / "scripts" / "verify_jerkgram_v12m_build124_final_ipa.py"


class Build124FinalIpaWiringTests(unittest.TestCase):
    def test_final_verifier_runs_private_api_ipa_gate_before_identity_gate(self):
        source = FINAL_VERIFY.read_text(encoding="utf-8")
        self.assertIn("verify_jerkgram_build124_telegram_api_ipa1", source)
        self.assertIn("JERKGRAM_TELEGRAM_API_HASH", source)
        self.assertIn("verify_ipa_credentials", source)
        self.assertLess(source.index("verify_ipa_credentials"), source.index("base.main()"))

    def test_final_verifier_keeps_build124_identity_gate(self):
        source = FINAL_VERIFY.read_text(encoding="utf-8")
        self.assertIn('base.EXPECTED_BUILD = "124"', source)
        self.assertIn("base.main()", source)


if __name__ == "__main__":
    unittest.main()
