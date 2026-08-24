#!/usr/bin/env python3
from pathlib import Path
import os

ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()

def require(value, message):
    if not value: raise RuntimeError("[verify Build118 glass] " + message)

def main():
    files = [
        ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoScreenItemSectionContainerNode.swift",
        ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/Panes/PeerInfoListPaneNode.swift",
        ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoVisualMediaPaneNode/Sources/PeerInfoVisualMediaPaneNode.swift",
    ]
    for path in files: require(path.is_file(), "missing " + str(path))
    text = "\n".join(path.read_text() for path in files)
    for token in ("BUILD118_GLASS1", "withAlphaComponent(0.075)", "withAlphaComponent(0.035)", "cornerRadius: 16.0", "ghostBaseGlassEnabled"):
        require(token in text, "missing " + token)
    print("[verify Build118 glass] GREEN: reference material and stock fallback present")

if __name__ == "__main__": main()
