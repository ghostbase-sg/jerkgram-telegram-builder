#!/usr/bin/env python3

from pathlib import Path
import plistlib
import sys
import zipfile


EXPECTED_BUNDLE_ID = "ph.telegra.Telegraph"

ipa = Path(
    sys.argv[1]
    if len(sys.argv) > 1
    else "ghostbase-final/GhostBase.ipa"
)


def require(condition, message):
    if not condition:
        raise RuntimeError(
            "[verify Build109 final IPA] "
            + message
        )


require(
    ipa.is_file(),
    f"missing IPA: {ipa}",
)

with zipfile.ZipFile(ipa, "r") as archive:
    targets = [
        entry.filename
        for entry in archive.infolist()
        if entry.filename.startswith("Payload/")
        and entry.filename.endswith(".app/Info.plist")
        and entry.filename.count("/") == 2
    ]

    require(
        len(targets) == 1,
        f"unexpected main plist targets: {targets}",
    )

    plist = plistlib.loads(
        archive.read(targets[0])
    )


require(
    plist.get("CFBundleIdentifier")
    == EXPECTED_BUNDLE_ID,
    (
        "CFBundleIdentifier mismatch: "
        f"{plist.get('CFBundleIdentifier')!r}"
    ),
)

require(
    plist.get("CFBundleDisplayName")
    == "JerkGram",
    (
        "CFBundleDisplayName mismatch: "
        f"{plist.get('CFBundleDisplayName')!r}"
    ),
)

require(
    plist.get("CFBundleName")
    == "JerkGram",
    (
        "CFBundleName mismatch: "
        f"{plist.get('CFBundleName')!r}"
    ),
)

print(
    "[verify Build109 final IPA] GREEN"
)

print(
    "Bundle ID: ph.telegra.Telegraph"
)

print(
    "Display Name: JerkGram"
)
