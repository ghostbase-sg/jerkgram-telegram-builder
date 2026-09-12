#!/usr/bin/env python3
from pathlib import Path
import os

ROOT = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd()))).resolve()
ICON_ITEM = ROOT / "submodules/SettingsUI/Sources/Themes/ThemeSettingsAppIconItem.swift"
THEME = ROOT / "submodules/SettingsUI/Sources/Themes/ThemeSettingsController.swift"
APP = ROOT / "submodules/TelegramUI/Sources/AppDelegate.swift"
BUILD = ROOT / "Telegram/BUILD"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build140 premium icons verify] " + message)


for path in (ICON_ITEM, THEME, APP, BUILD):
    require(path.is_file(), "missing source file: " + str(path))

icon_item = ICON_ITEM.read_text(encoding="utf-8")
theme = THEME.read_text(encoding="utf-8")
app = APP.read_text(encoding="utf-8")
build = BUILD.read_text(encoding="utf-8")

require("locked: !item.isPremium && icon.isPremium" not in icon_item, "visual Premium lock still active")
require("locked: false" in icon_item, "unlocked app-icon visual state missing")
require("if icon.isPremium && !isPremium {" not in theme, "Premium redirect still active")
require(theme.count("if icon.isPremium && !isPremium && false {") == 1, "local app-icon unlock condition missing or duplicated")
require("requestSetAlternateIconName(icon.isDefault ? nil : icon.name" in theme, "alternate icon application path missing")

for row in (
    'PresentationAppIcon(name: "Premium", imageName: "Premium", isPremium: true)',
    'PresentationAppIcon(name: "PremiumTurbo", imageName: "PremiumTurbo", isPremium: true)',
    'PresentationAppIcon(name: "PremiumBlack", imageName: "PremiumBlack", isPremium: true)',
):
    require(row in app, "Premium icon metadata changed: " + row)

require('PresentationAppIcon(name: "JerkgramGlassReveal", imageName: "JerkgramGlassRevealPreview", isDefault: true)' in app, "JerkgramGlassReveal logical default missing")
require('primary_app_icon = "JerkgramGlassReveal"' in build, "JerkgramGlassReveal physical primary missing")

print("[Build140 premium icons verify] GREEN")
print("[Build140 premium icons verify] local icon selection unlocked; Premium metadata + Jerkgram default preserved")
