#!/usr/bin/env python3
from pathlib import Path
import os
import plistlib
import sys
import tempfile
import zipfile

BASE = "app.pumpkin6584.lion7414"
DISPLAY = "Jerkgram"
PRIMARY = "JerkgramGlassReveal"
REQUIRED_ALTERNATES = {
    "JerkgramGlassSolid",
    "Telegram",
    "JerkGramSteelReveal",
    "JerkGramSteelSolid",
    "JerkGramRustReveal",
    "JerkGramRustSolid",
    "JerkGramInkReveal",
    "JerkGramInkSolid",
    "JerkGramOliveReveal",
    "JerkGramOliveSolid",
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

def require(v, msg):
    if not v:
        raise RuntimeError("[Build113 finalizer] " + msg)

ipa = Path(sys.argv[1] if len(sys.argv) > 1 else "ghostbase-final/GhostBase.ipa").resolve()
require(ipa.is_file(), f"IPA missing: {ipa}")

with zipfile.ZipFile(ipa, "r") as zin:
    infos = zin.infolist()
    mains = [
        x for x in infos
        if x.filename.startswith("Payload/")
        and x.filename.endswith(".app/Info.plist")
        and x.filename.count("/") == 2
    ]
    require(len(mains) == 1, f"expected one main Info.plist, got {[x.filename for x in mains]}")
    target = mains[0]
    raw = zin.read(target)
    fmt = plistlib.FMT_BINARY if raw.startswith(b"bplist") else plistlib.FMT_XML
    plist = plistlib.loads(raw)

    require(plist.get("CFBundleIdentifier") == BASE, f"main Bundle ID must stay internal before ESign: {plist.get('CFBundleIdentifier')!r}")
    plist["CFBundleDisplayName"] = DISPLAY
    plist["CFBundleName"] = DISPLAY

    for key in ("CFBundleIcons", "CFBundleIcons~ipad"):
        icons = plist.get(key)
        require(isinstance(icons, dict), f"{key} missing")
        primary = icons.setdefault("CFBundlePrimaryIcon", {})
        require(isinstance(primary, dict), f"{key}.CFBundlePrimaryIcon malformed")
        primary["CFBundleIconName"] = PRIMARY

        alternates = icons.setdefault("CFBundleAlternateIcons", {})
        require(isinstance(alternates, dict), f"{key}.CFBundleAlternateIcons malformed")
        alternates.pop(PRIMARY, None)
        for name in sorted(REQUIRED_ALTERNATES):
            entry = alternates.get(name)
            if not isinstance(entry, dict):
                entry = {}
                alternates[name] = entry
            entry["CFBundleIconName"] = name

    patched = plistlib.dumps(plist, fmt=fmt, sort_keys=False)

    fd, tmp_name = tempfile.mkstemp(prefix=ipa.name + ".build113.", suffix=".tmp", dir=str(ipa.parent))
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        with zipfile.ZipFile(tmp, "w") as zout:
            for item in infos:
                data = patched if item.filename == target.filename else zin.read(item)
                zout.writestr(item, data)
        os.replace(tmp, ipa)
    finally:
        tmp.unlink(missing_ok=True)

print("[Build113 finalizer] main Bundle ID preserved:", BASE)
print("[Build113 finalizer] display name:", DISPLAY)
print("[Build113 finalizer] primary icon:", PRIMARY)
