#!/usr/bin/env python3
from pathlib import Path
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]

SOURCE_DIR = (
    ROOT
    / "scripts"
    / "assets"
    / "ghostbase_settings_icons"
)

CATALOG_DIR = (
    ROOT
    / "work"
    / "swiftgram-src"
    / "Swiftgram"
    / "SGSettingsUI"
    / "Images.xcassets"
)

ICONS = {
    "GhostBaseHome": "ghostbase_home",
    "GhostBaseGhostMode": "ghost_mode",
    "GhostBaseMessages": "messages",
    "GhostBaseProtectedContent": "protected_content",
    "GhostBaseMediaStories": "media_stories",
    "GhostBaseAppearance": "appearance",
    "GhostBaseDebugResearch": "debug_research",
    "GhostBaseAbout": "about",
}

if not SOURCE_DIR.is_dir():
    raise RuntimeError(
        f"[v1.0R ASSETS] missing source directory: {SOURCE_DIR}"
    )

SG_SETTINGS_BUILD = CATALOG_DIR.parent / "BUILD"
TELEGRAM_BUILD = (
    ROOT
    / "work"
    / "swiftgram-src"
    / "Telegram"
    / "BUILD"
)

if not SG_SETTINGS_BUILD.is_file():
    raise RuntimeError(
        f"[v1.0R ASSETS] missing SGSettingsUI BUILD: {SG_SETTINGS_BUILD}"
    )

if not TELEGRAM_BUILD.is_file():
    raise RuntimeError(
        f"[v1.0R ASSETS] missing Telegram BUILD: {TELEGRAM_BUILD}"
    )

if 'name = "SGUIAssets"' not in SG_SETTINGS_BUILD.read_text(
    encoding="utf-8"
):
    raise RuntimeError(
        "[v1.0R ASSETS] SGUIAssets filegroup missing"
    )

if "//Swiftgram/SGSettingsUI:SGUIAssets" not in TELEGRAM_BUILD.read_text(
    encoding="utf-8"
):
    raise RuntimeError(
        "[v1.0R ASSETS] SGUIAssets not connected to Telegram resources"
    )

CATALOG_DIR.mkdir(
    parents=True,
    exist_ok=True
)

catalog_contents = CATALOG_DIR / "Contents.json"

if not catalog_contents.is_file():
    catalog_contents.write_text(
        json.dumps(
            {
                "info": {
                    "author": "xcode",
                    "version": 1,
                }
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

for asset_name, source_name in ICONS.items():
    image_set = CATALOG_DIR / f"{asset_name}.imageset"
    image_set.mkdir(parents=True, exist_ok=True)

    images = []

    for scale, suffix in (
        ("1x", ""),
        ("2x", "@2x"),
        ("3x", "@3x"),
    ):
        source_file = SOURCE_DIR / f"{source_name}{suffix}.png"
        target_name = f"{asset_name}{suffix}.png"
        target_file = image_set / target_name

        if not source_file.is_file():
            raise RuntimeError(
                f"[v1.0R ASSETS] missing PNG: {source_file}"
            )

        shutil.copy2(source_file, target_file)

        images.append({
            "filename": target_name,
            "idiom": "universal",
            "scale": scale,
        })

    contents = {
        "images": images,
        "info": {
            "author": "xcode",
            "version": 1,
        },
    }

    (image_set / "Contents.json").write_text(
        json.dumps(contents, indent=2) + "\n",
        encoding="utf-8",
    )

print(f"[v1.0R ASSETS] installed {len(ICONS)} imagesets")
print(f"[v1.0R ASSETS] catalog: {CATALOG_DIR}")
