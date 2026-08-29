#!/usr/bin/env python3
from pathlib import Path
import os

ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
TARGET = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/Panes/PeerInfoListPaneNode.swift"

def main():
    text = TARGET.read_text(encoding="utf-8")
    if text.count("BUILD125_LINKS_LOCAL_CARD_BOUNDS1") != 1:
        raise RuntimeError("[Build125 Links bounds verify] local card owner missing")
    if "min(300.0, self.listNode.bounds.size.height - distanceToTop - self.listNode.insets.bottom)" not in text:
        raise RuntimeError("[Build125 Links bounds verify] full list viewport is still used")
    print("[Build125 Links bounds verify] GREEN")

if __name__ == "__main__":
    main()
