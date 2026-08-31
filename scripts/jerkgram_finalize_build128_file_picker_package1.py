#!/usr/bin/env python3
"""Embed the audited FilePicker compatibility library into the main app only."""

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import plistlib
import sys
import tempfile
import zipfile

import jerkgram_finalize_build126_keychain_package1 as macho


FILE_PICKER_NAME = "FilePickerFix.dylib"
FILE_PICKER_INSTALL_NAME = "@executable_path/Frameworks/FilePickerFix.dylib"
FILE_PICKER_SHA256 = "ece2756a52ee34110b3a0252008cce3cd58b359d7571edd080032e064bf0cc7a"
FILE_PICKER_ASSET = Path(__file__).resolve().parents[1] / "assets" / FILE_PICKER_NAME


@dataclass(frozen=True)
class ApprovedFilePicker:
    data: bytes
    sha256: str


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build128 FilePicker package] " + message)


def approved_file_picker() -> ApprovedFilePicker:
    require(FILE_PICKER_ASSET.is_file(), "FilePicker dylib asset is missing: " + str(FILE_PICKER_ASSET))
    data = FILE_PICKER_ASSET.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    require(digest == FILE_PICKER_SHA256, "FilePicker dylib SHA-256 mismatch")
    return ApprovedFilePicker(data=data, sha256=digest)


def package_file_picker(ipa: Path) -> None:
    library = approved_file_picker()
    require(ipa.is_file(), "IPA missing: " + str(ipa))
    with tempfile.TemporaryDirectory(prefix="jerkgram-build128-file-picker-") as directory:
        root = Path(directory)
        with zipfile.ZipFile(ipa, "r") as archive:
            infos = archive.infolist()
            archive.extractall(root)
        apps = list((root / "Payload").glob("*.app"))
        require(len(apps) == 1, "expected exactly one main app")
        app = apps[0]
        info = plistlib.loads((app / "Info.plist").read_bytes())
        executable = info.get("CFBundleExecutable")
        require(isinstance(executable, str) and executable, "main executable key missing")
        executable_path = app / executable
        require(executable_path.is_file(), "main executable missing")
        frameworks = app / "Frameworks"
        frameworks.mkdir(exist_ok=True)
        target = frameworks / FILE_PICKER_NAME
        executable_path.write_bytes(macho.inject_load_dylib(executable_path.read_bytes(), FILE_PICKER_INSTALL_NAME))
        target.write_bytes(library.data)
        fd, temporary_name = tempfile.mkstemp(prefix=ipa.name + ".build128.", suffix=".tmp", dir=str(ipa.parent))
        os.close(fd)
        temporary = Path(temporary_name)
        try:
            with zipfile.ZipFile(temporary, "w") as output:
                existing = {info.filename for info in infos}
                for info in infos:
                    source = root / info.filename
                    output.writestr(info, b"" if info.is_dir() else source.read_bytes())
                relative = target.relative_to(root).as_posix()
                if relative not in existing:
                    output.writestr(relative, target.read_bytes())
            os.replace(temporary, ipa)
        finally:
            if temporary.exists():
                temporary.unlink()


def main() -> None:
    ipa = Path(sys.argv[1] if len(sys.argv) > 1 else "work/swiftgram-src/ghostbase-final/GhostBase.ipa").resolve()
    package_file_picker(ipa)
    print("[Build128 FilePicker package] GREEN")
    print("[Build128 FilePicker package] exact arm64 dylib added to the main app only; ESign must sign the final IPA")


if __name__ == "__main__":
    main()
