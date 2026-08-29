#!/usr/bin/env python3
from pathlib import Path
import os

ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
TARGET = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/Panes/PeerInfoListPaneNode.swift"
MARKER = "// MARK: Jerkgram v1.2N BUILD125_LINKS_REMOVE_VIEWPORT_CARD2"

def require(value, message):
    if not value:
        raise RuntimeError("[Build125 Links bounds] " + message)

def patch_text(text):
    if MARKER in text:
        return text
    require(text.count("BUILD124_LINKS_INTRINSIC_MATERIAL1") == 1, "Build124 Links material owner missing")
    old = "height: max(1.0, self.listNode.bounds.size.height - distanceToTop - self.listNode.insets.bottom)"
    new = '''// MARK: Jerkgram v1.2N BUILD125_LINKS_LOCAL_CARD_BOUNDS1
                    // MARK: Jerkgram v1.2N BUILD125_LINKS_REMOVE_VIEWPORT_CARD2
                    // This owner sits behind *every* ChatHistory cell; it cannot
                    // be used as a per-link glass card. Keeping it visible turns
                    // a variable-length list into one giant dark rectangle.
                    height: 1.0'''
    if old not in text:
        old = "height: max(1.0, min(300.0, self.listNode.bounds.size.height - distanceToTop - self.listNode.insets.bottom))"
    require(text.count(old) == 1, "viewport Links frame owner missing")
    return text.replace(old, new, 1)

def main():
    TARGET.write_text(patch_text(TARGET.read_text(encoding="utf-8")), encoding="utf-8")
    print("[Build125 Links bounds] GREEN")

if __name__ == "__main__":
    main()
