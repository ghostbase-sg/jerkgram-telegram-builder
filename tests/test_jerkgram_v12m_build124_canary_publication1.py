from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[1]
PUBLISH = REPO / "scripts" / "jerkgram_publish_build124_artifact.py"
WORKFLOW = REPO / ".github" / "workflows" / "build.yml"


class Build124CanaryPublicationTests(unittest.TestCase):
    def test_publisher_uses_visible_canary_names_and_info_label(self):
        source = PUBLISH.read_text(encoding="utf-8")
        self.assertIn('Jerkgram-Build124-canary.ipa', source)
        self.assertIn('Jerkgram-Build124-canary-info.txt', source)
        self.assertIn('Build=124-canary', source)
        self.assertNotIn('Path("artifacts/Jerkgram-build124.ipa")', source)

    def test_workflow_uploads_private_actions_canary_artifact_only(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('name: Jerkgram 12.9.2 Build124 Canary', source)
        self.assertIn('name: Jerkgram-Build124-canary', source)
        self.assertIn('artifacts/Jerkgram-Build124-canary.ipa', source)
        self.assertIn('artifacts/Jerkgram-Build124-canary-info.txt', source)
        for forbidden in ('actions/create-release', 'softprops/action-gh-release', 'gh release create', 'releases/create'):
            self.assertNotIn(forbidden, source)

    def test_new_api_ipa_gates_are_part_of_ci(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('scripts/verify_jerkgram_build124_telegram_api_ipa1.py', source)
        self.assertIn('tests.test_jerkgram_build124_telegram_api_source_owner1', source)
        self.assertIn('tests.test_jerkgram_v12m_build124_final_ipa_credentials1', source)
        self.assertIn('tests.test_jerkgram_v12m_build124_final_ipa_wiring1', source)
        self.assertIn('tests.test_jerkgram_v12m_build124_canary_publication1', source)


if __name__ == "__main__":
    unittest.main()
