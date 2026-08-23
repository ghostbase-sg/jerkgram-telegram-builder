#!/usr/bin/env python3

from pathlib import Path
import os
import re


ROOT = Path(
    os.environ.get(
        "JERKGRAM_SOURCE_ROOT",
        os.environ.get(
            "GHOSTBASE_SOURCE_ROOT",
            str(Path.cwd())
        )
    )
).resolve()

SETTINGS = (
    ROOT
    / "submodules/SettingsUI/Sources/GhostBase"
    / "GhostBaseSettingsController.swift"
)
MAIN_ITEMS = (
    ROOT
    / "submodules/TelegramUI/Components/PeerInfo"
    / "PeerInfoScreen/Sources/PeerInfoSettingsItems.swift"
)

MARKER = "// MARK: Jerkgram v1.2D BUILD115_SETTINGS_LOCALIZATION1"
MAIN_MARKER = "// MARK: Jerkgram v1.2D BUILD115_MAIN_SETTINGS_LOCALIZATION1"
OLD_MAIN_MARKER = "// MARK: GhostBase v1.0R Main Settings Group"


ENTRY_LITERALS = {
    # Root/page groups.
    "Основные функции": "strings.basicFunctions",
    "Basic Functions": "strings.basicFunctions",
    "Ghost Mode": "strings.ghostMode",
    "Сообщения": "strings.messages",
    "Messages": "strings.messages",
    "Защищённый контент": "strings.protectedContent",
    "Protected Content": "strings.protectedContent",
    "Медиа и истории": "strings.mediaAndStories",
    "Media & Stories": "strings.mediaAndStories",
    "Внешний вид": "strings.appearance",
    "Appearance": "strings.appearance",
    "Debug / Research": "strings.debugResearch",
    "О клиенте": "strings.about",
    "About": "strings.about",

    # Basic functions.
    "Карточка профиля": "strings.profileCard",
    "Profile Card": "strings.profileCard",
    "Показывать ID": "strings.showIds",
    "Show IDs": "strings.showIds",
    "Показывать DC": "strings.showDcs",
    "Show DCs": "strings.showDcs",
    "Дата регистрации": "strings.registrationDate",
    "Registration date": "strings.registrationDate",
    "Registration Date": "strings.registrationDate",
    "Локальный баланс Stars": "strings.localStarsBalance",
    "Local Stars Balance": "strings.localStarsBalance",
    "Баланс Stars": "strings.starsBalance",
    "Stars Balance": "strings.starsBalance",

    # Ghost Mode. Build110 deliberately shortened several English labels.
    "Не отмечать прочитанным": "strings.readGhost",
    "Read Ghost": "strings.readGhost",
    "Don't Mark as Read": "strings.readGhost",
    "Скрыть набор текста": "strings.typing",
    "Typing": "strings.typing",
    "Скрыть запись": "strings.recording",
    "Recording": "strings.recording",
    "Скрыть загрузку": "strings.uploading",
    "Uploading": "strings.uploading",
    "Скрыть выбор стикера": "strings.choosingSticker",
    "Choosing sticker": "strings.choosingSticker",
    "Choosing Sticker": "strings.choosingSticker",
    "Скрыть игровую активность": "strings.gameActivity",
    "Game activity": "strings.gameActivity",
    "Game Activity": "strings.gameActivity",
    "Скрыть выбор эмодзи": "strings.choosingEmoji",
    "Choosing emoji": "strings.choosingEmoji",
    "Choosing Emoji": "strings.choosingEmoji",
    "Скрыть онлайн": "strings.hideOnline",
    "Online Status": "strings.hideOnline",
    "Отложенная отправка": "strings.scheduledSend",
    "Scheduled send": "strings.scheduledSend",
    "Scheduled Send": "strings.scheduledSend",

    # Messages.
    "Удалённые сообщения": "strings.deletedMessages",
    "Deleted Messages": "strings.deletedMessages",
    "Сохранять удалённые сообщения": "strings.saveDeletedMessages",
    "Save Deleted Messages": "strings.saveDeletedMessages",
    "Сохранять удалённые": "strings.saveDeletedMessages",
    "Save Deleted": "strings.saveDeletedMessages",
    "Показывать удалённые сообщения": "strings.showDeletedMessages",
    "Show Deleted Messages": "strings.showDeletedMessages",
    "История изменений": "strings.editHistory",
    "Edit History": "strings.editHistory",
    "Сохранять историю изменений": "strings.saveEditHistory",
    "Save Edit History": "strings.saveEditHistory",
    "Показывать историю изменений": "strings.showEditHistory",
    "Show Edit History": "strings.showEditHistory",
    "Выключение функций не удаляет уже сохранённые данные.": "strings.savedDataHint",
    "Disabling these features does not remove already saved data.": "strings.savedDataHint",
    "История редактирования и сохранение удалённых сообщений доступны через меню сообщения.": "strings.savedDataHint",

    # Text send style and portable deleted replies are injected by later
    # Build105/Build111 owners into the final Messages page.
    "Отправка текста": "strings.textSending",
    "Text Sending": "strings.textSending",
    "Стиль отправки": "strings.sendStyle",
    "Send Style": "strings.sendStyle",
    "Стиль применяется после нажатия кнопки отправки.": "strings.sendStyleHint",
    "The style is applied after tapping the send button.": "strings.sendStyleHint",
    "Удалённые ответы": "strings.deletedReplies",
    "Deleted Replies": "strings.deletedReplies",
    "Переносимый ответ": "strings.portableReply",
    "Portable Reply": "strings.portableReply",
    "Переносимый ответ на удалённое": "strings.portableReply",
    "Сохранять удалённые медиа": "strings.saveDeletedMedia",
    "Save Deleted Media": "strings.saveDeletedMedia",
    "Ответ материализуется только после Send. Медиа хранится только во внутреннем кэше GhostBase: до 1 ГБ, 30 дней; если bytes недоступны, используется текстовый fallback.": "strings.portableReplyHint",
    "Ответ материализуется только после Send. Медиа хранится только во внутреннем кэше Jerkgram: до 1 ГБ, 30 дней; если bytes недоступны, используется текстовый fallback.": "strings.portableReplyHint",
    "The reply is materialized only after Send. Media is kept only in Jerkgram's internal cache: up to 1 GB for 30 days; if bytes are unavailable, a text fallback is used.": "strings.portableReplyHint",

    # Protected content.
    "Включить обход защиты": "strings.protectionEnabled",
    "Bypass Protection": "strings.protectionEnabled",
    "Поделиться из галереи": "strings.shareFromGallery",
    "Share from Gallery": "strings.shareFromGallery",
    "Сохранить из галереи": "strings.saveFromGallery",
    "Save from Gallery": "strings.saveFromGallery",
    "Копировать из галереи": "strings.copyFromGallery",
    "Copy from Gallery": "strings.copyFromGallery",
    "Сохранить из чата": "strings.saveFromChat",
    "Save from Chat": "strings.saveFromChat",
    "Копировать из чата": "strings.copyFromChat",
    "Copy from Chat": "strings.copyFromChat",
    "Переслать из чата": "strings.forwardFromChat",
    "Forward from Chat": "strings.forwardFromChat",
    "Разрешить скриншоты": "strings.allowScreenshots",
    "Allow Screenshots": "strings.allowScreenshots",
    "Разрешить запись экрана": "strings.allowScreenRecording",
    "Allow Screen Recording": "strings.allowScreenRecording",

    # Media & Stories.
    "Скриншоты одноразовых медиа": "strings.oneTimeScreenshots",
    "One-Time Media Screenshots": "strings.oneTimeScreenshots",
    "Запись одноразовых медиа": "strings.oneTimeScreenRecording",
    "One-Time Media Screen Recording": "strings.oneTimeScreenRecording",
    "Сохранение одноразовых медиа": "strings.oneTimeSave",
    "Save One-Time Media": "strings.oneTimeSave",
    "Одноразовые медиа": "strings.oneTimeMedia",
    "One-Time Media": "strings.oneTimeMedia",
    "Сохранение историй": "strings.storySave",
    "Save Stories": "strings.storySave",

    # Appearance / profile background.
    "Фон профиля": "strings.profileBackground",
    "Profile Background": "strings.profileBackground",
    "Эффект фона профиля": "strings.profileBackgroundEffect",
    "Profile Background Effect": "strings.profileBackgroundEffect",
    "Размывать аватар в профиле": "strings.blurProfileAvatar",
    "Размытие аватара в профиле": "strings.blurProfileAvatar",
    "Blur Profile Avatar": "strings.blurProfileAvatar",
    "Предпочитать аватар как фон": "strings.preferAvatarAsBackground",
    "Prefer Avatar as Background": "strings.preferAvatarAsBackground",
    "Анимированный фон": "strings.animatedBackground",
    "Animated Background": "strings.animatedBackground",
    "Цветовой tint": "strings.colorTint",
    "Цветовой оттенок": "strings.colorTint",
    "Color Tint": "strings.colorTint",
    "Облегчённое размытие": "strings.reducedBlur",
    "Reduced Blur": "strings.reducedBlur",
    "Видеоаватар зацикливается и использует кэш Telegram. В режиме энергосбережения или облегчённого размытия используется статический кадр.": "strings.animatedBackgroundHint",
    "The video avatar loops and uses Telegram's cache. In Low Power Mode or with Reduced Blur, a static frame is used.": "strings.animatedBackgroundHint",
    "Выключенный главный эффект не создаёт дополнительные profile views, observers или image/palette pipeline. Новые значения применяются при следующем открытии профиля.": "strings.profileEffectDisabledHint",
    "При выключенном главном тумблере профиль полностью использует штатный интерфейс Telegram.": "strings.profileEffectDisabledHint",
    "Когда главный эффект выключен, Jerkgram не создаёт дополнительные profile views, observers или image/palette pipeline. Новые значения применяются при следующем открытии профиля.": "strings.profileEffectDisabledHint",
    "When the main effect is disabled, Jerkgram creates no additional profile views, observers, or image/palette pipeline. New values apply the next time the profile opens.": "strings.profileEffectDisabledHint",
    "Прочее": "strings.other",
    "Other": "strings.other",
    "Интерфейс": "strings.interface",
    "Interface": "strings.interface",
    "Показывать секунды в сообщениях": "strings.messageSeconds",
    "Секунды в сообщениях": "strings.messageSeconds",
    "Message Seconds": "strings.messageSeconds",
    "Скрывать мой номер": "strings.hideMyPhone",
    "Hide My Phone Number": "strings.hideMyPhone",
    "Показывать RAM под часами": "strings.showRamUnderClock",
    "Show RAM Under Clock": "strings.showRamUnderClock",
    "Номер скрывается только локально в интерфейсе GhostBase. Экран изменения профиля и смены номера остаётся доступен.": "strings.hidePhoneHint",
    "Номер скрывается только локально в интерфейсе GhostBase.": "strings.hidePhoneHint",
    "Номер скрывается только локально в интерфейсе Jerkgram. Экран изменения профиля и смены номера остаётся доступен.": "strings.hidePhoneHint",
    "Номер скрывается только локально в интерфейсе Jerkgram.": "strings.hidePhoneHint",
    "Your phone number is hidden only locally in Jerkgram. Profile editing and number changing remain available.": "strings.hidePhoneHint",

    # Bounded Debug / Research diagnostics.
    "История присутствия пока пуста": "strings.presenceHistoryEmpty",
    "Presence history is empty": "strings.presenceHistoryEmpty",
    "Известные пользователи: нет данных": "strings.knownUsersNoData",
    "Known users: no data": "strings.knownUsersNoData",
    "Последние события": "strings.recentEvents",
    "Recent Events": "strings.recentEvents",
    "Событий пока нет": "strings.eventsEmpty",
    "No events yet": "strings.eventsEmpty",
    "Буфер ограничен 200 строками. Сбор не запускается при открытии этой страницы.": "strings.diagnosticsBufferHint",
    "The buffer is limited to 200 lines. Collection does not start when this page opens.": "strings.diagnosticsBufferHint",

    # Late debug/profile labels that are still legitimate settings labels.
    "Главное меню": "strings.mainMenu",
    "Main menu": "strings.mainMenu",
    "Main Menu": "strings.mainMenu",
    "Профиль": "strings.profile",
    "Profile": "strings.profile",
    "Показать raw ID и raw namespace": "strings.rawIdNamespace",
    "Raw ID / Namespace": "strings.rawIdNamespace",
    "Telegram ID": "strings.telegramId",
}

PAGE_CANONICAL = {
    'return "GhostBase"': 'return "Jerkgram"',
    'return "Основные функции"': 'return "Basic Functions"',
    'return "Ghost Mode"': 'return "Ghost Mode"',
    'return "Сообщения"': 'return "Messages"',
    'return "Защищённый контент"': 'return "Protected Content"',
    'return "Медиа и истории"': 'return "Media & Stories"',
    'return "Внешний вид"': 'return "Appearance"',
    'return "Debug / Research"': 'return "Debug / Research"',
    'return "О клиенте"': 'return "About"',
}

MAIN_TITLES = (
    (("GhostBase", "JerkGram", "Jerkgram"), "presentationData.strings.jerkgram.settingsTitle"),
    (("Ghost Mode",), "presentationData.strings.jerkgram.ghostMode"),
    (("Messages", "Сообщения"), "presentationData.strings.jerkgram.messages"),
    (("Protected Content", "Защищённый контент"), "presentationData.strings.jerkgram.protectedContent"),
    (("Media & Stories", "Медиа и истории"), "presentationData.strings.jerkgram.mediaAndStories"),
    (("Appearance", "Внешний вид"), "presentationData.strings.jerkgram.appearance"),
    (("Debug / Research",), "presentationData.strings.jerkgram.debugResearch"),
    (("About", "О клиенте"), "presentationData.strings.jerkgram.about"),
)


def require(value, message):
    if not value:
        raise RuntimeError("[Build115 settings localization] " + message)


def block_bounds(text, signature):
    start = text.find(signature)
    require(start >= 0, "block missing: " + signature)
    brace = text.find("{", start)
    require(brace >= 0, "opening brace missing: " + signature)
    depth = 0
    in_string = False
    escaped = False
    for index in range(brace, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return start, brace, index + 1
    raise RuntimeError("[Build115 settings localization] unterminated block: " + signature)


def replace_literal(region, literal, expression):
    token = '"' + literal.replace('\\', '\\\\').replace('"', '\\"') + '"'
    return region.replace(token, expression)


def cyrillic_string_literals(text):
    results = []
    pattern = re.compile(r'"""(.*?)"""|"(?:\\.|[^"\\])*"', re.S)
    for match in pattern.finditer(text):
        value = match.group(0)
        if re.search(r"[А-Яа-яЁё]", value):
            results.append(value.replace("\n", "\\n")[:180])
    return results


def patch_settings(text):
    require(MARKER not in text, "settings overlay already applied")
    require("BUILD110_SHORT_TOGGLE_TITLES1" in text, "Build110 settings prerequisite missing")

    # Keep the legacy .title property only for equality/compatibility, but make
    # its canonical values English/Jerkgram. Rendering uses localizedTitle().
    page_start = text.find("private enum GhostBaseSettingsPage")
    page_end = text.find("private final class GhostBaseSettingsArguments", page_start)
    require(page_start >= 0 and page_end > page_start, "settings page enum bounds missing")
    page_region = text[page_start:page_end]
    for old, new in PAGE_CANONICAL.items():
        page_region = page_region.replace(old, new)

    require("func localizedTitle(_ strings: JerkgramStrings)" not in page_region, "page localizer already exists")
    last_brace = page_region.rfind("}")
    require(last_brace >= 0, "settings page enum closing brace missing")
    localized = r'''

    func localizedTitle(_ strings: JerkgramStrings) -> String {
        switch self {
        case .root:
            return strings.settingsTitle
        case .home:
            return strings.basicFunctions
        case .ghostMode:
            return strings.ghostMode
        case .messages:
            return strings.messages
        case .protectedContent:
            return strings.protectedContent
        case .mediaStories:
            return strings.mediaAndStories
        case .appearance:
            return strings.appearance
        case .debugResearch:
            return strings.debugResearch
        case .about:
            return strings.about
        }
    }
'''
    page_region = page_region[:last_brace] + localized + page_region[last_brace:]
    text = text[:page_start] + page_region + text[page_end:]

    start, brace, end = block_bounds(text, "private func ghostBaseSettingsEntries(")
    entries = text[start:end]
    header = entries[:entries.find("{")]
    if "strings: JerkgramStrings" not in header:
        new_header, count = re.subn(
            r"page:\s*GhostBaseSettingsPage\s*\n\)",
            "page: GhostBaseSettingsPage,\n    strings: JerkgramStrings\n)",
            header,
            count=1,
        )
        require(count == 1, "entries signature page anchor missing")
        entries = new_header + entries[len(header):]

    # Recompute the entries region after the signature length changed.
    for literal, expression in ENTRY_LITERALS.items():
        entries = replace_literal(entries, literal, expression)

    balance_patterns = (
        '"Текущий визуальный баланс: \\(balance) ⭐"',
        '"Current visual balance: \\(balance) ⭐"',
    )
    for token in balance_patterns:
        entries = entries.replace(token, "strings.currentVisualBalance(balance)")

    # Appearance placeholder is a sentence and may still mention the legacy brand.
    for token in (
        '"Настройки оформления GhostBase будут добавляться в этот раздел."',
        '"Настройки оформления Jerkgram будут добавляться в этот раздел."',
        '"Jerkgram appearance settings will be added here."',
    ):
        entries = entries.replace(token, "strings.appearancePlaceholder")

    # The old About multiline block may still begin with the legacy public name.
    entries = re.sub(r"(?m)^GhostBase$", "Jerkgram", entries)

    leftovers = cyrillic_string_literals(entries)
    require(
        not leftovers,
        "unmapped Cyrillic settings strings: " + " | ".join(leftovers[:8])
    )

    text = text[:start] + MARKER + "\n" + entries + text[end:]

    call_pattern = re.compile(
        r"entries:\s*ghostBaseSettingsEntries\(\s*"
        r"state:\s*state,\s*context:\s*context,\s*page:\s*page\s*\),",
        re.S,
    )
    replacement = """entries: ghostBaseSettingsEntries(
                state: state,
                context: context,
                page: page,
                strings: presentationData.strings.jerkgram
            ),"""
    text, count = call_pattern.subn(replacement, text, count=1)
    require(count == 1, "entries call anchor missing")

    require("title: .text(page.title)," in text, "page title render anchor missing")
    text = text.replace(
        "title: .text(page.title),",
        "title: .text(page.localizedTitle(presentationData.strings.jerkgram)),",
        1,
    )

    return text


def patch_main_items(text):
    require(MAIN_MARKER not in text, "main settings overlay already applied")
    start = text.find(OLD_MAIN_MARKER)
    require(start >= 0, "legacy main settings marker missing")

    cursor = start
    for _ in range(8):
        cursor = text.find("interaction.openSettings(.ghostbase)", cursor)
        require(cursor >= 0, "expected eight Jerkgram settings rows")
        cursor += len("interaction.openSettings(.ghostbase)")

    region = text[start:cursor]
    region = region.replace(OLD_MAIN_MARKER, OLD_MAIN_MARKER + "\n" + MAIN_MARKER, 1)

    for alternatives, expression in MAIN_TITLES:
        replaced = False
        for title in alternatives:
            token = 'text: "' + title + '"'
            if token in region:
                region = region.replace(token, "text: " + expression, 1)
                replaced = True
                break
        require(replaced, "main settings title missing: " + "/".join(alternatives))

    require('text: "GhostBase"' not in region, "legacy visible GhostBase row survived")
    return text[:start] + region + text[cursor:]


def main():
    require(SETTINGS.is_file(), "GhostBaseSettingsController.swift missing")
    require(MAIN_ITEMS.is_file(), "PeerInfoSettingsItems.swift missing")
    require(
        (ROOT / "submodules/TelegramPresentationData/Sources/JerkgramStrings.swift").is_file(),
        "JerkgramStrings foundation missing"
    )

    settings = patch_settings(SETTINGS.read_text(encoding="utf-8"))
    main_items = patch_main_items(MAIN_ITEMS.read_text(encoding="utf-8"))

    SETTINGS.write_text(settings, encoding="utf-8")
    MAIN_ITEMS.write_text(main_items, encoding="utf-8")

    print("[Build115 settings localization] visible Settings rows -> JerkgramStrings")
    print("[Build115 settings localization] navigation titles -> Telegram language")
    print("[Build115 settings localization] main Settings rows -> Telegram language")
    print("[Build115 settings localization] no hard-coded Cyrillic in visible entries")


if __name__ == "__main__":
    main()
