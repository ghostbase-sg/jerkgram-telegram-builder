#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(
    os.environ.get(
        "JERKGRAM_SOURCE_ROOT",
        os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())),
    )
).resolve()

PROFILE = ROOT / (
    "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/"
    "Sources/PeerInfoData.swift"
)
CHAT = ROOT / "submodules/TelegramUI/Sources/ChatController.swift"
SETTINGS = ROOT / (
    "submodules/SettingsUI/Sources/GhostBase/"
    "GhostBaseSettingsController.swift"
)
STRINGS = ROOT / (
    "submodules/TelegramPresentationData/Sources/JerkgramStrings.swift"
)


def require(value, message):
    if not value:
        raise RuntimeError("[Build116 UI] " + message)


def replace_once(text, old, new, label):
    count = text.count(old)
    require(count == 1, f"{label}: expected 1 anchor, found {count}")
    return text.replace(old, new, 1)


def block_bounds(text, marker, opening):
    marker_index = text.find(marker)
    require(marker_index >= 0, "marker missing: " + marker)
    start = text.find(opening, marker_index)
    require(start >= 0, "block opening missing after: " + marker)
    brace = text.find("{", start)
    require(brace >= 0, "block brace missing after: " + marker)
    depth = 0
    in_string = False
    escaped = False
    for index in range(brace, len(text)):
        character = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return marker_index, index + 1
    raise RuntimeError("[Build116 UI] unbalanced block after: " + marker)


def numeric_peer_id(value):
    value = value.strip()
    if value.startswith("@"):
        value = value[1:]
    if value.lower().startswith("id"):
        value = value[2:]
    if not value or not all("0" <= character <= "9" for character in value):
        return None
    result = int(value)
    if result <= 0 or result > 9223372036854775807:
        return None
    return result


def patch_profile_ui(text):
    old = '''// MARK: GhostBase v1.1G NATIVEPANES1
// MARK: Jerkgram v1.2D BUILD115_HIDE_RESEARCH_PANES1
private func ghostBaseAppendingProfilePanes(
    _ availablePanes: [PeerInfoPaneKey],
    peer: EnginePeer?,
    personalChannel: PeerInfoPersonalChannelData?
) -> [PeerInfoPaneKey] {
    // Keep PROFILEINTEL/history recording and persisted data intact,
    // but do not publish raw research/report panes in the normal
    // Telegram profile UI.
    return availablePanes
}
'''
    new = '''// MARK: GhostBase v1.1G NATIVEPANES1
// MARK: Jerkgram v1.2E BUILD116_PROFILE_SCOPE1
private func ghostBaseAppendingProfilePanes(
    _ availablePanes: [PeerInfoPaneKey],
    peer: EnginePeer?,
    personalChannel: PeerInfoPersonalChannelData?
) -> [PeerInfoPaneKey] {
    guard let peer, case .user = peer else {
        return availablePanes
    }

    var result = availablePanes
    for key in [
        PeerInfoPaneKey.ghostBaseProfileHistory,
        PeerInfoPaneKey.ghostBasePresence,
        PeerInfoPaneKey.ghostBaseGiftHistory
    ] where !result.contains(key) {
        result.append(key)
    }

    if personalChannel != nil,
       !result.contains(.ghostBasePersonalChannel) {
        result.append(.ghostBasePersonalChannel)
    }

    return result
}
'''
    return replace_once(text, old, new, "Build115 profile suppression")


def patch_chat_mentions(text):
    anchor = '''    func openPeerMention(_ name: String, navigation: ChatControllerInteractionNavigateToPeer = .default, sourceMessageId: MessageId? = nil, progress: Promise<Bool>? = nil) {
        let _ = self.presentVoiceMessageDiscardAlert(action: {
'''
    replacement = '''    // MARK: Jerkgram v1.2E BUILD116_CHAT_NUMERIC_MENTION1
    private func jerkgramNumericMentionPeerId(_ source: String) -> Int64? {
        var value = source.trimmingCharacters(in: .whitespacesAndNewlines)

        if value.hasPrefix("@") {
            value.removeFirst()
        }
        if value.lowercased().hasPrefix("id") {
            value.removeFirst(2)
        }

        guard !value.isEmpty,
              value.unicodeScalars.allSatisfy({ scalar in
                  scalar.value >= 48 && scalar.value <= 57
              }),
              let result = Int64(value),
              result > 0 else {
            return nil
        }

        return result
    }

    func openPeerMention(_ name: String, navigation: ChatControllerInteractionNavigateToPeer = .default, sourceMessageId: MessageId? = nil, progress: Promise<Bool>? = nil) {
        let _ = self.presentVoiceMessageDiscardAlert(action: {
            if let idValue = self.jerkgramNumericMentionPeerId(name) {
                self.openUrl("https://t.me/@id\\(idValue)", concealed: false)
                return
            }
'''
    return replace_once(text, anchor, replacement, "ChatController mention owner")


def patch_settings_runtime(text):
    start, end = block_bounds(
        text,
        "// MARK: GhostBase v1.1G BOUNDEDDEBUG1",
        "if page == .debugResearch {",
    )
    new = '''    // MARK: Jerkgram v1.2E BUILD116_SETTINGS_RUNTIME_CLEANUP1
    if page == .debugResearch {
        return []
    }
'''
    return text[:start] + new + text[end:]


def patch_strings(text):
    key_anchor = "    case exportArchive\n}"
    key_replacement = '''    case exportArchive

    case sendStyleNormal
    case sendStyleBold
    case sendStyleItalic
    case sendStyleMonospace
    case sendStyleStrikethrough
    case sendStyleUnderline
    case sendStyleSpoiler
    case sendStyleExamplePrefix
    case sendStyleExampleBody
    case community
    case communityHint
    case copyExtensionDiagnostics
}'''
    text = replace_once(text, key_anchor, key_replacement, "Jerkgram string keys")

    property_anchor = "    public var exportArchive: String { self.text(.exportArchive) }"
    property_replacement = '''    public var exportArchive: String { self.text(.exportArchive) }

    public var sendStyleNormal: String { self.text(.sendStyleNormal) }
    public var sendStyleBold: String { self.text(.sendStyleBold) }
    public var sendStyleItalic: String { self.text(.sendStyleItalic) }
    public var sendStyleMonospace: String { self.text(.sendStyleMonospace) }
    public var sendStyleStrikethrough: String { self.text(.sendStyleStrikethrough) }
    public var sendStyleUnderline: String { self.text(.sendStyleUnderline) }
    public var sendStyleSpoiler: String { self.text(.sendStyleSpoiler) }
    public var sendStyleExamplePrefix: String { self.text(.sendStyleExamplePrefix) }
    public var sendStyleExampleBody: String { self.text(.sendStyleExampleBody) }
    public var community: String { self.text(.community) }
    public var communityHint: String { self.text(.communityHint) }
    public var copyExtensionDiagnostics: String { self.text(.copyExtensionDiagnostics) }'''
    text = replace_once(text, property_anchor, property_replacement, "Jerkgram string properties")

    english_anchor = '        .exportArchive: "Export Jerkgram Archive"\n'
    english_replacement = '''        .exportArchive: "Export Jerkgram Archive",

        .sendStyleNormal: "Normal",
        .sendStyleBold: "Bold",
        .sendStyleItalic: "Italic",
        .sendStyleMonospace: "Monospace",
        .sendStyleStrikethrough: "Strikethrough",
        .sendStyleUnderline: "Underline",
        .sendStyleSpoiler: "Spoiler",
        .sendStyleExamplePrefix: "Example: ",
        .sendStyleExampleBody: "this is how your text will look",
        .community: "Jerkgram Community",
        .communityHint: "News, builds and updates",
        .copyExtensionDiagnostics: "Copy Extension Diagnostics"
'''
    text = replace_once(text, english_anchor, english_replacement, "English Build116 strings")

    russian_anchor = '        .exportArchive: "Экспорт архива Jerkgram"\n'
    russian_replacement = '''        .exportArchive: "Экспорт архива Jerkgram",

        .sendStyleNormal: "Обычный",
        .sendStyleBold: "Жирный",
        .sendStyleItalic: "Курсив",
        .sendStyleMonospace: "Моноширинный",
        .sendStyleStrikethrough: "Зачёркнутый",
        .sendStyleUnderline: "Подчёркнутый",
        .sendStyleSpoiler: "Спойлер",
        .sendStyleExamplePrefix: "Пример: ",
        .sendStyleExampleBody: "так будет выглядеть ваш текст",
        .community: "Сообщество Jerkgram",
        .communityHint: "Новости, сборки и обновления",
        .copyExtensionDiagnostics: "Копировать диагностику расширений"
'''
    return replace_once(text, russian_anchor, russian_replacement, "Russian Build116 strings")


def _replace_about_block(text):
    marker = "if page == .about {"
    start = text.find(marker)
    require(start != -1, "About block missing")
    brace = text.find("{", start)
    depth = 0
    end = None
    for index in range(brace, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                end = index + 1
                break
    require(end is not None, "About block is unbalanced")
    replacement = '''// MARK: Jerkgram v1.2E BUILD116_ABOUT_COMMUNITY1
    if page == .about {
        return [
            .header(0, strings.about),
            .researchAction(
                0,
                1,
                strings.community,
                "https://t.me/JerkgramApp"
            ),
            .info(0, strings.communityHint),
            .info(1, "Jerkgram\\nBase: Official Telegram 12.9.2\\nBuild: 116")
        ]
    }'''
    return text[:start] + replacement + text[end:]


def patch_settings_localization_about(text):
    title_old = '''private func ghostBaseSendTextStyleTitle(
    _ value: String
) -> String {
    switch value {
    case "bold":
        return "Жирный"
    case "italic":
        return "Курсив"
    case "monospace":
        return "Моноширинный"
    case "strikethrough":
        return "Зачёркнутый"
    case "underline":
        return "Подчёркнутый"
    case "spoiler":
        return "Спойлер"
    default:
        return "Обычный"
    }
}'''
    title_new = '''// MARK: Jerkgram v1.2E BUILD116_STYLE_LOCALIZATION1
private func ghostBaseSendTextStyleTitle(
    _ value: String,
    strings: JerkgramStrings
) -> String {
    switch value {
    case "bold":
        return strings.sendStyleBold
    case "italic":
        return strings.sendStyleItalic
    case "monospace":
        return strings.sendStyleMonospace
    case "strikethrough":
        return strings.sendStyleStrikethrough
    case "underline":
        return strings.sendStyleUnderline
    case "spoiler":
        return strings.sendStyleSpoiler
    default:
        return strings.sendStyleNormal
    }
}'''
    text = replace_once(text, title_old, title_new, "send style title helper")

    text = text.replace(
        "ghostBaseSendTextStyleTitle(value)",
        "ghostBaseSendTextStyleTitle(\n                    value,\n                    strings: presentationData.strings.jerkgram\n                )",
    )

    menu_signature = '''private func ghostBaseSendStyleMenuItems(
    selected: String,
    select: @escaping (String) -> Void
) -> [ContextMenuItem] {'''
    if menu_signature in text:
        text = text.replace(
            menu_signature,
            '''private func ghostBaseSendStyleMenuItems(
    selected: String,
    strings: JerkgramStrings,
    select: @escaping (String) -> Void
) -> [ContextMenuItem] {''',
            1,
        )
        menu_list = '''    let styles = [
        ("normal", "Обычный"),
        ("bold", "Жирный"),
        ("italic", "Курсив"),
        ("monospace", "Моноширинный"),
        ("strikethrough", "Зачёркнутый"),
        ("underline", "Подчёркнутый"),
        ("spoiler", "Спойлер")
    ]'''
        localized_menu_list = '''    let styles = [
        ("normal", strings.sendStyleNormal),
        ("bold", strings.sendStyleBold),
        ("italic", strings.sendStyleItalic),
        ("monospace", strings.sendStyleMonospace),
        ("strikethrough", strings.sendStyleStrikethrough),
        ("underline", strings.sendStyleUnderline),
        ("spoiler", strings.sendStyleSpoiler)
    ]'''
        text = replace_once(
            text,
            menu_list,
            localized_menu_list,
            "legacy send style menu localization",
        )
    text = text.replace(
        'string: "Пример: ",',
        "string: presentationData.strings.jerkgram.sendStyleExamplePrefix,",
    )
    text = text.replace(
        'text: "так будет выглядеть ваш текст",',
        "text: presentationData.strings.jerkgram.sendStyleExampleBody,",
    )
    text = text.replace(
        'let previewPrefix = "Пример: "',
        "let previewPrefix = presentationData.strings.jerkgram.sendStyleExamplePrefix",
    )
    text = text.replace(
        'let previewBody = "так будет выглядеть ваш текст"',
        "let previewBody = presentationData.strings.jerkgram.sendStyleExampleBody",
    )

    style_list = '''let styles: [(String, String)] = [
    ("normal", "Обычный"),
    ("bold", "Жирный"),
    ("italic", "Курсив"),
    ("monospace", "Моноширинный"),
    ("strikethrough", "Зачёркнутый"),
    ("underline", "Подчёркнутый"),
    ("spoiler", "Спойлер")
]'''
    localized_list = '''let styles: [(String, String)] = [
    ("normal", strings.sendStyleNormal),
    ("bold", strings.sendStyleBold),
    ("italic", strings.sendStyleItalic),
    ("monospace", strings.sendStyleMonospace),
    ("strikethrough", strings.sendStyleStrikethrough),
    ("underline", strings.sendStyleUnderline),
    ("spoiler", strings.sendStyleSpoiler)
]'''
    if style_list in text:
        text = text.replace(style_list, localized_list)

    page_list = '''    let styles: [(String, String)] = [
        ("normal", "Обычный"),
        ("bold", "Жирный"),
        ("italic", "Курсив"),
        ("monospace", "Моноширинный"),
        ("strikethrough", "Зачёркнутый"),
        ("underline", "Подчёркнутый"),
        ("spoiler", "Спойлер")
    ]'''
    localized_page_list = '''    let styles: [(String, String)] = [
        ("normal", strings.sendStyleNormal),
        ("bold", strings.sendStyleBold),
        ("italic", strings.sendStyleItalic),
        ("monospace", strings.sendStyleMonospace),
        ("strikethrough", strings.sendStyleStrikethrough),
        ("underline", strings.sendStyleUnderline),
        ("spoiler", strings.sendStyleSpoiler)
    ]'''
    text = text.replace(page_list, localized_page_list)

    text = text.replace(
        "private func ghostBaseSendStylePageEntries(\n    selected: String\n)",
        "private func ghostBaseSendStylePageEntries(\n    selected: String,\n    strings: JerkgramStrings\n)",
    )
    text = text.replace(
        "entries: ghostBaseSendStylePageEntries(\n                selected: value\n            )",
        "entries: ghostBaseSendStylePageEntries(\n                selected: value,\n                strings: presentationData.strings.jerkgram\n            )",
    )
    text = text.replace(
        'title: .text("Стиль отправки"),',
        "title: .text(presentationData.strings.jerkgram.sendStyle),",
    )
    text = text.replace(
        'let styleTitle = "Стиль отправки"',
        "let styleTitle = strings.sendStyle",
    )

    text = _replace_about_block(text)

    research_action_anchor = '''        case let .researchAction(_, _, title, actionId):
            return ItemListDisclosureItem('''
    if research_action_anchor in text:
        text = text.replace(
            "disclosureStyle: .none,\n                action: {\n                    arguments.runResearchAction(actionId)",
            "disclosureStyle: actionId.hasPrefix(\"https://\") ? .arrow : .none,\n                action: {\n                    arguments.runResearchAction(actionId)",
            1,
        )

    action_anchor = '''            switch action {
            case "hiddenGiftsSelf":
'''
    if action_anchor in text:
        action_replacement = '''            switch action {
            case "https://t.me/JerkgramApp":
                context.sharedContext.applicationBindings.openUrl(action)

            case "hiddenGiftsSelf":
'''
        text = replace_once(text, action_anchor, action_replacement, "community URL action")

    return text


def main():
    for path in (PROFILE, CHAT, SETTINGS, STRINGS):
        require(path.is_file(), "source owner missing: " + str(path))

    PROFILE.write_text(
        patch_profile_ui(PROFILE.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    CHAT.write_text(
        patch_chat_mentions(CHAT.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    settings = patch_settings_runtime(SETTINGS.read_text(encoding="utf-8"))
    settings = patch_settings_localization_about(settings)
    SETTINGS.write_text(settings, encoding="utf-8")
    STRINGS.write_text(
        patch_strings(STRINGS.read_text(encoding="utf-8")),
        encoding="utf-8",
    )

    print("[Build116 UI] profile panes restored")
    print("[Build116 UI] chat numeric mention owner patched")
    print("[Build116 UI] raw Settings Runtime list removed")
    print("[Build116 UI] send style localized and About community added")


if __name__ == "__main__":
    main()
