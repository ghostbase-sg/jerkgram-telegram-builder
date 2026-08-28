from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[1]
APPLY = REPO / "scripts/apply_jerkgram_v12k_build122_edit_caption_history1.py"
VERIFY = REPO / "scripts/verify_jerkgram_v12k_build122_edit_caption_history1.py"
INSTALL = REPO / "scripts/install_jerkgram_v12k_build122_probe_hook.py"
WORKFLOW = REPO / ".github/workflows/build.yml"


class Build122EditCaptionHistoryTests(unittest.TestCase):
    def test_empty_to_caption_edit_is_not_discarded(self) -> None:
        source = APPLY.read_text(encoding="utf-8")
        verifier = VERIFY.read_text(encoding="utf-8")
        self.assertIn("BUILD122_EDIT_CAPTION_HISTORY1", source)
        self.assertIn("previousMessage.text != message.text", source)
        self.assertIn("previousText: previousMessage.text", verifier)
        self.assertIn("previousVersionDate", source)

    def test_history_view_includes_current_caption_once(self) -> None:
        source = APPLY.read_text(encoding="utf-8")
        self.assertIn("BUILD122_EDIT_HISTORY_CURRENT1", source)
        self.assertIn("result.last?.text != message.text", source)
        self.assertIn("timestamp: Double(message.timestamp)", source)

    def test_overlay_and_verifier_are_wired(self) -> None:
        install = INSTALL.read_text(encoding="utf-8")
        workflow = WORKFLOW.read_text(encoding="utf-8")
        for name in (
            "apply_jerkgram_v12k_build122_edit_caption_history1.py",
            "verify_jerkgram_v12k_build122_edit_caption_history1.py",
        ):
            self.assertIn(name, install)
        self.assertIn("install_jerkgram_v12k_build122_probe_hook.py", workflow)
        self.assertIn("python3 -m unittest tests.test_jerkgram_v12k_build122_edit_caption_history1", workflow)
        self.assertTrue(VERIFY.is_file())


if __name__ == "__main__":
    unittest.main()
