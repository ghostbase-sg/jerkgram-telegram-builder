#!/usr/bin/env python3
from pathlib import Path
import plistlib
import sys
import zipfile

IPA = Path(sys.argv[1] if len(sys.argv) > 1 else "ghostbase-final/GhostBase.ipa")

EXPECTED_LEGACY_JG = {
    "JerkGramSteelReveal",
    "JerkGramSteelSolid",
    "JerkGramRustReveal",
    "JerkGramRustSolid",
    "JerkGramInkReveal",
    "JerkGramInkSolid",
    "JerkGramOliveReveal",
    "JerkGramOliveSolid",
}
EXPECTED_GLASS = {"JerkgramGlassReveal", "JerkgramGlassSolid"}
EXPECTED_STOCK = {
    "BlackIcon",
    "BlackClassicIcon",
    "BlackFilledIcon",
    "BlueIcon",
    "BlueClassicIcon",
    "BlueFilledIcon",
    "WhiteFilledIcon",
    "New1",
    "New2",
    "Premium",
    "PremiumBlack",
    "PremiumTurbo",
}


def require(condition, message):
    if not condition:
        raise RuntimeError("[verify Build111 final] " + message)


require(IPA.is_file(), f"IPA missing: {IPA}")
with zipfile.ZipFile(IPA, "r") as archive:
    names = archive.namelist()
    plist_paths = [
        name for name in names
        if name.startswith("Payload/")
        and name.endswith(".app/Info.plist")
        and name.count("/") == 2
    ]
    require(len(plist_paths) == 1, f"expected one main Info.plist: {plist_paths}")
    plist = plistlib.loads(archive.read(plist_paths[0]))
    app_root = plist_paths[0][:-len("Info.plist")]
    require(app_root + "Assets.car" in names, "Assets.car missing; Composer output not materialized")
    require(not any("JerkgramGlassReveal.alticon" in n or "JerkgramGlassSolid.alticon" in n for n in names), "Glass .alticon unexpectedly bundled")

require(plist.get("CFBundleIdentifier") == "ph.telegra.Telegraph", f"Bundle ID changed: {plist.get('CFBundleIdentifier')!r}")
require(plist.get("CFBundleDisplayName") == "Jerkgram", f"display name mismatch: {plist.get('CFBundleDisplayName')!r}")
require(plist.get("CFBundleName") == "Jerkgram", f"bundle name mismatch: {plist.get('CFBundleName')!r}")

icon_dicts = []
for key in ("CFBundleIcons", "CFBundleIcons~ipad"):
    value = plist.get(key)
    if isinstance(value, dict):
        icon_dicts.append((key, value))

require(icon_dicts, "CFBundleIcons dictionaries missing")
primary_names = set()
alternate_ids = set()
for key, icons in icon_dicts:
    primary = icons.get("CFBundlePrimaryIcon")
    if isinstance(primary, dict):
        name = primary.get("CFBundleIconName")
        if isinstance(name, str):
            primary_names.add(name)
    alternates = icons.get("CFBundleAlternateIcons")
    if isinstance(alternates, dict):
        alternate_ids.update(alternates.keys())
        missing_glass_here = EXPECTED_GLASS - set(alternates.keys())
        require(not missing_glass_here, f"{key} missing Composer alternates: {sorted(missing_glass_here)}")

require("Telegram" in primary_names, f"primary Composer icon is not Telegram: {sorted(primary_names)}")
require(not (EXPECTED_GLASS - alternate_ids), f"Glass alternate identifiers missing: {sorted(EXPECTED_GLASS - alternate_ids)}")
require(not (EXPECTED_LEGACY_JG - alternate_ids), f"legacy JerkGram alternates missing: {sorted(EXPECTED_LEGACY_JG - alternate_ids)}")
require(not (EXPECTED_STOCK - alternate_ids), f"stock Telegram alternates missing: {sorted(EXPECTED_STOCK - alternate_ids)}")

print("[verify Build111 final] GREEN")
print("CFBundleIdentifier: ph.telegra.Telegraph")
print("CFBundleDisplayName: Jerkgram")
print("Primary Composer icon: Telegram")
print("Composer alternates:", ", ".join(sorted(EXPECTED_GLASS)))
print("Legacy JerkGram alternates:", ", ".join(sorted(EXPECTED_LEGACY_JG)))
print("Stock Telegram alternates preserved:", len(EXPECTED_STOCK))
print("Assets.car: present")
