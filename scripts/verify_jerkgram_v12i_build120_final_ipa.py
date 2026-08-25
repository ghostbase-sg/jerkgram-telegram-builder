#!/usr/bin/env python3

from pathlib import Path
import plistlib
import sys
import tempfile
import zipfile


EXPECTED_BUILD = "120"
EXPECTED_DISPLAY = "Jerkgram"
EXPECTED_BUNDLE = "ph.telegra.Telegraph"
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
        raise RuntimeError("[Build120 final IPA verify] " + message)


def load_plist(path):
    with path.open("rb") as file:
        return plistlib.load(file)


def main():
    ipa = Path(
        sys.argv[1]
        if len(sys.argv) > 1
        else "work/swiftgram-src/ghostbase-final/GhostBase.ipa"
    ).resolve()
    require(ipa.is_file(), "IPA missing: " + str(ipa))

    with tempfile.TemporaryDirectory(prefix="jerkgram-build120-verify-") as directory:
        root = Path(directory)
        with zipfile.ZipFile(ipa, "r") as archive:
            archive.extractall(root)

        apps = list((root / "Payload").glob("*.app"))
        require(len(apps) == 1, "expected exactly one main app")
        app = apps[0]
        main = load_plist(app / "Info.plist")

        require(main.get("CFBundleDisplayName") == EXPECTED_DISPLAY, "CFBundleDisplayName is not Jerkgram")
        require(main.get("CFBundleName") == EXPECTED_DISPLAY, "CFBundleName is not Jerkgram")
        require(main.get("CFBundleIdentifier") == EXPECTED_BUNDLE, "public bundle identifier changed")
        require(str(main.get("CFBundleVersion")) == EXPECTED_BUILD, "embedded main CFBundleVersion is not 120")

        plugins = {path.name: path for path in (app / "PlugIns").glob("*.appex") if path.is_dir()}
        require(set(plugins) == EXPECTED_EXTENSIONS, "*.appex topology mismatch")
        for name, extension in sorted(plugins.items()):
            info = load_plist(extension / "Info.plist")
            require(str(info.get("CFBundleVersion")) == EXPECTED_BUILD, f"{name} CFBundleVersion is not 120")
            bundle_id = info.get("CFBundleIdentifier")
            require(isinstance(bundle_id, str) and bundle_id.startswith(EXPECTED_BUNDLE + "."), f"{name} public bundle identifier mismatch")

    print("[Build120 final IPA verify] GREEN")
    print("[Build120 final IPA verify] CFBundleDisplayName=Jerkgram")
    print("[Build120 final IPA verify] CFBundleVersion=120 in app + 6 extensions")


if __name__ == "__main__":
    main()
