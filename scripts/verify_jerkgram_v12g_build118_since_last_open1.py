#!/usr/bin/env python3
from pathlib import Path
import os

ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()

def require(value, message):
    if not value: raise RuntimeError("[verify Build118 since last opening] " + message)

def main():
    chat = ROOT / "submodules/TelegramUI/Sources/ChatController.swift"
    engine = ROOT / "submodules/JerkgramCore/Sources/JerkgramTimeMachineIndex.swift"
    require(chat.is_file() and engine.is_file(), "owners missing")
    chat_text, engine_text = chat.read_text(), engine.read_text()
    for token in ("BUILD118_SINCE_LAST_OPEN1", "Set(changes.eventIds)", "changesSinceLastOpening", "position: .top"):
        require(token in chat_text, "chat invariant missing: " + token)
    require("JerkgramCaptureRecorder.readyIndexRecords(" in chat_text, "bounded shared ready-index query missing")
    require("eventStore.events(accountPeerId:" not in chat_text, "full event-log read remains in chat opening")
    require("if previousValue == nil" in engine_text, "first-visit baseline missing")
    print("[verify Build118 since last opening] GREEN: bounded per-account/chat ID summary present")

if __name__ == "__main__": main()
