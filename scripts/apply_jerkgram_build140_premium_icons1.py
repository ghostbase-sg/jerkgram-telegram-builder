#!/usr/bin/env python3
from pathlib import Path
import os

ROOT = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd()))).resolve()
ICON_ITEM = ROOT / "submodules/SettingsUI/Sources/Themes/ThemeSettingsAppIconItem.swift"
THEME = ROOT / "submodules/SettingsUI/Sources/Themes/ThemeSettingsController.swift"
APP = ROOT / "submodules/TelegramUI/Sources/AppDelegate.swift"
BUILD = ROOT / "Telegram/BUILD"

VISUAL_LOCK_OLD = "locked: !item.isPremium && icon.isPremium"
VISUAL_LOCK_NEW = "locked: false"
PREMIUM_BRANCH_OLD = "if icon.isPremium && !isPremium {"
PREMIUM_BRANCH_NEW = "if icon.isPremium && !isPremium && false {"

PREMIUM_ICON_ROWS = (
    'PresentationAppIcon(name: "Premium", imageName: "Premium", isPremium: true)',
    'PresentationAppIcon(name: "PremiumTurbo", imageName: "PremiumTurbo", isPremium: true)',
    'PresentationAppIcon(name: "PremiumBlack", imageName: "PremiumBlack", isPremium: true)',
)
JERKGRAM_DEFAULT_ROW = 'PresentationAppIcon(name: "JerkgramGlassReveal", imageName: "JerkgramGlassRevealPreview", isDefault: true)'
JERKGRAM_PRIMARY_BUILD = 'primary_app_icon = "JerkgramGlassReveal"'


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build140 premium icons] " + message)


def patch_icon_item(text: str) -> str:
    old_count = text.count(VISUAL_LOCK_OLD)
    if old_count:
        require(old_count == 1, f"visual premium lock anchor count = {old_count}")
        text = text.replace(VISUAL_LOCK_OLD, VISUAL_LOCK_NEW, 1)
    require(VISUAL_LOCK_OLD not in text, "visual premium lock survived")
    require(text.count(VISUAL_LOCK_NEW) >= 1, "unlocked visual state missing")
    return text


def patch_icon_selection(text: str) -> str:
    old_count = text.count(PREMIUM_BRANCH_OLD)
    if old_count:
        require(old_count == 1, f"premium redirect anchor count = {old_count}")
        text = text.replace(PREMIUM_BRANCH_OLD, PREMIUM_BRANCH_NEW, 1)
    require(PREMIUM_BRANCH_OLD not in text, "Premium app-icon redirect survived")
    require(text.count(PREMIUM_BRANCH_NEW) == 1, "unlocked selection branch missing or duplicated")
    require(text.count("requestSetAlternateIconName") >= 1, "alternate icon application call missing")
    return text


def patch_app_delegate_contract(text: str) -> str:
    for row in PREMIUM_ICON_ROWS:
        require(row in text, "Telegram Premium icon metadata changed: " + row)
    return text


def main() -> None:
    for path in (ICON_ITEM, THEME, APP, BUILD):
        require(path.is_file(), "missing source file: " + str(path))

    icon_item = patch_icon_item(ICON_ITEM.read_text(encoding="utf-8"))
    theme = patch_icon_selection(THEME.read_text(encoding="utf-8"))
    app = patch_app_delegate_contract(APP.read_text(encoding="utf-8"))
    build = BUILD.read_text(encoding="utf-8")

    require(JERKGRAM_DEFAULT_ROW in app, "JerkgramGlassReveal logical default missing")
    require(JERKGRAM_PRIMARY_BUILD in build, "JerkgramGlassReveal physical primary missing")

    ICON_ITEM.write_text(icon_item, encoding="utf-8")
    THEME.write_text(theme, encoding="utf-8")

    print("[Build140 premium icons] Telegram Premium app icons unlocked locally")
    print("[Build140 premium icons] Premium metadata preserved; JerkgramGlassReveal remains default")


if __name__ == "__main__":
    main()
