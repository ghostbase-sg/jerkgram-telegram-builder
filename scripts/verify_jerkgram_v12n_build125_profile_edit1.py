#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
FILES = (
    ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoHeaderSingleLineTextFieldNode.swift",
    ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoHeaderMultiLineTextFieldNode.swift",
)


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build125 profile edit verify] " + message)


def main() -> None:
    for path in FILES:
        text = path.read_text(encoding="utf-8")
        require(text.count("BUILD125_PROFILE_EDIT_GLASS_OWNER1") == 1, f"{path.name}: Build125 visual owner missing")
        require("GhostBaseGlassStyle.isEnabled" in text, f"{path.name}: profile Glass switch not used")
        require("GhostBaseProfileBlurSettings\n                .loadEnabled()" not in text, f"{path.name}: stale independent toggle survived")
        require("UIColor.white.withAlphaComponent(0.055)" in text, f"{path.name}: dark translucent tint missing")
        require("UIColor.black.withAlphaComponent(0.045)" in text, f"{path.name}: light translucent tint missing")
        require("itemBlocksBackgroundColor.withAlphaComponent" not in text, f"{path.name}: opaque list card survived")
        require("self.backgroundNode.isOpaque = false" in text, f"{path.name}: field remains opaque")
    print("[Build125 profile edit verify] GREEN")


if __name__ == "__main__":
    main()
