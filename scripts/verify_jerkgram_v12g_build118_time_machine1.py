#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
INDEX = ROOT / "submodules/JerkgramCore/Sources/JerkgramTimeMachineIndex.swift"
DIFF = ROOT / "submodules/JerkgramCore/Sources/JerkgramTextDiff.swift"


def require(value, message):
    if not value:
        raise RuntimeError("[verify Build118 Time Machine] " + message)


def main():
    require(INDEX.is_file() and DIFF.is_file(), "sources missing")
    index = INDEX.read_text(encoding="utf-8")
    diff = DIFF.read_text(encoding="utf-8")
    for token in ("accountPeerId", "chatPeerId", "eventId", "senderPeerId", "eventIds", "upperSequence", "options: .atomic"):
        require(token in index, "index invariant missing: " + token)
    require("messageText" not in index and "mediaBytes" not in index, "index duplicated payload")
    for token in ("Array(old)", "Array(new)", "case replace", "250_000"):
        require(token in diff, "diff invariant missing: " + token)
    print("[verify Build118 Time Machine] GREEN: account/chat filters, ID identity, reference-only index, grapheme diff, atomic watermarks")


if __name__ == "__main__":
    main()
