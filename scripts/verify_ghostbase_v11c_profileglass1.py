#!/usr/bin/env python3
import os
from pathlib import Path

root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
base = root / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen"
profile = (base / "Sources/PeerInfoProfileItems.swift").read_text(encoding="utf-8")
screen = (base / "Sources/PeerInfoScreen.swift").read_text(encoding="utf-8")
item_path = base / "Sources/GhostBaseProfileHubItem.swift"
item = item_path.read_text(encoding="utf-8") if item_path.exists() else ""
section = (base / "Sources/PeerInfoScreenItemSectionContainerNode.swift").read_text(encoding="utf-8")
build = (base / "BUILD").read_text(encoding="utf-8")

checks = {
    "one inline hub item": profile.count("GhostBaseProfileHubItem(") == 1,
    "old vertical hub removed": "PROFILEHUB2 inline rows" not in profile and "9911210 + tab.rawValue" not in profile,
    "horizontal scroll selector": "UIScrollView" in item and "tabsScrollView" in item and "tabButtons" in item,
    "tab titles from model": "tabTitles: GhostBaseProfileHubTab.allCases.map" in profile,
    "chevron down/up": '"chevron.up"' in item and '"chevron.down"' in item,
    "same expanding card": "isExpanded" in item and "return 58.0 + 44.0" in item,
    "live status separate": "data.status?.text" in profile and "История переходов" in profile,
    "wallpaper node": "createWallpaperBackgroundNode" in screen and "presentationData.chatWallpaper" in screen,
    "single wallpaper backdrop": screen.count("createWallpaperBackgroundNode(") == 1,
    "no per-cell blur": "UIVisualEffectView" not in item and "UIBlurEffect" not in item,
    "cold sections": "GhostBaseGlassStyle.coldFillColor" in section,
    "wallpaper dependency": "//submodules/WallpaperBackgroundNode" in build,
}
# The tab labels live in PeerInfoProfileItems.swift, not duplicated in the view source.
checks["five exact tabs"] = all(f'case .{case}: return "{title}"' in profile for case, title in [
    ("history", "История"), ("gifts", "Подарки"), ("online", "Онлайн"), ("channel", "Канал"), ("info", "Сведения")
])
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("PROFILEGLASS1 VERIFY FAILED: " + ", ".join(failed))
print("PROFILEGLASS1 VERIFY OK")
