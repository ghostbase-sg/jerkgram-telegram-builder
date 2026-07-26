#!/usr/bin/env python3
import os
from pathlib import Path
root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
base = root / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources"
checks = {
    base / "GhostBaseProfileHubItem.swift": ["GlassBackgroundView", "TabSelectorComponent", "style: enabled ? .glass", "chevron.up", "chevron.down"],
    base / "PeerInfoScreen.swift": ["PROFILEBACKDROP2", "cached.wallpaper", "ghostBaseCaptureAvatarBackdrop", "UIBlurEffect(style: .systemMaterialDark)", "presentationData.chatWallpaper", "ghostBaseGlassTintDidChange", "NSProcessInfoPowerStateDidChange"],
    base / "PeerInfoScreenItemSectionContainerNode.swift": ["SECTIONGLASS2", "GlassBackgroundView", "exact final material size", "ComponentTransition(transition)"],
    base / "PeerInfoHeaderNode.swift": ["HEADERGLASS2", "contentButtonBackgroundColor = tint", "backgroundCoverView.alpha = GhostBaseGlassStyle.isEnabled ? 0.0 : 1.0"],
    base / "PeerInfoProfileItems.swift": ["PROFILESELECTOR2 one native glass block", "metrics moved into Сведения"],
}
for path, markers in checks.items():
    text = path.read_text(encoding="utf-8")
    for marker in markers:
        if marker not in text: raise SystemExit(f"[VERIFY V11D PROFILE] {path.name}: missing {marker}")
profile = (base / "PeerInfoProfileItems.swift").read_text(encoding="utf-8")
for forbidden in ["PROFILEHUB2 inline rows", "PROFILEGLASS1 inline hub", 'label: "id:', 'label: "dc:']:
    if forbidden in profile: raise SystemExit(f"[VERIFY V11D PROFILE] rejected UI remains: {forbidden}")
item = (base / "GhostBaseProfileHubItem.swift").read_text(encoding="utf-8")
if "UIScrollView()" in item or "tabButtons" in item:
    raise SystemExit("[VERIFY V11D PROFILE] custom button selector remains")
print("[VERIFY V11D PROFILE] OK")
