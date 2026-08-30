#!/usr/bin/env python3

import hashlib
from pathlib import Path
import plistlib
import sys
import tempfile
import zipfile

import verify_jerkgram_v12k_build122_final_ipa as base
from jerkgram_finalize_build126_keychain_package1 import EXPECTED_SHA256, INSTALL_NAME, loaded_dylib_paths, require


base.EXPECTED_BUILD = "126"
DYLIB_NAME = "sideloadKeychainFix.dylib"


def main() -> None:
    ipa = Path(sys.argv[1] if len(sys.argv) > 1 else "work/swiftgram-src/ghostbase-final/GhostBase.ipa").resolve()
    base.main()
    with tempfile.TemporaryDirectory(prefix="jerkgram-build126-verify-") as directory:
        root = Path(directory)
        with zipfile.ZipFile(ipa, "r") as archive:
            archive.extractall(root)
        apps = list((root / "Payload").glob("*.app"))
        require(len(apps) == 1, "expected exactly one main app")
        app = apps[0]
        info = plistlib.loads((app / "Info.plist").read_bytes())
        executable_name = info.get("CFBundleExecutable")
        require(isinstance(executable_name, str) and executable_name, "main executable key missing")
        dylib = app / "Frameworks" / DYLIB_NAME
        require(dylib.is_file(), "approved dylib missing from main app Frameworks")
        require(hashlib.sha256(dylib.read_bytes()).hexdigest() == EXPECTED_SHA256, "approved dylib SHA-256 mismatch")
        require(loaded_dylib_paths((app / executable_name).read_bytes()).count(INSTALL_NAME) == 1, "main executable must load the approved dylib exactly once")
        extension_copies = list((app / "PlugIns").rglob(DYLIB_NAME)) if (app / "PlugIns").is_dir() else []
        require(not extension_copies, "approved dylib must not be embedded in extensions")
    print("[Build126 final IPA verify] GREEN")
    print("[Build126 final IPA verify] Build=126, exact main-app-only sideload keychain library")


if __name__ == "__main__":
    main()
