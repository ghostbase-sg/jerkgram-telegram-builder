#!/usr/bin/env python3
from pathlib import Path
import os

ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
TARGET = ROOT / "submodules/TelegramUI/Sources/ChatControllerForwardMessages.swift"

def main():
    text = TARGET.read_text(encoding="utf-8")
    marker = "BUILD125_PROTECTED_FORWARD_CACHE_FIRST1"
    if text.count(marker) != 1:
        raise RuntimeError("[Build125 protected cache verify] cache-first owner missing")
    start = text.index(marker)
    owner = text[start:text.index("private func jerkgramPortableForwardMessage", start)]
    if "waitUntilFetchStatus: false" not in owner or "if cachedData.isComplete" not in owner:
        raise RuntimeError("[Build125 protected cache verify] local completed-resource branch missing")
    if owner.index("if cachedData.isComplete") > owner.index("context.engine.resources.fetch"):
        raise RuntimeError("[Build125 protected cache verify] network fetch still precedes local cache")
    print("[Build125 protected cache verify] GREEN")

if __name__ == "__main__":
    main()
