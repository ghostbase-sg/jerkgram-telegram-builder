#!/usr/bin/env python3

import hashlib
from pathlib import Path
import plistlib
import sys
import tempfile
import zipfile

import verify_jerkgram_v12k_build122_final_ipa as base
import jerkgram_finalize_build126_keychain_package1 as keychain
import jerkgram_finalize_build128_file_picker_package1 as file_picker


base.EXPECTED_BUILD = "128"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build128 final IPA verify] " + message)


def main() -> None:
    ipa = Path(sys.argv[1] if len(sys.argv) > 1 else "work/swiftgram-src/ghostbase-final/GhostBase.ipa").resolve()
    base.main()
    with tempfile.TemporaryDirectory(prefix="jerkgram-build128-verify-") as directory:
        root = Path(directory)
        with zipfile.ZipFile(ipa, "r") as archive:
            archive.extractall(root)
        apps = list((root / "Payload").glob("*.app"))
        require(len(apps) == 1, "expected exactly one main app")
        app = apps[0]
        info = plistlib.loads((app / "Info.plist").read_bytes())
        executable = info.get("CFBundleExecutable")
        require(isinstance(executable, str) and executable, "main executable key missing")
        binary = (app / executable).read_bytes()
        expected = (
            ("sideloadKeychainFix.dylib", keychain.EXPECTED_SHA256, keychain.INSTALL_NAME),
            (file_picker.FILE_PICKER_NAME, file_picker.FILE_PICKER_SHA256, file_picker.FILE_PICKER_INSTALL_NAME),
        )
        for name, digest, install_name in expected:
            dylib = app / "Frameworks" / name
            require(dylib.is_file(), name + " missing from main-app Frameworks")
            require(hashlib.sha256(dylib.read_bytes()).hexdigest() == digest, name + " SHA-256 mismatch")
            require(keychain.loaded_dylib_paths(binary).count(install_name) == 1, name + " must load exactly once")
            extension_copies = list((app / "PlugIns").rglob(name)) if (app / "PlugIns").is_dir() else []
            require(not extension_copies, name + " must not be embedded in extensions")
    print("[Build128 final IPA verify] GREEN")


if __name__ == "__main__":
    main()
