#!/usr/bin/env python3
from pathlib import Path
import os

ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
TARGET = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/Panes/PeerInfoListPaneNode.swift"
MARKER = "// MARK: Jerkgram v1.2N BUILD125_LINKS_LOCAL_CARD_BOUNDS1"

def require(value, message):
    if not value:
        raise RuntimeError("[Build125 Links bounds] " + message)

def patch_text(text):
    if MARKER in text:
        return text
    require(text.count("BUILD124_LINKS_INTRINSIC_MATERIAL1") == 1, "Build124 Links material owner missing")
    old = "height: max(1.0, self.listNode.bounds.size.height - distanceToTop - self.listNode.insets.bottom)"
    new = '''// MARK: Jerkgram v1.2N BUILD125_LINKS_LOCAL_CARD_BOUNDS1
                    // A Links material card must never inherit the full list viewport.
                    // It decorates the compact links header/content region only.
                    height: max(1.0, min(300.0, self.listNode.bounds.size.height - distanceToTop - self.listNode.insets.bottom))'''
    require(text.count(old) == 1, "full-viewport Links frame owner missing")
    return text.replace(old, new, 1)

def main():
    TARGET.write_text(patch_text(TARGET.read_text(encoding="utf-8")), encoding="utf-8")
    print("[Build125 Links bounds] GREEN")

if __name__ == "__main__":
    main()
