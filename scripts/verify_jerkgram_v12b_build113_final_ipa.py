#!/usr/bin/env python3
from pathlib import Path
import plistlib
import struct
import sys
import tempfile
import zipfile

IPA = Path(sys.argv[1] if len(sys.argv) > 1 else "ghostbase-final/GhostBase.ipa").resolve()
BASE = "app.pumpkin6584.lion7414"
PRIMARY = "JerkgramGlassReveal"
FORBIDDEN_GROUP = b"group.4a348a9b186b700c.10"

EXTENSIONS = {
    "BroadcastUploadExtension.appex": (BASE + ".BroadcastUpload", "com.apple.broadcast-services-upload"),
    "IntentsExtension.appex": (BASE + ".SiriIntents", "com.apple.intents-service"),
    "NotificationContentExtension.appex": (BASE + ".NotificationContent", "com.apple.usernotifications.content-extension"),
    "NotificationServiceExtensionv1.appex": (BASE + ".NotificationService", "com.apple.usernotifications.service"),
    "ShareExtension.appex": (BASE + ".Share", "com.apple.share-services"),
    "WidgetExtension.appex": (BASE + ".Widget", "com.apple.widgetkit-extension"),
}

def require(v, msg):
    if not v:
        raise RuntimeError("[verify Build113 final] " + msg)

def load_plist(path):
    with open(path, "rb") as f:
        return plistlib.load(f)

def code_signature_sizes_thin(data):
    if len(data) < 32:
        return []
    magic = data[:4]
    if magic == b"\xcf\xfa\xed\xfe":
        endian, header = "<", 32
    elif magic == b"\xfe\xed\xfa\xcf":
        endian, header = ">", 32
    elif magic == b"\xce\xfa\xed\xfe":
        endian, header = "<", 28
    elif magic == b"\xfe\xed\xfa\xce":
        endian, header = ">", 28
    else:
        return None
    ncmds = struct.unpack_from(endian + "I", data, 16)[0]
    off = header
    sizes = []
    for _ in range(ncmds):
        require(off + 8 <= len(data), "truncated Mach-O load commands")
        cmd, cmdsize = struct.unpack_from(endian + "II", data, off)
        require(cmdsize >= 8 and off + cmdsize <= len(data), "invalid Mach-O load command")
        if cmd == 0x1D:
            require(cmdsize >= 16, "short LC_CODE_SIGNATURE")
            _, size = struct.unpack_from(endian + "II", data, off + 8)
            sizes.append(size)
        off += cmdsize
    return sizes

def code_signature_sizes(data):
    thin = code_signature_sizes_thin(data)
    if thin is not None:
        return thin
    if len(data) < 8:
        return []
    magic_be = struct.unpack_from(">I", data, 0)[0]
    if magic_be not in (0xCAFEBABE, 0xCAFEBABF):
        return []
    is64 = magic_be == 0xCAFEBABF
    nfat = struct.unpack_from(">I", data, 4)[0]
    off = 8
    sizes = []
    for _ in range(nfat):
        if is64:
            require(off + 32 <= len(data), "truncated fat64 header")
            slice_off, slice_size = struct.unpack_from(">QQ", data, off + 8)
            off += 32
        else:
            require(off + 20 <= len(data), "truncated fat header")
            slice_off, slice_size = struct.unpack_from(">II", data, off + 8)
            off += 20
        sizes.extend(code_signature_sizes(data[slice_off:slice_off + slice_size]))
    return sizes

require(IPA.is_file(), f"IPA missing: {IPA}")

with tempfile.TemporaryDirectory(prefix="build113-final-") as td:
    root = Path(td)
    with zipfile.ZipFile(IPA, "r") as z:
        for info in z.infolist():
            require(FORBIDDEN_GROUP not in z.read(info), f"forbidden AppGroup .10 in {info.filename}")
        z.extractall(root)

    apps = list((root / "Payload").glob("*.app"))
    require(len(apps) == 1, f"expected one app, got {[x.name for x in apps]}")
    app = apps[0]
    info = load_plist(app / "Info.plist")

    require(info.get("CFBundleIdentifier") == BASE, f"main BID mismatch: {info.get('CFBundleIdentifier')!r}")
    require(info.get("CFBundleDisplayName") == "Jerkgram", "display name mismatch")
    require(info.get("CFBundleName") == "Jerkgram", "bundle name mismatch")
    require(not (app / "embedded.mobileprovision").exists(), "main embedded.mobileprovision present")
    require(not (app / "_CodeSignature").exists(), "main _CodeSignature present")

    main_exe = info.get("CFBundleExecutable")
    require(isinstance(main_exe, str) and (app / main_exe).is_file(), "main executable missing")
    sizes = code_signature_sizes((app / main_exe).read_bytes())
    require(not any(sizes), f"main has nonempty LC_CODE_SIGNATURE: {sizes}")

    for key in ("CFBundleIcons", "CFBundleIcons~ipad"):
        icons = info.get(key)
        require(isinstance(icons, dict), f"{key} missing")
        primary = icons.get("CFBundlePrimaryIcon")
        require(isinstance(primary, dict) and primary.get("CFBundleIconName") == PRIMARY, f"{key} primary != {PRIMARY}: {primary}")
        alternates = icons.get("CFBundleAlternateIcons")
        require(isinstance(alternates, dict), f"{key} alternates missing")
        require(PRIMARY not in alternates, f"{key} primary duplicated as alternate")
        for name in ("JerkgramGlassSolid", "Telegram"):
            require(name in alternates, f"{key} missing alternate {name}")

    plugins = app / "PlugIns"
    require(plugins.is_dir(), "PlugIns missing")
    present = {x.name: x for x in plugins.glob("*.appex") if x.is_dir()}
    require(set(present) == set(EXTENSIONS), f"extension set mismatch: {sorted(present)}")

    for name, (expected_bid, expected_point) in EXTENSIONS.items():
        ext = present[name]
        ext_info = load_plist(ext / "Info.plist")
        require(ext_info.get("CFBundleIdentifier") == expected_bid, f"{name} BID mismatch: {ext_info.get('CFBundleIdentifier')!r}")
        ns = ext_info.get("NSExtension")
        require(isinstance(ns, dict), f"{name} NSExtension missing")
        require(ns.get("NSExtensionPointIdentifier") == expected_point, f"{name} extension point mismatch: {ns.get('NSExtensionPointIdentifier')!r}")
        exe = ext_info.get("CFBundleExecutable")
        require(isinstance(exe, str) and (ext / exe).is_file(), f"{name} executable missing")
        require(not (ext / "embedded.mobileprovision").exists(), f"{name} embedded.mobileprovision present")
        require(not (ext / "_CodeSignature").exists(), f"{name} _CodeSignature present")
        sizes = code_signature_sizes((ext / exe).read_bytes())
        require(not any(sizes), f"{name} has nonempty LC_CODE_SIGNATURE: {sizes}")

    bns = load_plist(present["BroadcastUploadExtension.appex"] / "Info.plist")["NSExtension"]
    require("BroadcastUploadSampleHandler" in str(bns.get("NSExtensionPrincipalClass")), "Broadcast principal mismatch")
    process_mode = bns.get("RPBroadcastProcessMode")
    require(
        process_mode == "RPBroadcastProcessModeSampleBuffer",
        f"Broadcast process mode mismatch: {process_mode!r}",
    )

print("[verify Build113 final] GREEN")
print("[verify Build113 final] coherent main/extension namespace:", BASE)
print("[verify Build113 final] 6/6 extensions, unsigned and profile-free")
print("[verify Build113 final] primary icon:", PRIMARY)
