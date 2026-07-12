#!/usr/bin/env python3
from pathlib import Path
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "work/swiftgram-src"

SOURCE_DIR = (
    ROOT
    / "scripts"
    / "assets"
    / "ghostbase_settings_icons"
)

TELEGRAM_UI_DIR = (
    SRC
    / "submodules"
    / "TelegramUI"
)

CATALOG_DIR = (
    TELEGRAM_UI_DIR
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


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(
            f"[v1.0R ASSETS] {message}"
        )


require(
    SOURCE_DIR.is_dir(),
    f"missing source icons: {SOURCE_DIR}"
)

require(
    TELEGRAM_UI_DIR.is_dir(),
    f"missing TelegramUI source: {TELEGRAM_UI_DIR}"
)

CATALOG_DIR.mkdir(
    parents=True,
    exist_ok=True
)

root_contents = CATALOG_DIR / "Contents.json"

if not root_contents.is_file():
    root_contents.write_text(
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
    image_set = (
        CATALOG_DIR
        / f"{asset_name}.imageset"
    )

    image_set.mkdir(
        parents=True,
        exist_ok=True
    )

    images = []

    for scale, suffix in (
        ("1x", ""),
        ("2x", "@2x"),
        ("3x", "@3x"),
    ):
        source_file = (
            SOURCE_DIR
            / f"{source_name}{suffix}.png"
        )

        require(
            source_file.is_file(),
            f"missing PNG: {source_file}"
        )

        target_name = (
            f"{asset_name}{suffix}.png"
        )

        shutil.copy2(
            source_file,
            image_set / target_name
        )

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

installed = list(
    CATALOG_DIR.glob(
        "GhostBase*.imageset"
    )
)

require(
    len(installed) == 8,
    f"expected 8 imagesets, got {len(installed)}"
)

print("[v1.0R ASSETS] installed 8 TelegramUI imagesets")
print(f"[v1.0R ASSETS] catalog: {CATALOG_DIR}")
