from pathlib import Path
import unittest

REPO = Path(__file__).resolve().parents[1]

class Build118AboutCardsTests(unittest.TestCase):
    def test_two_live_cards_and_build_label(self):
        text = (REPO / "scripts/apply_jerkgram_v12g_build118_about_cards1.py").read_text()
        self.assertIn('username: "JerkgramApp"', text)
        self.assertIn('username: "JerkgramCommunity"', text)
        self.assertIn("height: .peerList", text)
        self.assertIn("Build: 118", text)
        self.assertIn("aboutCommunitySignal", text)

if __name__ == "__main__": unittest.main()
