#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
LIST = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/Panes/PeerInfoListPaneNode.swift"
MARKER = "// MARK: Jerkgram v1.2M BUILD124_LINKS_INTRINSIC_MATERIAL1"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build124 Links glass verify] " + message)


def main() -> None:
    text = LIST.read_text(encoding="utf-8")
    require(text.count(MARKER) == 1, "intrinsic Links material owner missing or duplicated")
    owner_start = text.index(MARKER)
    geometry_marker = "BUILD123_LINKS_INTRINSIC_GLASS1"
    geometry_start = text.find(geometry_marker, owner_start)
    owner = text[owner_start:] if geometry_start < 0 else text[owner_start:geometry_start]
    geometry = "" if geometry_start < 0 else text[geometry_start:]

    require("if self.ghostBaseGlassEnabled" in owner, "Links material is not gated by GBGlass")
    require("0.20 + 0.06 * lightness" in owner, "dark material alpha floor missing")
    require("0.14 + 0.04 * lightness" in owner, "light material alpha floor missing")
    require("presentationData.theme.overallDarkAppearance ? 0.0 : 1.0" in owner, "theme-aware neutral material missing")
    require("0.26 * lightness" not in owner, "old zero-alpha Links formula survived")
    require("self.backgroundColor = .clear" in owner and "self.listNode.backgroundColor = .clear" in owner, "GBGlass-off Telegram fallback missing")

    if geometry:
        require("self.ghostBaseGlassEnabled && !self.jerkgramLinksReadabilityEnabled" in geometry, "Build123 non-Links plate policy changed")
        require("self.jerkgramLinksReadabilityEnabled ? .zero" in geometry, "Links viewport plate was restored")

    print("[Build124 Links glass verify] GREEN")
    print("[Build124 Links glass verify] Links has intrinsic non-zero material; viewport plate remains disabled")


if __name__ == "__main__":
    main()
