import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("build125_auth_localization", ROOT / "scripts" / "apply_jerkgram_v12n_build125_auth_ghost_localization1.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class Build125AuthGhostLocalizationTests(unittest.TestCase):
    def test_replaces_both_login_labels_with_string_owner(self):
        owner = '''private func ghostBaseSafeLoginButtonTitle(_ enabled: Bool) -> String {\nreturn enabled ? "👻 Режим призрака: ВКЛ" : "👻 Режим призрака: ВЫКЛ"\n}\nlet info = NSAttributedString(string: "Включите до входа, чтобы оставаться невидимым с первой сессии.")\nself.ghostBaseSafeLoginNode = SolidRoundedButtonNode(title: ghostBaseSafeLoginButtonTitle(ghostBaseInitialSafeLoginEnabled))\nstrongSelf.ghostBaseSafeLoginNode.animateTitle(to: ghostBaseSafeLoginButtonTitle(strongSelf.ghostBaseSafeLoginEnabled))\nlet bot = NSAttributedString(string: "Войти как бот")\nself.ghostBaseBotLoginNode.accessibilityLabel = "Войти как бот"\n'''
        patched = MODULE.patch_phone(owner)
        self.assertIn('strings.jerkgram.authGhostModeStatus(enabled: enabled)', patched)
        self.assertIn('strings.jerkgram.authGhostModeHint', patched)
        self.assertIn('ghostBaseSafeLoginButtonTitle(_ enabled: Bool, strings: PresentationStrings)', patched)
        self.assertIn('ghostBaseSafeLoginButtonTitle(ghostBaseInitialSafeLoginEnabled, strings: strings)', patched)
        self.assertIn('ghostBaseSafeLoginButtonTitle(strongSelf.ghostBaseSafeLoginEnabled, strings: strongSelf.strings)', patched)
        self.assertIn('strings.jerkgram.botLoginButton', patched)
        self.assertIn('strings.jerkgram.botLoginAccessibility', patched)
        self.assertIn(MODULE.BOT_MARKER, patched)
        self.assertNotIn("Locale.current", patched)
        self.assertIn(MODULE.MARKER, patched)

    def test_adds_russian_and_english_string_contract(self):
        strings = "public struct JerkgramStrings { public let languageCode: String }\n"
        patched = MODULE.patch_strings(strings)
        self.assertIn('self.languageCode == "ru"', patched)
        self.assertIn("Ghost Mode: ON", patched)
        self.assertIn("Режим призрака: ВКЛ", patched)
        self.assertIn('var botLoginButton: String', patched)
        self.assertIn('var botLoginAccessibility: String', patched)

    def test_rejects_owner_without_both_controls(self):
        with self.assertRaisesRegex(RuntimeError, "expected Ghost Mode title and hint owners"):
            MODULE.patch_phone('return enabled ? "👻 Ghost Mode: ON" : "👻 Ghost Mode: OFF"')


if __name__ == "__main__":
    unittest.main()
