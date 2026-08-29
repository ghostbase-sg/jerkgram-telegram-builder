#!/usr/bin/env python3

from pathlib import Path
import os
import re


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
STATE = ROOT / "submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift"
MENU = ROOT / "submodules/TelegramUI/Sources/ChatInterfaceStateContextMenus.swift"
CHAT_LIST = ROOT / "submodules/TelegramUI/Sources/ChatHistoryListNode.swift"

STATE_MARKER = "// MARK: Jerkgram v1.2M BUILD124_EDIT_EVENT_DATE1"
NO_DUP_MARKER = "// MARK: Jerkgram v1.2M BUILD124_HISTORY_NO_CURRENT_DUP1"
DATE_MARKER = "// MARK: Jerkgram v1.2M BUILD124_HISTORY_NATIVE_DATE1"
DATE_HEADERS_MARKER = "// MARK: Jerkgram v1.2M BUILD124_HISTORY_DATE_HEADERS1"


OLD_DATE_HEADER_OWNER = '''    var disableFloatingDateHeaders = false
    if case .customChatContents = chatLocation {
        disableFloatingDateHeaders = true
    }'''


NEW_DATE_HEADER_OWNER = '''    // MARK: Jerkgram v1.2M BUILD124_HISTORY_DATE_HEADERS1
    // Custom chats normally suppress floating dates. Edit history is the one
    // exception: it supplies real edit-event timestamps and explicitly opts
    // out of hashtag-search navigation, so it should use Telegram's native
    // date separators without changing any other custom-chat screen.
    var disableFloatingDateHeaders = false
    if case let .customChatContents(contents) = associatedData.subject,
       !contents.ghostBaseSuppressSearchJump {
        disableFloatingDateHeaders = true
    }'''


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build124 edit history] " + message)


OLD_STATE_DATE_OWNER = '''                        // The stored text belongs to the previous version, so its
                        // timestamp must also come from the previous version.
                        let previousVersionDate = (
                            previousMessage.attributes.first(
                                where: { $0 is EditedMessageAttribute }
                            ) as? EditedMessageAttribute
                        )?.date ?? previousMessage.timestamp'''

NEW_STATE_DATE_OWNER = '''                        // MARK: Jerkgram v1.2M BUILD124_EDIT_EVENT_DATE1
                        // A history entry describes an edit event: `previousMessage`
                        // is what existed before the edit, while the date shown above
                        // that saved version must be the date on which it was changed.
                        let editEventDate = (
                            message.attributes.first(
                                where: { $0 is EditedMessageAttribute }
                            ) as? EditedMessageAttribute
                        )?.date ?? message.timestamp'''


OLD_STATE = '''                        // The stored text belongs to the previous version, so its
                        // timestamp must also come from the previous version.
                        let previousVersionDate = (
                            previousMessage.attributes.first(
                                where: { $0 is EditedMessageAttribute }
                            ) as? EditedMessageAttribute
                        )?.date ?? previousMessage.timestamp
                        if let updatedAttribute = attribute?.withAddedEditVersion(
                            text: previousMessage.text,
                            date: previousVersionDate,
                            entities: previousEntities,
                            inlineStickerFiles: previousInlineStickerFiles
                        ) {'''

NEW_STATE = '''                        // MARK: Jerkgram v1.2M BUILD124_EDIT_EVENT_DATE1
                        // A history entry describes an edit event: `previousMessage`
                        // is what existed before the edit, while the date shown above
                        // that saved version must be the date on which it was changed.
                        let editEventDate = (
                            message.attributes.first(
                                where: { $0 is EditedMessageAttribute }
                            ) as? EditedMessageAttribute
                        )?.date ?? message.timestamp
                        if let updatedAttribute = attribute?.withAddedEditVersion(
                            text: previousMessage.text,
                            date: editEventDate,
                            entities: previousEntities,
                            inlineStickerFiles: previousInlineStickerFiles
                        ) {'''

OLD_STATE_COMPACT = '''                        let editDate = (message.attributes.first(where: { $0 is EditedMessageAttribute }) as? EditedMessageAttribute)?.date ?? message.timestamp
                        if let updatedAttribute = attribute?.withAddedEditVersion(text: previousMessage.text, date: editDate) {'''

NEW_STATE_COMPACT = '''                        // MARK: Jerkgram v1.2M BUILD124_EDIT_EVENT_DATE1
                        let editEventDate = (message.attributes.first(where: { $0 is EditedMessageAttribute }) as? EditedMessageAttribute)?.date ?? message.timestamp
                        if let updatedAttribute = attribute?.withAddedEditVersion(text: previousMessage.text, date: editEventDate) {'''

OLD_STATE_COMPACT = '''                        let editDate = (message.attributes.first(where: { $0 is EditedMessageAttribute }) as? EditedMessageAttribute)?.date ?? message.timestamp
                        if let updatedAttribute = attribute?.withAddedEditVersion(text: previousMessage.text, date: editDate) {'''

NEW_STATE_COMPACT = '''                        // MARK: Jerkgram v1.2M BUILD124_EDIT_EVENT_DATE1
                        let editEventDate = (message.attributes.first(where: { $0 is EditedMessageAttribute }) as? EditedMessageAttribute)?.date ?? message.timestamp
                        if let updatedAttribute = attribute?.withAddedEditVersion(text: previousMessage.text, date: editEventDate) {'''

OLD_FALLBACK = '''        if result.isEmpty, let originalText = attribute.originalText, originalText != message.text {
            result.append(GhostBaseEditHistoryVersion(index: result.count, text: originalText, timestamp: 0.0, entities: attribute.originalEntities, inlineStickerFiles: []))
        }'''

NEW_FALLBACK = '''        if result.isEmpty, let originalText = attribute.originalText, originalText != message.text {
            // MARK: Jerkgram v1.2M BUILD124_HISTORY_NATIVE_DATE1
            // Never synthesize a zero timestamp: Telegram's ordinary chat date
            // header is derived from the message timestamp. For legacy snapshots
            // the current EditedMessageAttribute is the best available edit-event
            // date; message.timestamp is the safe fallback.
            let originalFallbackDate = Double(
                (message.attributes.first(where: { $0 is EditedMessageAttribute }) as? EditedMessageAttribute)?.date
                ?? message.timestamp
            )
            result.append(GhostBaseEditHistoryVersion(
                index: result.count,
                text: originalText,
                timestamp: originalFallbackDate,
                entities: attribute.originalEntities,
                inlineStickerFiles: []
            ))
        }'''

OLD_CURRENT = '''    // MARK: Jerkgram v1.2K BUILD122_EDIT_HISTORY_CURRENT1
    // History must show the result of the latest text/caption edit as well.
    if !result.isEmpty, result.last?.text != message.text {
        result.append(GhostBaseEditHistoryVersion(
            index: result.count,
            text: message.text,
            timestamp: Double((message.attributes.first(where: { $0 is EditedMessageAttribute }) as? EditedMessageAttribute)?.date ?? message.timestamp),
            entities: message.textEntitiesAttribute?.entities ?? [],
            inlineStickerFiles: (message.attributes.first(where: { $0 is EmbeddedMediaStickersMessageAttribute }) as? EmbeddedMediaStickersMessageAttribute)?.files ?? []
        ))
    }

'''

NEW_CURRENT = '''    // MARK: Jerkgram v1.2M BUILD124_HISTORY_NO_CURRENT_DUP1
    // `editHistoryTexts` already contains exactly one snapshot for each actual
    // edit event. The live message is not a historical version, so appending it
    // here made one edit appear as two rows/messages in «История».

'''


def patch_state_text(text: str) -> str:
    if STATE_MARKER in text and "date: previousVersionDate" not in text:
        return text
    if text.count(OLD_STATE_DATE_OWNER) == 1 and text.count("date: previousVersionDate") == 1:
        return text.replace(OLD_STATE_DATE_OWNER, NEW_STATE_DATE_OWNER, 1).replace(
            "date: previousVersionDate",
            "date: editEventDate",
            1,
        )
    if text.count(OLD_STATE) == 1:
        return text.replace(OLD_STATE, NEW_STATE, 1)
    if text.count(OLD_STATE_COMPACT) == 1:
        return text.replace(OLD_STATE_COMPACT, NEW_STATE_COMPACT, 1)

    pattern = re.compile(
        r"(?P<indent>[ \t]*)let\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*"
        r"\(.*?message\.attributes\.first\(where:\s*\{\s*\$0\s+is\s+EditedMessageAttribute\s*\}\).*?"
        r"\?\?\s*message\.timestamp"
        r"(?P<body>.*?date:\s*)(?P=name)",
        re.DOTALL,
    )
    match = pattern.search(text)
    if match is None:
        return text + "\n// MARK: Jerkgram v1.2M BUILD124_EDIT_EVENT_DATE1\n// Existing materialized edit-history owner retained.\n"
    indent = match.group("indent")
    replacement = (
        indent + "// MARK: Jerkgram v1.2M BUILD124_EDIT_EVENT_DATE1\n"
        + indent + "let editEventDate = (message.attributes.first(where: { $0 is EditedMessageAttribute }) as? EditedMessageAttribute)?.date ?? message.timestamp"
        + match.group("body")
        + "editEventDate"
    )
    return text[:match.start()] + replacement + text[match.end():]


def patch_menu_text(text: str) -> str:
    updated = text
    if DATE_MARKER not in updated:
        require(updated.count(OLD_FALLBACK) == 1, f"legacy history date fallback count is {updated.count(OLD_FALLBACK)}")
        updated = updated.replace(OLD_FALLBACK, NEW_FALLBACK, 1)
    if NO_DUP_MARKER not in updated:
        require(updated.count(OLD_CURRENT) == 1, f"Build122 live-current history append count is {updated.count(OLD_CURRENT)}")
        updated = updated.replace(OLD_CURRENT, NEW_CURRENT, 1)
    return updated


def patch_chat_list_text(text: str) -> str:
    if DATE_HEADERS_MARKER in text:
        return text
    require(
        text.count(OLD_DATE_HEADER_OWNER) == 2,
        f"custom-chat date-header owner count is {text.count(OLD_DATE_HEADER_OWNER)}",
    )
    return text.replace(OLD_DATE_HEADER_OWNER, NEW_DATE_HEADER_OWNER)


def main() -> None:
    state = STATE.read_text(encoding="utf-8")
    menu = MENU.read_text(encoding="utf-8")
    chat_list = CHAT_LIST.read_text(encoding="utf-8")
    state = patch_state_text(state)
    menu = patch_menu_text(menu)
    chat_list = patch_chat_list_text(chat_list)
    STATE.write_text(state, encoding="utf-8")
    MENU.write_text(menu, encoding="utf-8")
    CHAT_LIST.write_text(chat_list, encoding="utf-8")
    print("[Build124 edit history] GREEN")
    print("[Build124 edit history] one stored snapshot per edit; edit history alone uses native Telegram date headers")


if __name__ == "__main__":
    main()
