#!/usr/bin/env python3
from pathlib import Path
import os

ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
SETTINGS = ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"

def require(value, message):
    if not value: raise RuntimeError("[verify Build118 About cards] " + message)

def main():
    text = SETTINGS.read_text()
    for token in ("BUILD118_ABOUT_CHANNEL_CARDS1", 'username: "JerkgramApp"', 'username: "JerkgramCommunity"', "height: .peerList", "Build: 118", "aroundMessageHistoryViewForLocation"):
        require(token in text, "missing " + token)
    print("[verify Build118 About cards] GREEN: two live, larger native cards")

if __name__ == "__main__": main()
