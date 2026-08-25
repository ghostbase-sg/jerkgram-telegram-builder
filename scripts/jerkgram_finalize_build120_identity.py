#!/usr/bin/env python3

from pathlib import Path
import os
import plistlib
import sys
import tempfile
import zipfile


BUILD = "120"
DISPLAY = "Jerkgram"
PUBLIC_BUNDLE = "ph.telegra.Telegraph"
EXPECTED_EXTENSIONS = {
    "BroadcastUploadExtension.appex",
    "IntentsExtension.appex",
    "NotificationContentExtension.appex",
    "NotificationServiceExtensionv1.appex",
    "ShareExtension.appex",
    "WidgetExtension.appex",
}


def require(value, message):
    if not value:
        raise RuntimeError("[Build120 identity] " + message)


def load_plist(path):
    with path.open("rb") as file:
        return plistlib.load(file)


def save_plist(path, value):
    original = path.read_bytes()
    fmt = plistlib.FMT_BINARY if original.startswith(b"bplist") else plistlib.FMT_XML
    path.write_bytes(plistlib.dumps(value, fmt=fmt, sort_keys=False))


def main():
    ipa = Path(
        sys.argv[1]
        if len(sys.argv) > 1
        else "work/swiftgram-src/ghostbase-final/GhostBase.ipa"
    ).resolve()
    require(ipa.is_file(), "final public/resign-ready IPA missing: " + str(ipa))

    with tempfile.TemporaryDirectory(prefix="jerkgram-build120-identity-") as directory:
        root = Path(directory)
        with zipfile.ZipFile(ipa, "r") as archive:
            infos = archive.infolist()
            archive.extractall(root)

        apps = list((root / "Payload").glob("*.app"))
        require(len(apps) == 1, "expected exactly one main .app")
        app = apps[0]
        main_info_path = app / "Info.plist"
        require(main_info_path.is_file(), "main Info.plist missing")

        main_info = load_plist(main_info_path)
        require(main_info.get("CFBundleDisplayName") == DISPLAY, "public display identity missing")
        require(main_info.get("CFBundleIdentifier") == PUBLIC_BUNDLE, "public bundle identity missing")

        plugins = {path.name: path for path in (app / "PlugIns").glob("*.appex") if path.is_dir()}
        require(set(plugins) == EXPECTED_EXTENSIONS, "extension topology mismatch before Build120 stamping")

        plist_paths = []
        for info_path in app.rglob("Info.plist"):
            if info_path.parent == app or info_path.parent.suffix == ".appex":
                plist_paths.append(info_path)
        require(len(plist_paths) == 1 + len(EXPECTED_EXTENSIONS), "main/extension Info.plist count mismatch")

        for info_path in plist_paths:
            info = load_plist(info_path)
            info["CFBundleVersion"] = BUILD
            if info_path == main_info_path:
                info["CFBundleName"] = DISPLAY
                info["CFBundleDisplayName"] = DISPLAY
            save_plist(info_path, info)

        fd, temp_name = tempfile.mkstemp(
            prefix=ipa.name + ".build120.",
            suffix=".tmp",
            dir=str(ipa.parent),
        )
        os.close(fd)
        temp = Path(temp_name)
        try:
            with zipfile.ZipFile(temp, "w") as output:
                for info in infos:
                    source = root / info.filename
                    if info.is_dir():
                        output.writestr(info, b"")
                    else:
                        output.writestr(info, source.read_bytes())
            os.replace(temp, ipa)
        finally:
            if temp.exists():
                temp.unlink()

    print("[Build120 identity] GREEN")
    print("[Build120 identity] stamped CFBundleVersion=120 in main app and all extensions")
    print("[Build120 identity] public/resign-ready topology preserved")


if __name__ == "__main__":
    main()
