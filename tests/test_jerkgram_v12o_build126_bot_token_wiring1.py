from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[1]
PROBE = REPO / "scripts" / "bazel_build_probe_official.sh"


class Build126BotTokenWiringTests(unittest.TestCase):
    def test_selected_language_overlay_runs_after_build125_creates_bot_login_owner(self):
        text = PROBE.read_text(encoding="utf-8")

        bot_apply = "apply_jerkgram_v12m_build124_bot_localization1.py"
        bot_verify = "verify_jerkgram_v12m_build124_bot_localization1.py"
        build125_apply = "apply_jerkgram_v12n_build125_auth_ghost_localization1.py"

        self.assertIn(bot_apply, text)
        self.assertIn(bot_verify, text)
        self.assertLess(text.index(build125_apply), text.index(bot_apply))
        self.assertLess(text.index(build125_apply), text.index(bot_verify))

    def test_build126_owner_overlays_run_after_build125_and_before_bazel(self):
        text = PROBE.read_text(encoding="utf-8")
        bazel = text.index('"$BAZEL_BIN" build')
        build125 = text.index("apply_jerkgram_v12n_build125_auth_ghost_localization1.py")
        owners = (
            "apply_jerkgram_v12o_build126_bio_corner_mask1.py",
            "apply_jerkgram_v12o_build126_voice_viewed_state1.py",
            "apply_jerkgram_v12o_build126_circle_viewed_state1.py",
            "apply_jerkgram_v12o_build126_forward_menu_owner1.py",
        )
        for owner in owners:
            self.assertIn(owner, text)
            self.assertLess(build125, text.index(owner))
            self.assertLess(text.index(owner), bazel)


if __name__ == "__main__":
    unittest.main()
