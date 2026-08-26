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
        raise RuntimeError("[Build122 edit/caption verify] " + message)


def main() -> None:
    core = CORE.read_text(encoding="utf-8")
    ui = UI.read_text(encoding="utf-8")
    require(core.count("BUILD122_EDIT_CAPTION_HISTORY1") == 1, "capture marker count != 1")
    require("previousMessage.text != message.text {" in core, "text/caption change gate missing")
    require("previousMessage.text != message.text,\n                       !previousMessage.text.isEmpty" not in core, "empty caption transition still discarded")
    require("date: previousVersionDate" in core, "previous version timestamp not used")
    require("previousText: previousMessage.text" in core, "previous caption missing from event payload")
    require(ui.count("BUILD122_EDIT_HISTORY_CURRENT1") == 1, "current version marker count != 1")
    require("result.last?.text != message.text" in ui, "current version deduplication missing")
    require('text: version.text.isEmpty ? "∅" : version.text' in ui, "empty-caption history placeholder missing")
    print("[Build122 edit/caption verify] GREEN")
    print("[Build122 edit/caption verify] body and caption edits include empty transitions + current version")


if __name__ == "__main__":
    main()
