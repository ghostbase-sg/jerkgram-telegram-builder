#!/usr/bin/env python3
from pathlib import Path
import os

ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
DURATION = ROOT / "submodules/TelegramUI/Components/Chat/ChatInstantVideoMessageDurationNode/Sources/ChatInstantVideoMessageDurationNode.swift"
INSTANT = ROOT / "submodules/TelegramUI/Components/Chat/ChatMessageInteractiveInstantVideoNode/Sources/ChatMessageInteractiveInstantVideoNode.swift"

def require(value, message):
    if not value:
        raise RuntimeError("[Build125 circle viewed verify] " + message)

def main():
    duration = DURATION.read_text(encoding="utf-8")
    instant = INSTANT.read_text(encoding="utf-8")
    require(duration.count("BUILD125_CIRCLE_VIEWED_CHECK1") == 1, "duration viewed-check owner missing")
    require("public var showsViewedCheck: Bool = false" in duration, "duration viewed-check state missing")
    require("else if parameters.showsViewedCheck" in duration, "duration check renderer missing")
    require(instant.count("BUILD125_CIRCLE_VIEWED_CHECK1") == 1, "instant-video viewed-check owner missing")
    require("durationNode.showsViewedCheck = jerkgramOutgoingOneTimeCircleViewed" in instant, "outgoing consumed bit is not connected to visual check")
    print("[Build125 circle viewed verify] GREEN")

if __name__ == "__main__":
    main()
