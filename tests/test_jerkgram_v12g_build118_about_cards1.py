from pathlib import Path
import importlib.util
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

    def test_build_footer_uses_swift_newline_escapes_not_literal_backslashes(self):
        path = REPO / "scripts/apply_jerkgram_v12g_build118_about_cards1.py"
        spec = importlib.util.spec_from_file_location("about_cards", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(
            module.ABOUT_BUILD_FOOTER_SWIFT,
            r"Jerkgram\nBase: Official Telegram 12.9.2\nBuild: 118",
        )
        self.assertNotIn(r"\\n", module.ABOUT_BUILD_FOOTER_SWIFT)

if __name__ == "__main__": unittest.main()
