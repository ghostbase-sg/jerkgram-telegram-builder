#!/usr/bin/env python3

from pathlib import Path
import os
import plistlib
import sys
import zipfile


EXPECTED_BUNDLE_ID = "ph.telegra.Telegraph"
DISPLAY_NAME = "Jerkgram"

ipa = Path(
    sys.argv[1]
    if len(sys.argv) > 1
    else "ghostbase-final/GhostBase.ipa"
)

if not ipa.is_file():
    raise FileNotFoundError(
        f"IPA missing: {ipa}"
    )

tmp = ipa.with_name(
    ipa.name + ".jerkgram-build110.tmp"
)

tmp.unlink(missing_ok=True)

try:
    with zipfile.ZipFile(
        ipa,
        "r",
    ) as source:
        entries = source.infolist()

        targets = [
            entry.filename
            for entry in entries
            if entry.filename.startswith("Payload/")
            and entry.filename.endswith(".app/Info.plist")
            and entry.filename.count("/") == 2
        ]

        if len(targets) != 1:
            raise RuntimeError(
                f"Expected one main Info.plist: {targets}"
            )

        target = targets[0]

        with zipfile.ZipFile(
            tmp,
            "w",
        ) as destination:
            for entry in entries:
                data = source.read(
                    entry.filename
                )

                if entry.filename == target:
                    plist = plistlib.loads(data)

                    bundle_id = plist.get(
                        "CFBundleIdentifier"
                    )

                    if bundle_id != EXPECTED_BUNDLE_ID:
                        raise RuntimeError(
                            "Bundle ID mismatch before "
                            "Build110 naming: "
                            f"{bundle_id!r}"
                        )

                    plist[
                        "CFBundleDisplayName"
                    ] = DISPLAY_NAME

                    plist[
                        "CFBundleName"
                    ] = DISPLAY_NAME

                    fmt = (
                        plistlib.FMT_BINARY
                        if data.startswith(b"bplist")
                        else plistlib.FMT_XML
                    )

                    data = plistlib.dumps(
                        plist,
                        fmt=fmt,
                        sort_keys=False,
                    )

                destination.writestr(
                    entry,
                    data,
                )

    os.replace(
        tmp,
        ipa,
    )

except Exception:
    tmp.unlink(missing_ok=True)
    raise


with zipfile.ZipFile(
    ipa,
    "r",
) as archive:
    plist = plistlib.loads(
        archive.read(target)
    )


if (
    plist.get("CFBundleIdentifier")
    != EXPECTED_BUNDLE_ID
):
    raise RuntimeError(
        "Build110 changed Bundle ID"
    )

if (
    plist.get("CFBundleDisplayName")
    != DISPLAY_NAME
):
    raise RuntimeError(
        "Build110 display name mismatch"
    )

if (
    plist.get("CFBundleName")
    != DISPLAY_NAME
):
    raise RuntimeError(
        "Build110 bundle name mismatch"
    )


print(
    "CFBundleIdentifier: "
    "ph.telegra.Telegraph (preserved)"
)

print(
    "CFBundleDisplayName: Jerkgram"
)

print(
    "CFBundleName: Jerkgram"
)
