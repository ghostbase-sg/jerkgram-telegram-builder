#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
STATE = ROOT / "submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift"
MENU = ROOT / "submodules/TelegramUI/Sources/ChatInterfaceStateContextMenus.swift"

STATE_MARKER = "// MARK: Jerkgram v1.2M BUILD124_EDIT_EVENT_DATE1"
NO_DUP_MARKER = "// MARK: Jerkgram v1.2M BUILD124_HISTORY_NO_CURRENT_DUP1"
DATE_MARKER = "// MARK: Jerkgram v1.2M BUILD124_HISTORY_NATIVE_DATE1"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build124 edit history] " + message)


OLD_DATE_DECL = '''                        let previousVersionDate = (
                            previousMessage.attributes.first(
                                where: { $0 is EditedMessageAttribute }
                            ) as? EditedMessageAttribute
                        )?.date ?? previousMessage.timestamp'''

NEW_DATE_DECL = '''                        // MARK: Jerkgram v1.2M BUILD124_EDIT_EVENT_DATE1
                        // The stored snapshot is the value that existed before this
                        // edit, but its history date belongs to the edit event that
                        // replaced it. Use the incoming edited message as that owner.
                        let editEventDate = (
                            message.attributes.first(
                                where: { $0 is EditedMessageAttribute }
                            ) as? EditedMessageAttribute
                        )?.date ?? message.timestamp'''

OLD_DATE_USE = "                            date: previousVersionDate,"
NEW_DATE_USE = "                            date: editEventDate,"

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
    if STATE_MARKER in text:
        return text

    # Bind only to the two semantic owners that Build122/123 establish. Do not
    # include surrounding comments or the Build123 entity/sticker arguments in
    # the anchor: those are independent fidelity owners and may evolve safely.
    require(text.count(OLD_DATE_DECL) == 1, f"previous edit-date declaration count is {text.count(OLD_DATE_DECL)}")
    require(text.count(OLD_DATE_USE) == 1, f"previous edit-date use count is {text.count(OLD_DATE_USE)}")
    updated = text.replace(OLD_DATE_DECL, NEW_DATE_DECL, 1)
    updated = updated.replace(OLD_DATE_USE, NEW_DATE_USE, 1)
    require("date: previousVersionDate" not in updated, "previous-version date use survived")
    return updated


def patch_menu_text(text: str) -> str:
    updated = text
    if DATE_MARKER not in updated:
        require(updated.count(OLD_FALLBACK) == 1, f"legacy history date fallback count is {updated.count(OLD_FALLBACK)}")
        updated = updated.replace(OLD_FALLBACK, NEW_FALLBACK, 1)
    if NO_DUP_MARKER not in updated:
        require(updated.count(OLD_CURRENT) == 1, f"Build122 live-current history append count is {updated.count(OLD_CURRENT)}")
        updated = updated.replace(OLD_CURRENT, NEW_CURRENT, 1)
    return updated


def main() -> None:
    state = STATE.read_text(encoding="utf-8")
    menu = MENU.read_text(encoding="utf-8")
    state = patch_state_text(state)
    menu = patch_menu_text(menu)
    STATE.write_text(state, encoding="utf-8")
    MENU.write_text(menu, encoding="utf-8")
    print("[Build124 edit history] GREEN")
    print("[Build124 edit history] one stored snapshot per edit; edit-event timestamps feed native Telegram date headers")


if __name__ == "__main__":
    main()
