#!/usr/bin/env python3

import os
from pathlib import Path
import plistlib
import sys
import tempfile
import zipfile

import jerkgram_finalize_build128_identity as base
import jerkgram_finalize_build132_esign_ready as build132


base.base.BUILD = "130"
DISPLAY_VERSION = "1.0.0"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build130 identity] " + message)


def stamp_short_version(ipa: Path) -> None:
    require(ipa.is_file(), "IPA missing: " + str(ipa))
    with tempfile.TemporaryDirectory(prefix="jerkgram-build130-version-") as directory:
        root = Path(directory)
        with zipfile.ZipFile(ipa, "r") as archive:
            archive.extractall(root)
            infos = archive.infolist()
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
            data["CFBundleShortVersionString"] = DISPLAY_VERSION
            info_path.write_bytes(plistlib.dumps(data, fmt=plistlib.FMT_BINARY, sort_keys=False))
        descriptor, temporary_name = tempfile.mkstemp(prefix="jerkgram-build130-", suffix=".ipa", dir=ipa.parent)
        os.close(descriptor)
        temporary = Path(temporary_name)
        try:
            with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as output:
                for info in infos:
                    output.writestr(info, b"" if info.is_dir() else (root / info.filename).read_bytes())
            os.replace(temporary, ipa)
        finally:
            temporary.unlink(missing_ok=True)


def main() -> None:
    ipa = Path(sys.argv[1] if len(sys.argv) > 1 else "work/swiftgram-src/ghostbase-final/GhostBase.ipa").resolve()
    base.main()
    stamp_short_version(ipa)
    print("[Build130 identity] legacy identity stage GREEN")
    print("[Build130 identity] handing finalized legacy package to Build132 InstalledIdentity finalizer")
    build132.main()


if __name__ == "__main__":
    main()
