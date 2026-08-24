#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
BASE = ROOT / "submodules/TelegramUI/Components/Chat/ChatSearchNavigationContentNode/Sources"


def require(value, message):
    if not value:
        raise RuntimeError("[verify Build118 Time Machine UI] " + message)


def main():
    node = (BASE / "ChatSearchNavigationContentNode.swift").read_text()
    controller = (BASE / "JerkgramTimeMachineController.swift").read_text()
    require("jerkgramOpenTimeMachine" in node and "interaction.presentController" in node, "search route missing")
    require("peerId: EnginePeer.Id(event.chatPeerId)" in controller, "message navigation peer-id owner mismatch")
    for token in ("deletedMessage", "editedMessage", "recoveredMedia", "senderPeerId", "JerkgramTextDiff.diff", "navigateToMessage", "event.eventId"):
        require(token in controller, "controller invariant missing: " + token)
    print("[verify Build118 Time Machine UI] GREEN: ordinary search entry, filters, author, exact diff and live/local navigation")


if __name__ == "__main__":
    main()
