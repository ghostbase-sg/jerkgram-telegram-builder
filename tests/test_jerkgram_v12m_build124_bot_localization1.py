import importlib.util
from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts" / "apply_jerkgram_v12m_build124_bot_localization1.py"


class Build124BotLocalizationTests(unittest.TestCase):
    def load_patch(self):
        spec = importlib.util.spec_from_file_location("build124_bot_localization", PATCH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_strings_extension_is_bilingual_and_brand_clean(self):
        module = self.load_patch()
        source = "public struct JerkgramStrings { public let languageCode: String }\n"
        result = module.patch_strings(source)
        self.assertIn("BUILD124_BOT_LOCALIZATION1", result)
        self.assertIn("public extension JerkgramStrings", result)
        self.assertIn("var botLoginButton", result)
        self.assertIn("Log in as Bot — Experimental", result)
        self.assertIn("Войти как бот — Экспериментально", result)
        self.assertIn("var botAlreadyAdded", result)
        self.assertIn("already added to Jerkgram", result)
        self.assertNotIn("added to GhostBase", result)

    def test_auth_ui_uses_selected_presentation_language(self):
        module = self.load_patch()
        files = {
            "passwordNode": 'mode == .ghostBaseBotToken ? "Вход как бот" : strings.LoginPassword_Title\nmode == .ghostBaseBotToken ? "Введите токен, выданный BotFather. Токен не сохраняется." : strings.TwoStepAuth_EnterPasswordHelp\nself.mode == .ghostBaseBotToken ? "Вход как бот" : self.strings.LoginPassword_Title\n',
            "phoneNode": 'NSAttributedString(string: "Войти как бот — Экспериментально", font: Font.regular(16.0))\nself.ghostBaseBotLoginNode.accessibilityLabel = "Войти как бот"\n',
            "controller": 'text = "Токен бота недействителен."\ntext = "Telegram отклонил API ID клиента."\ntext = "Этот бот уже добавлен в GhostBase."\ntitle: "Вход как бот",\n',
            "actions": 'title: "Выйти из аккаунта бота?",\ntext: "Аккаунт будет удалён только из GhostBase. Сам бот и его токен в BotFather не удаляются.",\ntitle: "Выйти",\n',
        }
        result = module.patch_auth_sources(files)
        joined = "\n".join(result.values())
        self.assertIn("strings.jerkgram.botLoginTitle", joined)
        self.assertIn("self.strings.jerkgram.botLoginTitle", joined)
        self.assertIn("strings.jerkgram.botLoginButton", joined)
        self.assertIn("self.presentationData.strings.jerkgram.botInvalidToken", joined)
        self.assertIn("self.presentationData.strings.jerkgram.botAlreadyAdded", joined)
        self.assertIn("self.presentationData.strings.jerkgram.botLogoutTitle", joined)
        self.assertNotIn('"Вход как бот"', joined)
        self.assertNotIn("GhostBase. Сам бот", joined)

    def test_debug_bot_surfaces_use_jerkgram_strings(self):
        module = self.load_patch()
        source = '''private func ghostBaseBotCapabilityReport() -> String {\n    let report = defaults.string(forKey: "Report") ?? "Результатов пока нет."\n    return """\n    Status: \\(status)\n    Updated: \\(updated)\n\n    \\(report)\n    """\n}\nprivate func ghostBaseBotDifferenceReport() -> String {\n    let report = defaults.string(forKey: "Report") ?? "Результатов пока нет."\n    return """\n    Status: \\(status)\n    Updated: \\(updated)\n\n    \\(report)\n    """\n}\n"Bot Account Capability Probe"\n"Проверить RPC bot-аккаунта"\nghostBaseBotCapabilityReport()\n"Проверить updates.getDifference"\nghostBaseBotDifferenceReport()\n'''
        result = module.patch_settings(source)
        self.assertIn("ghostBaseBotCapabilityReport(strings: PresentationStrings)", result)
        self.assertIn("ghostBaseBotDifferenceReport(strings: PresentationStrings)", result)
        self.assertIn("strings.jerkgram.botNoResults", result)
        self.assertIn("strings.jerkgram.botDiagnosticReport", result)
        self.assertIn("strings.jerkgram.botCapabilityTitle", result)
        self.assertIn("strings.jerkgram.botCapabilityAction", result)
        self.assertIn("strings.jerkgram.botDifferenceAction", result)
        self.assertIn("ghostBaseBotCapabilityReport(strings: strings)", result)
        self.assertIn("ghostBaseBotDifferenceReport(strings: strings)", result)

    def test_missing_legacy_diagnostics_do_not_block_token_localization(self):
        module = self.load_patch()
        source = '''private func ghostBaseBotCapabilityReport(strings: PresentationStrings) -> String {
    return strings.researchBotCapability
}
private func ghostBaseBotDifferenceReport(strings: PresentationStrings) -> String {
    return strings.researchBotDifference
}
'''
        self.assertEqual(module.patch_settings(source), source)
        self.assertFalse(module.has_legacy_bot_diagnostics(source))

    def test_patch_is_idempotent(self):
        module = self.load_patch()
        source = "public struct JerkgramStrings { public let languageCode: String }\n"
        once = module.patch_strings(source)
        twice = module.patch_strings(once)
        self.assertEqual(once, twice)
        self.assertEqual(once.count("BUILD124_BOT_LOCALIZATION1"), 1)


if __name__ == "__main__":
    unittest.main()
