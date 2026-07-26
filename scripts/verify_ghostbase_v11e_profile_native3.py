#!/usr/bin/env python3
import os
from pathlib import Path
root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
base = root / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources"
files = {
    "backdrop": base / "GhostBaseProfileBackdropNode.swift",
    "section": base / "GhostBaseColdGlassSectionView.swift",
    "hub": base / "GhostBaseProfileHubItem.swift",
    "screen": base / "PeerInfoScreen.swift",
    "header": base / "PeerInfoHeaderNode.swift",
    "container": base / "PeerInfoScreenItemSectionContainerNode.swift",
    "items": base / "PeerInfoProfileItems.swift",
}
texts = {key: path.read_text(encoding="utf-8") for key, path in files.items()}
for value in ["HorizontalTabsComponent(", "layout: .fit", "PROFILEHUBNATIVE3"]:
    if value not in texts["hub"]:
        raise SystemExit(f"[VERIFY V11E PROFILE] native tabs missing {value}")
for forbidden in ["TabSelectorComponent", "GlassBackgroundView", "innerColor:", "drawHierarchy", "snapshotView"]:
    if forbidden in texts["hub"] + texts["backdrop"] + texts["section"]:
        raise SystemExit(f"[VERIFY V11E PROFILE] forbidden custom/heavy artifact {forbidden}")
if "containerLayoutUpdated" in texts["backdrop"]:
    raise SystemExit("[VERIFY V11E PROFILE] backdrop must never re-enter controller layout")
if "self.addSubnode(self.ghostBaseProfileBackdropNode)" not in texts["screen"]:
    raise SystemExit("[VERIFY V11E PROFILE] passive backdrop hierarchy missing")
if "frame: CGRect(origin: .zero, size: layout.size)" not in texts["screen"]:
    raise SystemExit("[VERIFY V11E PROFILE] full-screen layout size missing")
if "peer-wallpaper-user" not in texts["backdrop"] or "avatar-" not in texts["backdrop"] or "global-fallback" not in texts["backdrop"]:
    raise SystemExit("[VERIFY V11E PROFILE] wallpaper -> avatar -> global fallback chain missing")
if "GhostBaseColdGlassSectionView" not in texts["container"]:
    raise SystemExit("[VERIFY V11E PROFILE] safe section material missing")
if "emojiStatus" not in texts["header"]:
    raise SystemExit("[VERIFY V11E PROFILE] stock emoji status path was lost")
for forbidden in ["PROFILESELECTOR2", "SECTIONGLASS2", "PROFILEBACKDROP2", "PROFILEGLASS1 inline hub"]:
    joined = "\n".join(texts.values())
    if forbidden in joined:
        raise SystemExit(f"[VERIFY V11E PROFILE] rejected implementation remains: {forbidden}")
if "История и сведения" not in texts["items"]:
    raise SystemExit("[VERIFY V11E PROFILE] logical hub item missing")
print("[VERIFY V11E PROFILENATIVE3] OK")
