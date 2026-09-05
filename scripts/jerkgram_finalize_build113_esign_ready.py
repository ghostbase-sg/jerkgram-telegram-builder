#!/usr/bin/env python3
from pathlib import Path
import os
import plistlib
import sys
import tempfile
import zipfile

BASE = "app.pumpkin6584.lion7414"
PROD_BASE = "com.jerkgram.ios"
TEST_BASE = "com.pixidev.jerkgram.test"
DISPLAY = "Jerkgram"
PRIMARY = "JerkgramGlassReveal"
EXTENSION_SUFFIXES = {
    "BroadcastUploadExtension.appex": "BroadcastUpload",
    "IntentsExtension.appex": "SiriIntents",
    "NotificationContentExtension.appex": "NotificationContent",
    "NotificationServiceExtensionv1.appex": "NotificationService",
    "ShareExtension.appex": "Share",
    "WidgetExtension.appex": "Widget",
}
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

    incoming_base = plist.get("CFBundleIdentifier")
    require(
        incoming_base in (BASE, PROD_BASE, TEST_BASE),
        f"unexpected main Bundle ID before ESign compatibility stage: {incoming_base!r}",
    )

    # Build132 compiles with its real InstalledIdentity. Build113/114 are retained
    # historical packaging stages and expect the old internal namespace, so bridge
    # main + extensions temporarily and let the final Build132 stage restore the
    # release InstalledIdentity after legacy packaging is complete.
    plist["CFBundleIdentifier"] = BASE
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

    replacements = {
        target.filename: plistlib.dumps(plist, fmt=fmt, sort_keys=False),
    }

    app_prefix = target.filename[:-len("Info.plist")]
    for appex_name, suffix in EXTENSION_SUFFIXES.items():
        member_name = app_prefix + f"PlugIns/{appex_name}/Info.plist"
        matches = [item for item in infos if item.filename == member_name]
        require(len(matches) == 1, f"expected one {appex_name} Info.plist, got {len(matches)}")
        item = matches[0]
        ext_raw = zin.read(item)
        ext_fmt = plistlib.FMT_BINARY if ext_raw.startswith(b"bplist") else plistlib.FMT_XML
        ext_plist = plistlib.loads(ext_raw)
        actual_bid = ext_plist.get("CFBundleIdentifier")
        allowed = {f"{BASE}.{suffix}", f"{PROD_BASE}.{suffix}", f"{TEST_BASE}.{suffix}"}
        require(actual_bid in allowed, f"{appex_name} unexpected Bundle ID before legacy packaging: {actual_bid!r}")
        ext_plist["CFBundleIdentifier"] = f"{BASE}.{suffix}"
        replacements[member_name] = plistlib.dumps(ext_plist, fmt=ext_fmt, sort_keys=False)

    fd, tmp_name = tempfile.mkstemp(prefix=ipa.name + ".build113.", suffix=".tmp", dir=str(ipa.parent))
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        with zipfile.ZipFile(tmp, "w") as zout:
            for item in infos:
                data = replacements.get(item.filename)
                if data is None:
                    data = zin.read(item)
                zout.writestr(item, data)
        os.replace(tmp, ipa)
    finally:
        tmp.unlink(missing_ok=True)

print("[Build113 finalizer] legacy packaging namespace:", BASE)
print("[Build113 finalizer] incoming InstalledIdentity:", incoming_base)
print("[Build113 finalizer] display name:", DISPLAY)
print("[Build113 finalizer] primary icon:", PRIMARY)
