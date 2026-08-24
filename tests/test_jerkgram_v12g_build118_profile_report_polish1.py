from pathlib import Path
import unittest

REPO = Path(__file__).resolve().parents[1]

class Build118ProfileReportPolishTests(unittest.TestCase):
    def test_semantic_status_and_bilingual_labels(self):
        text = (REPO / "scripts/apply_jerkgram_v12g_build118_profile_report_polish1.py").read_text()
        self.assertIn("emojiStatusValue", text)
        self.assertIn("fileId: ", text)
        self.assertIn("Эмодзи-статус", text)
        self.assertIn("Emoji status:", text)
        self.assertNotIn('return raw', text)

if __name__ == "__main__": unittest.main()
