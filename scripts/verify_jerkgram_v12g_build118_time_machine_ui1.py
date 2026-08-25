#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
BASE = ROOT / "submodules/TelegramUI/Components/Chat/ChatSearchNavigationContentNode/Sources"
BUILD = BASE.parent / "BUILD"


def require(value, message):
    if not value:
        raise RuntimeError("[verify Build118 Time Machine UI] " + message)


def main():
    node = (BASE / "ChatSearchNavigationContentNode.swift").read_text()
    controller = (BASE / "JerkgramTimeMachineController.swift").read_text()
    build = BUILD.read_text()
    require("jerkgramOpenTimeMachine" in node and "interaction.presentController" in node, "search route missing")
    require(node.index("self.view.addSubview(self.backgroundContainer)") < node.index("self.view.addSubview(self.jerkgramTimeMachineBackground)"), "Time Machine control is covered by background container")
    require("peerId: EnginePeer.Id(event.chatPeerId)" in controller, "message navigation peer-id owner mismatch")
    require("import PresentationDataUtils" in controller, "PresentationDataUtils import missing")
    require("loadNextPage" in controller and "timeMachineLoadMore" in controller, "bounded paging control missing")
    require("while let page" not in controller, "Time Machine still drains complete history eagerly")
    require("//submodules/PresentationDataUtils:PresentationDataUtils" in build, "PresentationDataUtils BUILD dependency missing")
    for token in ("deletedMessage", "editedMessage", "recoveredMedia", "senderPeerId", "JerkgramTextDiff.diff", "navigateToMessage", "event.eventId"):
        require(token in controller, "controller invariant missing: " + token)
    print("[verify Build118 Time Machine UI] GREEN: ordinary search entry, filters, author, exact diff and live/local navigation")


if __name__ == "__main__":
    main()
