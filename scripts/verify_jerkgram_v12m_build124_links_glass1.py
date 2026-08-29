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
    require("UIVisualEffectView" in owner, "Links-local material view missing")
    require(".systemMaterialDark" in owner and ".systemMaterialLight" in owner, "theme-aware Links material missing")
    require("let linksFrame = CGRect" in owner, "bounded Links-card frame missing")
    require(
        "visibleContentOffset" in owner
        and "self.listNode.bounds.size.width" in owner
        and "self.listNode.bounds.size.height" in owner
        and "self.listNode.insets.bottom" in owner,
        "Links-card frame is not tied to the protocol-safe list geometry",
    )
    require("visibleBottomContentOffset" not in owner, "Links overlay calls an unavailable list API")
    require("0.26 * lightness" not in owner, "old whole-pane dimming formula survived")
    require("self.backgroundColor = .clear" in owner and "self.listNode.backgroundColor = .clear" in owner, "whole-pane fallback is not transparent")

    if geometry:
        require("self.ghostBaseGlassEnabled && !self.jerkgramLinksReadabilityEnabled" in geometry, "Build123 non-Links plate policy changed")
        require("else if !self.jerkgramLinksReadabilityEnabled" in geometry, "Links card is hidden by the old viewport branch")

    print("[Build124 Links glass verify] GREEN")
    print("[Build124 Links glass verify] Links material is bounded to the loaded list; pane surface remains transparent")


if __name__ == "__main__":
    main()
