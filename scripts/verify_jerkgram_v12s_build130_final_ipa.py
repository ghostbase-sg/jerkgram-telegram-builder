#!/usr/bin/env python3

from pathlib import Path
import plistlib
import sys
import tempfile
import zipfile

import verify_jerkgram_v12s_build128_final_ipa as base


base.base.EXPECTED_BUILD = "130"
EXPECTED_DISPLAY_VERSION = "1.0.0"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build130 final IPA verify] " + message)


def main() -> None:
    ipa = Path(sys.argv[1] if len(sys.argv) > 1 else "work/swiftgram-src/ghostbase-final/GhostBase.ipa").resolve()
    base.main()
    with tempfile.TemporaryDirectory(prefix="jerkgram-build130-verify-") as directory:
        root = Path(directory)
        with zipfile.ZipFile(ipa, "r") as archive:
            archive.extractall(root)
        apps = list((root / "Payload").glob("*.app"))
        require(len(apps) == 1, "expected exactly one main app")
        app = apps[0]
        info_paths = [app / "Info.plist"]
        plugins = app / "PlugIns"
        if plugins.is_dir():
            info_paths.extend(sorted(plugins.glob("*.appex/Info.plist")))
        for info_path in info_paths:
            require(info_path.is_file(), "Info.plist missing: " + str(info_path.relative_to(root)))
            data = plistlib.loads(info_path.read_bytes())
            require(data.get("CFBundleShortVersionString") == EXPECTED_DISPLAY_VERSION,
                "public version must be 1.0.0 in " + str(info_path.relative_to(root)))
    print("[Build130 final IPA verify] GREEN")


if __name__ == "__main__":
    main()
