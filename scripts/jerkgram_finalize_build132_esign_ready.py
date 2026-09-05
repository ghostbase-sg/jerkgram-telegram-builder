#!/usr/bin/env python3
from pathlib import Path
import os
import plistlib
import shutil
import subprocess
import sys
import tempfile
import zipfile

LEGACY_BASE = "ph.telegra.Telegraph"
PROD_BASE = "com.jerkgram.ios"
TEST_BASE = "com.pixidev.jerkgram.test"
PUBLIC_TEAM = "C67CF9S4VU"
PUBLIC_GROUP = "group.ph.telegra.Telegraph"
DISPLAY = "Jerkgram"
TELEGRAM_BASE_VERSION = "12.9.2"
BUILD = "132"

EXTENSIONS = {
    "BroadcastUploadExtension.appex": ("BroadcastUpload", "keychain"),
    "IntentsExtension.appex": ("SiriIntents", "keychain"),
    "NotificationContentExtension.appex": ("NotificationContent", "aps"),
    "NotificationServiceExtensionv1.appex": ("NotificationService", "aps"),
    "ShareExtension.appex": ("Share", "aps"),
    "WidgetExtension.appex": ("Widget", "keychain"),
}


def require(value, message):
    if not value:
        raise RuntimeError("[Build132 finalizer] " + message)


def target_base():
    variant = os.environ.get("JERKGRAM_BUNDLE_VARIANT", "prod").strip().lower()
    if variant == "prod":
        return variant, PROD_BASE
    if variant == "test":
        return variant, TEST_BASE
    raise RuntimeError(f"[Build132 finalizer] unsupported JERKGRAM_BUNDLE_VARIANT: {variant!r}")


def load_plist(path):
    with path.open("rb") as f:
        return plistlib.load(f)


def save_plist(path, value):
    original = path.read_bytes()
    fmt = plistlib.FMT_BINARY if original.startswith(b"bplist") else plistlib.FMT_XML
    path.write_bytes(plistlib.dumps(value, fmt=fmt, sort_keys=False))


def carrier_entitlements(bundle_id, kind):
    value = {
        "application-identifier": f"{PUBLIC_TEAM}.{bundle_id}",
        "com.apple.security.application-groups": [PUBLIC_GROUP],
        "get-task-allow": False,
    }
    if kind == "main":
        value["aps-environment"] = "production"
    elif kind == "keychain":
        value["com.apple.developer.team-identifier"] = PUBLIC_TEAM
        value["keychain-access-groups"] = [f"{PUBLIC_TEAM}.*", "com.apple.token"]
    elif kind == "aps":
        value["aps-environment"] = "production"
    else:
        raise RuntimeError(f"[Build132 finalizer] unknown entitlement class: {kind}")
    return value


def sign_entitlement_carrier(executable, entitlements, temp_root):
    codesign = shutil.which("codesign")
    require(codesign is not None, "codesign missing; Build132 finalizer must run on macOS CI")
    plist_path = temp_root / (executable.name + ".build132.entitlements.plist")
    plist_path.write_bytes(plistlib.dumps(entitlements, fmt=plistlib.FMT_XML, sort_keys=False))
    result = subprocess.run(
        [
            codesign,
            "--force",
            "--sign", "-",
            "--timestamp=none",
            "--generate-entitlement-der",
            "--entitlements", str(plist_path),
            str(executable),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    require(
        result.returncode == 0,
        f"ad-hoc carrier signing failed for {executable}:\n{result.stdout}\n{result.stderr}",
    )


def main():
    ipa = Path(sys.argv[1] if len(sys.argv) > 1 else "ghostbase-final/GhostBase.ipa").resolve()
    require(ipa.is_file(), f"IPA missing: {ipa}")
    variant, base = target_base()

    with tempfile.TemporaryDirectory(prefix="build132-finalizer-") as td:
        root = Path(td)
        with zipfile.ZipFile(ipa, "r") as archive:
            infos = archive.infolist()
            archive.extractall(root)

        apps = list((root / "Payload").glob("*.app"))
        require(len(apps) == 1, f"expected one app, got {[x.name for x in apps]}")
        app = apps[0]
        main_info_path = app / "Info.plist"
        require(main_info_path.is_file(), "main Info.plist missing")
        main_info = load_plist(main_info_path)
        current_main = main_info.get("CFBundleIdentifier")
        require(current_main in (LEGACY_BASE, base), f"unexpected main BID before Build132 finalization: {current_main!r}")

        main_info["CFBundleIdentifier"] = base
        main_info["CFBundleName"] = DISPLAY
        main_info["CFBundleDisplayName"] = DISPLAY
        main_info["CFBundleShortVersionString"] = TELEGRAM_BASE_VERSION
        main_info["CFBundleVersion"] = BUILD
        save_plist(main_info_path, main_info)

        main_exe_name = main_info.get("CFBundleExecutable")
        require(isinstance(main_exe_name, str) and main_exe_name, "main executable key missing")
        main_exe = app / main_exe_name
        require(main_exe.is_file(), "main executable missing")
        sign_entitlement_carrier(main_exe, carrier_entitlements(base, "main"), root)

        plugins = app / "PlugIns"
        require(plugins.is_dir(), "PlugIns missing")
        present = {path.name: path for path in plugins.glob("*.appex") if path.is_dir()}
        require(set(present) == set(EXTENSIONS), f"extension set mismatch: {sorted(present)}")

        for name, (suffix, kind) in EXTENSIONS.items():
            extension = present[name]
            info_path = extension / "Info.plist"
            info = load_plist(info_path)
            expected_legacy = f"{LEGACY_BASE}.{suffix}"
            expected_target = f"{base}.{suffix}"
            current = info.get("CFBundleIdentifier")
            require(current in (expected_legacy, expected_target), f"{name} unexpected BID before Build132 finalization: {current!r}")
            info["CFBundleIdentifier"] = expected_target
            info["CFBundleName"] = DISPLAY
            info["CFBundleDisplayName"] = DISPLAY
            info["CFBundleShortVersionString"] = TELEGRAM_BASE_VERSION
            info["CFBundleVersion"] = BUILD
            save_plist(info_path, info)

            exe_name = info.get("CFBundleExecutable")
            require(isinstance(exe_name, str) and exe_name, f"{name} executable key missing")
            executable = extension / exe_name
            require(executable.is_file(), f"{name} executable missing")
            sign_entitlement_carrier(executable, carrier_entitlements(expected_target, kind), root)

        fd, temp_name = tempfile.mkstemp(prefix=ipa.name + ".build132.", suffix=".tmp", dir=str(ipa.parent))
        os.close(fd)
        temporary = Path(temp_name)
        try:
            with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as output:
                for item in infos:
                    source = root / item.filename
                    output.writestr(item, b"" if item.is_dir() else source.read_bytes())
            os.replace(temporary, ipa)
        finally:
            temporary.unlink(missing_ok=True)

    print(f"[Build132 finalizer] GREEN: variant={variant} main={base}")
    print(f"[Build132 finalizer] coherent main + 6 extension namespace; CFBundleVersion={BUILD}; CFBundleShortVersionString={TELEGRAM_BASE_VERSION}")


if __name__ == "__main__":
    main()
