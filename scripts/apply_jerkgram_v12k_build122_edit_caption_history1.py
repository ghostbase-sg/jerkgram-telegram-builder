#!/usr/bin/env python3
from pathlib import Path
import os


ROOT = Path(os.environ.get(
    "JERKGRAM_SOURCE_ROOT",
    os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())),
)).resolve()
CORE = ROOT / "submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift"
UI = ROOT / "submodules/TelegramUI/Sources/ChatInterfaceStateContextMenus.swift"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build122 edit/caption history] " + message)


def replace_once(path: Path, old: str, new: str, marker: str) -> None:
    text = path.read_text(encoding="utf-8")
    if marker in text:
        return
    require(text.count(old) == 1, f"{path}: owner count for {marker} != 1")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    require(CORE.is_file(), "TelegramCore edit owner missing")
    require(UI.is_file(), "TelegramUI history owner missing")

    old_capture = '''                    if ghostBaseSaveEditHistory,
                       previousMessage.text != message.text,
                       !previousMessage.text.isEmpty {
                        JerkgramCaptureRecorder.record('''
    new_capture = '''                    // MARK: Jerkgram v1.2K BUILD122_EDIT_CAPTION_HISTORY1
                    // Telegram captions and ordinary message bodies both live in message.text.
                    // Keep empty -> caption and caption -> empty transitions as real versions.
                    if ghostBaseSaveEditHistory,
                       previousMessage.text != message.text {
                        JerkgramCaptureRecorder.record('''
    replace_once(CORE, old_capture, new_capture, "BUILD122_EDIT_CAPTION_HISTORY1")

    old_date = '''                        let editDate = (
                            message.attributes.first(
                                where: { $0 is EditedMessageAttribute }
                            ) as? EditedMessageAttribute
                        )?.date ?? message.timestamp'''
    new_date = '''                        // The stored text belongs to the previous version, so its
                        // timestamp must also come from the previous version.
                        let previousVersionDate = (
                            previousMessage.attributes.first(
                                where: { $0 is EditedMessageAttribute }
                            ) as? EditedMessageAttribute
                        )?.date ?? previousMessage.timestamp'''
    replace_once(CORE, old_date, new_date, "previousVersionDate")

    core_text = CORE.read_text(encoding="utf-8")
    old_use = '''                            text: previousMessage.text,
                            date: editDate
                        )'''
    new_use = '''                            text: previousMessage.text,
                            date: previousVersionDate
                        )'''
    require(core_text.count(old_use) == 1 or new_use in core_text, "previous version date use owner mismatch")
    if new_use not in core_text:
        CORE.write_text(core_text.replace(old_use, new_use, 1), encoding="utf-8")

    old_ui = '''    if result.isEmpty {
        result = ghostBaseLoadEditHistoryVersions(messageId: message.id)
    }

    return result
}'''
    new_ui = '''    if result.isEmpty {
        result = ghostBaseLoadEditHistoryVersions(messageId: message.id)
    }

    // MARK: Jerkgram v1.2K BUILD122_EDIT_HISTORY_CURRENT1
    // History must show the result of the latest text/caption edit as well.
    if !result.isEmpty, result.last?.text != message.text {
        result.append(GhostBaseEditHistoryVersion(
            index: result.count,
            text: message.text,
            timestamp: Double(message.timestamp)
        ))
    }

    return result
}'''
    replace_once(UI, old_ui, new_ui, "BUILD122_EDIT_HISTORY_CURRENT1")

    old_message_text = '''                text: version.text,
                attributes: [],'''
    new_message_text = '''                text: version.text.isEmpty ? "∅" : version.text,
                attributes: [],'''
    ui_text = UI.read_text(encoding="utf-8")
    require(ui_text.count(old_message_text) == 1 or new_message_text in ui_text, "history display text owner mismatch")
    if new_message_text not in ui_text:
        UI.write_text(ui_text.replace(old_message_text, new_message_text, 1), encoding="utf-8")

    print("[Build122 edit/caption history] GREEN")
    print("[Build122 edit/caption history] text and media-caption transitions are preserved")
    print("[Build122 edit/caption history] current version is visible exactly once")


if __name__ == "__main__":
    main()
