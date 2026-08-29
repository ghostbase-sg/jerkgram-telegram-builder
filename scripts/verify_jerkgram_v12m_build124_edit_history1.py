#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
STATE = ROOT / "submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift"
MENU = ROOT / "submodules/TelegramUI/Sources/ChatInterfaceStateContextMenus.swift"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build124 edit history verify] " + message)


def main() -> None:
    state = STATE.read_text(encoding="utf-8")
    menu = MENU.read_text(encoding="utf-8")

    require("BUILD124_EDIT_EVENT_DATE1" in state, "edit-event date owner marker missing")
    require("previousVersionDate" not in state, "old previous-version timestamp owner survived")

    require("BUILD124_HISTORY_NO_CURRENT_DUP1" in menu, "current-version duplicate removal missing")
    require("BUILD122_EDIT_HISTORY_CURRENT1" not in menu, "Build122 live-current append survived")
    require("result.last?.text != message.text" not in menu, "live current message is still appended to edit history")

    require("BUILD124_HISTORY_NATIVE_DATE1" in menu, "legacy date fallback repair missing")
    require("let originalFallbackDate = Double(" in menu, "legacy history has no nonzero date fallback")
    require("timestamp: originalFallbackDate" in menu, "legacy snapshot does not carry date into synthetic message")
    require("timestamp: 0.0, entities: attribute.originalEntities" not in menu, "zero-timestamp history fallback survived")

    require("final class GhostBaseEditHistoryChatContents" in menu, "native chat history surface missing")
    require("timestamp: timestamp" in menu, "synthetic history messages do not carry version timestamp")
    require("mode: .standard(.previewing)" in menu, "read-only native chat presentation changed unexpectedly")

    print("[Build124 edit history verify] GREEN")
    print("[Build124 edit history verify] one edit event -> one historical snapshot; native chat timestamps preserved")


if __name__ == "__main__":
    main()
