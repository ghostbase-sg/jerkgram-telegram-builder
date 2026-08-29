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
        raise RuntimeError("[Build124 profile edit glass verify] " + message)


def main() -> None:
    for path in FILES:
        text = path.read_text(encoding="utf-8")
        require("BUILD124_PROFILE_EDIT_SURFACE1" in text, f"{path.name}: translucent edit surface missing")
        require("BUILD124_PROFILE_EDIT_RUNTIME_SURFACE1" in text, f"{path.name}: final edit field visual owner was not updated")
        require("GhostBaseGlassStyle.isEnabled" in text, f"{path.name}: Glass owner missing")
        require("? 0.12" in text and ": 0.10" in text, f"{path.name}: final translucency alpha missing")
        require(": presentationData.theme.list.itemBlocksBackgroundColor" in text, f"{path.name}: stock Telegram fallback missing")
        require("self.backgroundNode.backgroundColor = presentationData.theme.list.itemBlocksBackgroundColor" not in text, f"{path.name}: opaque direct owner survived")

    print("[Build124 profile edit glass verify] GREEN")
    print("[Build124 profile edit glass verify] both profile edit field owners obey Glass on/off contract")


if __name__ == "__main__":
    main()
