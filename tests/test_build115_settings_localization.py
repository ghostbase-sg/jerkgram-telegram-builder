import importlib.util
from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    path = REPO_ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Build115SettingsLocalizationTests(unittest.TestCase):
    def test_final_materialized_settings_literals_localize_without_cyrillic(self):
        localizer = load_script(
            "apply_jerkgram_v12d_build115_settings_localization1.py"
        )
        settings = r'''
// MARK: JerkGram v1.1Y BUILD110_SHORT_TOGGLE_TITLES1
private enum GhostBaseSettingsPage: Equatable {
    case root

    var title: String {
        return "GhostBase"
    }
}

private final class GhostBaseSettingsArguments {}

private func ghostBaseSettingsEntries(
    state: GhostBaseSettingsState,
    context: AccountContext,
    page: GhostBaseSettingsPage
) -> [GhostBaseSettingsEntry] {
    let presenceSummary = defaults.string(forKey: key) ?? "История присутствия пока пуста"
    let knownUsersSummary = defaults.string(forKey: key) ?? "Известные пользователи: нет данных"
    return [
        .toggle(0, 0, key, "Сохранять удалённые", true),
        .header(1, "Отправка текста"),
        .selector(1, 0, "Стиль отправки", style),
        .info(1, "Стиль применяется после нажатия кнопки отправки."),
        .header(2, "Удалённые ответы"),
        .toggle(2, 0, key, "Переносимый ответ", true),
        .toggle(2, 1, key, "Сохранять удалённые медиа", true),
        .info(2, "Ответ материализуется только после Send. Медиа хранится только во внутреннем кэше GhostBase: до 1 ГБ, 30 дней; если bytes недоступны, используется текстовый fallback."),
        .header(3, "Фон профиля"),
        .toggle(3, 0, key, "Эффект фона профиля", true),
        .toggle(3, 1, key, "Размытие аватара в профиле", true),
        .toggle(3, 2, key, "Цветовой tint", true),
        .toggle(3, 3, key, "Облегчённое размытие", true),
        .info(3, "При выключенном главном тумблере профиль полностью использует штатный интерфейс Telegram."),
        .header(4, "Интерфейс"),
        .toggle(4, 0, key, "Секунды в сообщениях", true),
        .toggle(4, 1, key, "Скрывать мой номер", true),
        .toggle(4, 2, key, "Показывать RAM под часами", true),
        .info(4, "Номер скрывается только локально в интерфейсе GhostBase."),
        .info(5, presenceSummary),
        .info(5, knownUsersSummary),
        .header(5, "Последние события"),
        .info(5, runtimeText.isEmpty ? "Событий пока нет" : runtimeText),
        .info(5, "Буфер ограничен 200 строками. Сбор не запускается при открытии этой страницы.")
    ]
}

let controller = ItemListController(
    entries: ghostBaseSettingsEntries(
        state: state,
        context: context,
        page: page
    ),
    title: .text(page.title),
)
'''

        patched = localizer.patch_settings(settings)
        entries = localizer.block_bounds(
            patched,
            "private func ghostBaseSettingsEntries("
        )
        entries_text = patched[entries[0]:entries[2]]

        expected_tokens = (
            "strings.saveDeletedMessages",
            "strings.textSending",
            "strings.sendStyle",
            "strings.sendStyleHint",
            "strings.deletedReplies",
            "strings.portableReply",
            "strings.saveDeletedMedia",
            "strings.portableReplyHint",
            "strings.profileBackground",
            "strings.profileBackgroundEffect",
            "strings.blurProfileAvatar",
            "strings.colorTint",
            "strings.reducedBlur",
            "strings.profileEffectDisabledHint",
            "strings.interface",
            "strings.messageSeconds",
            "strings.hideMyPhone",
            "strings.showRamUnderClock",
            "strings.hidePhoneHint",
            "strings.presenceHistoryEmpty",
            "strings.knownUsersNoData",
            "strings.recentEvents",
            "strings.eventsEmpty",
            "strings.diagnosticsBufferHint",
        )
        for token in expected_tokens:
            self.assertIn(token, entries_text)
        self.assertEqual(localizer.cyrillic_string_literals(entries_text), [])

    def test_localization_foundation_defines_final_settings_catalog(self):
        foundation = load_script(
            "apply_jerkgram_v12d_build115_localization1.py"
        )

        expected_catalog = {
            "saveDeletedMessages": (
                "Save Deleted",
                "Сохранять удалённые",
            ),
            "textSending": ("Text Sending", "Отправка текста"),
            "sendStyle": ("Send Style", "Стиль отправки"),
            "sendStyleHint": (
                "The style is applied after tapping the send button.",
                "Стиль применяется после нажатия кнопки отправки.",
            ),
            "deletedReplies": ("Deleted Replies", "Удалённые ответы"),
            "portableReply": ("Portable Reply", "Переносимый ответ"),
            "saveDeletedMedia": (
                "Save Deleted Media",
                "Сохранять удалённые медиа",
            ),
            "portableReplyHint": (
                "The reply is materialized only after Send. Media is kept only in Jerkgram's internal cache: up to 1 GB for 30 days; if bytes are unavailable, a text fallback is used.",
                "Ответ материализуется только после Send. Медиа хранится только во внутреннем кэше Jerkgram: до 1 ГБ, 30 дней; если bytes недоступны, используется текстовый fallback.",
            ),
            "profileBackground": ("Profile Background", "Фон профиля"),
            "profileBackgroundEffect": (
                "Profile Background Effect",
                "Эффект фона профиля",
            ),
            "blurProfileAvatar": (
                "Blur Profile Avatar",
                "Размывать аватар в профиле",
            ),
            "colorTint": ("Color Tint", "Цветовой оттенок"),
            "reducedBlur": ("Reduced Blur", "Облегчённое размытие"),
            "profileEffectDisabledHint": (
                "When the main effect is disabled, Jerkgram creates no additional profile views, observers, or image/palette pipeline. New values apply the next time the profile opens.",
                "Когда главный эффект выключен, Jerkgram не создаёт дополнительные profile views, observers или image/palette pipeline. Новые значения применяются при следующем открытии профиля.",
            ),
            "other": ("Other", "Прочее"),
            "interface": ("Interface", "Интерфейс"),
            "messageSeconds": ("Message Seconds", "Секунды в сообщениях"),
            "hideMyPhone": ("Hide My Phone Number", "Скрывать мой номер"),
            "showRamUnderClock": (
                "Show RAM Under Clock",
                "Показывать RAM под часами",
            ),
            "hidePhoneHint": (
                "Your phone number is hidden only locally in Jerkgram. Profile editing and number changing remain available.",
                "Номер скрывается только локально в интерфейсе Jerkgram. Экран изменения профиля и смены номера остаётся доступен.",
            ),
            "presenceHistoryEmpty": (
                "Presence history is empty",
                "История присутствия пока пуста",
            ),
            "knownUsersNoData": (
                "Known users: no data",
                "Известные пользователи: нет данных",
            ),
            "recentEvents": ("Recent Events", "Последние события"),
            "eventsEmpty": ("No events yet", "Событий пока нет"),
            "diagnosticsBufferHint": (
                "The buffer is limited to 200 lines. Collection does not start when this page opens.",
                "Буфер ограничен 200 строками. Сбор не запускается при открытии этой страницы.",
            ),
        }

        for key, (english, russian) in expected_catalog.items():
            self.assertIn(f"case {key}", foundation.SWIFT)
            self.assertIn(
                f"public var {key}: String {{ self.text(.{key}) }}",
                foundation.SWIFT,
            )
            self.assertIn(f'.{key}: "{english}"', foundation.SWIFT)
            self.assertIn(f'.{key}: "{russian}"', foundation.SWIFT)


if __name__ == "__main__":
    unittest.main()
