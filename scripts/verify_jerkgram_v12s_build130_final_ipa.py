#!/usr/bin/env python3

import os
from pathlib import Path
import plistlib
import sys
import tempfile
import zipfile

import verify_jerkgram_v12s_build128_final_ipa as base


PROD_BASE = "com.jerkgram.ios"
TEST_BASE = "com.pixidev.jerkgram.test"
EXPECTED_DISPLAY_VERSION = "12.9.2"
EXPECTED_BUILD = "132"
EXTENSION_SUFFIXES = {
    "BroadcastUploadExtension.appex": "BroadcastUpload",
    "IntentsExtension.appex": "SiriIntents",
    "NotificationContentExtension.appex": "NotificationContent",
    "NotificationServiceExtensionv1.appex": "NotificationService",
    "ShareExtension.appex": "Share",
    "WidgetExtension.appex": "Widget",
}


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build132 final IPA verify] " + message)


def expected_base() -> str:
    variant = os.environ.get("JERKGRAM_BUNDLE_VARIANT", "prod").strip().lower()
    if variant == "prod":
        return PROD_BASE
    if variant == "test":
        return TEST_BASE
    raise RuntimeError(f"[Build132 final IPA verify] unsupported JERKGRAM_BUNDLE_VARIANT: {variant!r}")


def main() -> None:
    ipa = Path(sys.argv[1] if len(sys.argv) > 1 else "work/swiftgram-src/ghostbase-final/GhostBase.ipa").resolve()
    bundle_base = expected_base()

    # Reuse the existing Build128 package verifier, but point its shared Build122
    # identity expectations at the final Build132 namespace/version.
    base.base.EXPECTED_BUILD = EXPECTED_BUILD
    base.base.EXPECTED_BUNDLE = bundle_base
    base.main()

    with tempfile.TemporaryDirectory(prefix="jerkgram-build132-verify-") as directory:
        root = Path(directory)
        with zipfile.ZipFile(ipa, "r") as archive:
            names = [item.filename for item in archive.infolist()]
            require(not any(name.endswith("/embedded.mobileprovision") for name in names), "embedded.mobileprovision survived raw IPA")
            require(not any("/_CodeSignature/" in name for name in names), "bundle CodeResources signature survived raw IPA")
            archive.extractall(root)

        apps = list((root / "Payload").glob("*.app"))
        require(len(apps) == 1, "expected exactly one main app")
        app = apps[0]
        main = plistlib.loads((app / "Info.plist").read_bytes())
        require(main.get("CFBundleIdentifier") == bundle_base, "final main InstalledIdentity mismatch")
        require(str(main.get("CFBundleVersion")) == EXPECTED_BUILD, "main CFBundleVersion != 132")
        require(main.get("CFBundleShortVersionString") == EXPECTED_DISPLAY_VERSION, "main signer-visible version != 12.9.2")

        plugins = {path.name: path for path in (app / "PlugIns").glob("*.appex") if path.is_dir()}
        require(set(plugins) == set(EXTENSION_SUFFIXES), "extension topology mismatch")
        for name, suffix in EXTENSION_SUFFIXES.items():
            info = plistlib.loads((plugins[name] / "Info.plist").read_bytes())
            require(info.get("CFBundleIdentifier") == f"{bundle_base}.{suffix}", f"{name} final BID mismatch")
            require(str(info.get("CFBundleVersion")) == EXPECTED_BUILD, f"{name} CFBundleVersion != 132")
            require(info.get("CFBundleShortVersionString") == EXPECTED_DISPLAY_VERSION, f"{name} signer-visible version != 12.9.2")

    print("[Build132 final IPA verify] GREEN")
    print(f"[Build132 final IPA verify] main={bundle_base}; build={EXPECTED_BUILD}; signer version={EXPECTED_DISPLAY_VERSION}")


if __name__ == "__main__":
    main()
