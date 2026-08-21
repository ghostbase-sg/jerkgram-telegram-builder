#!/usr/bin/env python3
from pathlib import Path
import hashlib
import os
import re
import struct
import xml.etree.ElementTree as ET

ROOT = Path(
    os.environ.get(
        "JERKGRAM_SOURCE_ROOT",
        os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())),
    )
).resolve()

IOS = ROOT / "Telegram/Telegram-iOS"
BUILD = ROOT / "Telegram/BUILD"
APP = ROOT / "submodules/TelegramUI/Sources/AppDelegate.swift"
THEME = ROOT / "submodules/SettingsUI/Sources/Themes/ThemeSettingsController.swift"
ICON_ITEM = ROOT / "submodules/SettingsUI/Sources/Themes/ThemeSettingsAppIconItem.swift"
SETTINGS = ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
PANE_CONTAINER = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoPaneContainerNode.swift"

EXPECTED_ICON_JSON = "cf7c84b1ceef48a16c9ea2c193428417f99b80258752d7fcc14914f6b0ca4c89"
EXPECTED_OVAL = "30b7245c9edef107ea7520cdd958246fcc771fa0872bb2f6cd13ab2dc11cfffd"
EXPECTED_REVEAL_PLANE = "9dc83c22a01878aac9f8494c509a7862fdd1679d7e7f7f0026afc367d3a7e304"
EXPECTED_SOLID_PLANE = "bf53330c359bb661f93b86f292d48206a31027b107e7b92d274c8663d2ceb61a"
EXPECTED_REVEAL_PREVIEW = "60900a0dfe618efb8d4414e07a2f211206cbc76467fb5ddec0ef7669bbf0c77e"
EXPECTED_SOLID_PREVIEW = "6562cd0d2f23b57cf19d0ad133f395d586cd33a65ec7a4098fb476bc36ff9dd5"

LEGACY_JG_IDS = [
    "JerkGramSteelReveal",
    "JerkGramSteelSolid",
    "JerkGramRustReveal",
    "JerkGramRustSolid",
    "JerkGramInkReveal",
    "JerkGramInkSolid",
    "JerkGramOliveReveal",
    "JerkGramOliveSolid",
]


def require(condition, message):
    if not condition:
        raise RuntimeError("[verify Build111] " + message)


def read(path):
    require(path.is_file(), f"missing file: {path}")
    return path.read_text(encoding="utf-8")


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def png_size(path):
    data = path.read_bytes()[:24]
    require(len(data) >= 24 and data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR", f"invalid PNG: {path}")
    return struct.unpack(">II", data[16:24])


def plane_d(path):
    raw = path.read_text(encoding="utf-8")
    require("<image" not in raw and "<mask" not in raw and "<filter" not in raw, f"forbidden SVG element: {path}")
    root = ET.fromstring(raw)
    require(root.attrib.get("width") == "1024", f"width mismatch: {path}")
    require(root.attrib.get("height") == "1024", f"height mismatch: {path}")
    require(root.attrib.get("viewBox") == "0 0 1024 1024", f"viewBox mismatch: {path}")
    paths = [node for node in root.iter() if node.tag.split("}")[-1] == "path"]
    require(len(paths) == 1, f"Plane must have one path element: {path}")
    return paths[0].attrib.get("d", ""), paths[0].attrib.get("fill-rule")


build = read(BUILD)
app = read(APP)
theme = read(THEME)
icon_item = read(ICON_ITEM)
settings = read(SETTINGS)
pane_container = read(PANE_CONTAINER)

# Official Composer owner remains untouched and is primary again.
official = IOS / "Telegram.icon"
require(sha256(official / "icon.json") == EXPECTED_ICON_JSON, "Official Telegram icon.json changed")
require(sha256(official / "Assets/Oval.svg") == EXPECTED_OVAL, "Official Telegram Oval changed")

planes = {}
for icon_id, expected_plane in (
    ("JerkgramGlassReveal", EXPECTED_REVEAL_PLANE),
    ("JerkgramGlassSolid", EXPECTED_SOLID_PLANE),
):
    icon = IOS / f"{icon_id}.icon"
    require(icon.is_dir(), f"Composer icon missing: {icon_id}")
    require(sha256(icon / "icon.json") == EXPECTED_ICON_JSON, f"{icon_id} icon.json changed")
    require(sha256(icon / "Assets/Oval.svg") == EXPECTED_OVAL, f"{icon_id} Oval changed")
    require(sha256(icon / "Assets/Plane.svg") == expected_plane, f"{icon_id} Plane changed")
    require((icon / "icon.json").read_bytes() == (official / "icon.json").read_bytes(), f"{icon_id} icon.json not Official")
    require((icon / "Assets/Oval.svg").read_bytes() == (official / "Assets/Oval.svg").read_bytes(), f"{icon_id} Oval not Official")
    planes[icon_id] = plane_d(icon / "Assets/Plane.svg")

solid_d = planes["JerkgramGlassSolid"][0]
reveal_d = planes["JerkgramGlassReveal"][0]
require(reveal_d.startswith(solid_d), "Reveal/Solid outer geometry diverged")
require(len(reveal_d) > len(solid_d), "Reveal negative-space missing")
require(planes["JerkgramGlassReveal"][1] == "evenodd", "Reveal evenodd missing")

require(not (IOS / "JerkgramGlassReveal.alticon").exists(), "Reveal must not use .alticon")
require(not (IOS / "JerkgramGlassSolid.alticon").exists(), "Solid must not use .alticon")
require(not (IOS / "JerkGramSteelReveal.icon").exists(), "old Steel Reveal Composer primary survived")

preview_dir = IOS / "JerkgramGlassUIPreviews"
require(sha256(preview_dir / "JerkgramGlassRevealPreview.png") == EXPECTED_REVEAL_PREVIEW, "Reveal UI preview changed")
require(sha256(preview_dir / "JerkgramGlassSolidPreview.png") == EXPECTED_SOLID_PREVIEW, "Solid UI preview changed")
require(png_size(preview_dir / "JerkgramGlassRevealPreview.png") == (1024, 1024), "Reveal UI preview size mismatch")
require(png_size(preview_dir / "JerkgramGlassSolidPreview.png") == (1024, 1024), "Solid UI preview size mismatch")

composer = re.search(r'composer_icon_folders\s*=\s*\[(.*?)\]', build, re.S)
require(composer is not None, "composer_icon_folders missing")
composer_block = composer.group(1)
for icon_id in ("Telegram", "JerkgramGlassReveal", "JerkgramGlassSolid"):
    require(f'"{icon_id}"' in composer_block, f"Composer registration missing: {icon_id}")
require("JerkGramSteelReveal" not in composer_block, "Steel Reveal still in Composer list")
require('primary_app_icon = "Telegram"' in build, "primary_app_icon != Telegram")
require('name = "JerkgramGlassUIPreviews"' in build, "UI preview resource filegroup missing")
require('":JerkgramGlassUIPreviews"' in build, "UI preview filegroup not in app resources")

alt_start = build.find("alternate_icon_folders = [")
alt_end = build.find("\n]", alt_start)
require(alt_start >= 0 and alt_end > alt_start, "alternate_icon_folders missing")
alt_block = build[alt_start:alt_end]
for icon_id in LEGACY_JG_IDS:
    require(f'"{icon_id}"' in alt_block, f"legacy JerkGram alternate missing: {icon_id}")
require("JerkgramGlassReveal" not in alt_block and "JerkgramGlassSolid" not in alt_block, "Glass Composer icon leaked into legacy alternate list")

steel_alt = IOS / "JerkGramSteelReveal.alticon"
require(steel_alt.is_dir(), "Steel Reveal .alticon missing")
steel_pngs = sorted(steel_alt.glob("*.png"))
require(steel_pngs, "Steel Reveal .alticon has no PNGs")
require(all(p.name.startswith("JerkGramSteelReveal") for p in steel_pngs), "Steel Reveal .alticon has foreign flattened resource names")

# Runtime selection: nil = Official Telegram primary; all ten Jerkgram entries remain selectable.
require('PresentationAppIcon(name: "BlueIcon", imageName: "BlueIcon", isDefault: true)' in app, "Telegram primary/default mapping missing")
require('PresentationAppIcon(name: "JerkGramSteelReveal", imageName: "JerkGramSteelReveal", isDefault: true)' not in app, "Steel Reveal still logical default")
for icon_id in LEGACY_JG_IDS:
    require(f'name: "{icon_id}"' in app, f"runtime legacy icon missing: {icon_id}")
require('name: "JerkgramGlassReveal", imageName: "JerkgramGlassRevealPreview"' in app, "Glass Reveal runtime mapping missing")
require('name: "JerkgramGlassSolid", imageName: "JerkgramGlassSolidPreview"' in app, "Glass Solid runtime mapping missing")

# Appearance crash hardening: explicit entry types, monotonic unique stable IDs, no content-dependent IDs.
require("BUILD111_SAFE_ICON_ENTRIES1" in theme, "safe icon entry marker missing")
require("case jerkgramIconHeader" in theme and "case jerkgramIconItem" in theme, "dedicated Jerkgram icon entry cases missing")
require("9100" not in theme and "9101" not in theme, "Build110 stable-id hack survived")
for token in (
    "case .jerkgramIconHeader:\n            return 12",
    "case .jerkgramIconItem:\n            return 13",
    "case .iconHeader:\n            return 14",
    "case .iconItem:\n            return 15",
):
    require(token in theme, f"stable-id mapping missing: {token}")
require(".jerkgramIconHeader(" in theme and ".jerkgramIconItem(" in theme, "Jerkgram Appearance block missing")
require('hasPrefix("Jerkgram")' in theme, "Composer Glass icons not included in Jerkgram section")
require('currentAppIcon?.name ?? "Blue"' in theme, "primary fallback not restored")

require('case "JerkgramGlassReveal":' in icon_item and 'name = "Glass Reveal"' in icon_item, "Glass Reveal UI label missing")
require('case "JerkgramGlassSolid":' in icon_item and 'name = "Glass Solid"' in icon_item, "Glass Solid UI label missing")

require('"Переносимый ответ на удалённое"' not in settings, "long portable reply title survived")
require('"Переносимый ответ"' in settings, "short portable reply title missing")
require("BUILD111_PORTABLE_REPLY_TITLE1" in settings, "portable reply title marker missing")

require("BUILD111_LIST_PANE_READABILITY1" in pane_container, "Files/Links/Voice/Music pane readability marker missing")
require("BUILD111_LIST_PANE_READABILITY1" in pane_container, "pane readability helper missing")
require("alpha: isDark ? 0.26 : 0.18" in pane_container, "pane readability alpha mismatch")

require("jerkgram.runtime.namespaceMigration.v1" in app, "Build109 namespace migration lost")

print("[verify Build111] GREEN")
print("  Telegram.icon = primary Composer icon")
print("  JerkgramGlassReveal/Solid = native Composer alternates")
print("  8 previous JerkGram variants = legacy alternates")
print("  Glass system icons have no source .alticon or system PNG pipeline")
print("  Appearance uses dedicated stable entries")
print("  portable reply title shortened")
print("  Files/Links/Voice/Music share pane-wide adaptive translucent surface")
