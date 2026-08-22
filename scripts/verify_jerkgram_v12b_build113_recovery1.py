#!/usr/bin/env python3
from pathlib import Path
import os

ROOT = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd()))).resolve()

THEME = ROOT / "submodules/SettingsUI/Sources/Themes/ThemeSettingsController.swift"
BUILD = ROOT / "Telegram/BUILD"
APP = ROOT / "submodules/TelegramUI/Sources/AppDelegate.swift"
AUTH = ROOT / "submodules/TelegramCore/Sources/Authorization.swift"
SHARED = ROOT / "submodules/TelegramUI/Sources/SharedAccountContext.swift"

def require(v, msg):
    if not v:
        raise RuntimeError("[verify Build113 recovery] " + msg)

theme = THEME.read_text(encoding="utf-8")
build = BUILD.read_text(encoding="utf-8")
app = APP.read_text(encoding="utf-8")

require("jerkgramIconHeader" not in theme, "custom jerkgramIconHeader survived")
require("jerkgramIconItem" not in theme, "custom jerkgramIconItem survived")
require("BUILD110_ICON_STABLE_IDS1" not in theme, "Build110 stable-id hack survived")
require("BUILD111_SAFE_ICON_ENTRIES1" not in theme, "Build111 custom enum marker survived")
require("BUILD111_ICON_SECTIONS1" not in theme, "Build111 split icon sections survived")
require(
    'currentAppIconName.set(currentAppIcon?.name ?? "JerkgramGlassReveal")' in theme,
    "Glass Reveal fallback missing",
)
require(
    '    primary_app_icon = "JerkgramGlassReveal",' in build,
    "primary_app_icon != JerkgramGlassReveal",
)
require(
    'PresentationAppIcon(name: "JerkgramGlassReveal", imageName: "JerkgramGlassRevealPreview", isDefault: true),' in app,
    "Glass Reveal runtime default missing",
)
require(
    'PresentationAppIcon(name: "BlueIcon", imageName: "BlueIcon", isDefault: true),' not in app,
    "BlueIcon is still logical default",
)

for path in (AUTH, SHARED):
    if path.is_file():
        text = path.read_text(encoding="utf-8", errors="ignore")
        require("GhostBase.BotMulti1" not in text, f"release BOTMULTI1 diagnostics survived in {path.name}")

print("[verify Build113 recovery] GREEN")
