#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
GROUPS = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/Panes/PeerInfoGroupsInCommonPaneNode.swift"
LINKS = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/Panes/PeerInfoListPaneNode.swift"
PROFILE_ITEMS = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoProfileItems.swift"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build124 profile regressions] " + message)


def main() -> None:
    groups = GROUPS.read_text(encoding="utf-8")
    links = LINKS.read_text(encoding="utf-8")
    profile_items = PROFILE_ITEMS.read_text(encoding="utf-8")

    require("BUILD123_COMMON_GROUPS_SURFACE1" in groups, "Common Groups surface owner missing")
    require("ghostBaseGlassEffectView.isHidden = false" in groups, "Common Groups material was hidden")
    require("ghostBaseGlassTintView.backgroundColor" in groups, "Common Groups tint missing")
    require("listBackgroundView.isHidden = true" in groups and "listMaskView.isHidden = true" in groups, "Common Groups opaque plate returned")

    require("BUILD123_LINKS_INTRINSIC_GLASS1" in links, "Links geometry owner missing")
    require("self.ghostBaseGlassEnabled && !self.jerkgramLinksReadabilityEnabled" in links, "Links geometry policy changed")
    require("self.jerkgramLinksReadabilityEnabled ? .zero : self.glassBackgroundView.frame" in links, "Links viewport plate regression")
    require("BUILD124_LINKS_INTRINSIC_MATERIAL1" in links, "Links material owner missing")

    require("BUILD123_REMOVE_PRIVATE_LINK_PROBE1" in profile_items, "private-link removal owner missing")
    require("PRIVATELINK1" not in profile_items, "experimental private invite owner returned")

    print("[Build124 profile regressions] GREEN")


if __name__ == "__main__":
    main()
