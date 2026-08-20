#!/usr/bin/env python3

from pathlib import Path
import os
import plistlib
import sys
import zipfile


EXPECTED_BUNDLE_ID = "ph.telegra.Telegraph"

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
    ipa.name + ".jerkgram-name.tmp"
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
                f"Expected one main plist: {targets}"
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
                            "Bundle ID before JerkGram "
                            "name finalization is wrong: "
                            f"{bundle_id!r}"
                        )

                    plist[
                        "CFBundleDisplayName"
                    ] = "JerkGram"

                    plist[
                        "CFBundleName"
                    ] = "JerkGram"

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

    os.replace(tmp, ipa)

except Exception:
    tmp.unlink(missing_ok=True)
    raise


with zipfile.ZipFile(ipa, "r") as result:
    plist = plistlib.loads(
        result.read(target)
    )

if (
    plist.get("CFBundleIdentifier")
    != EXPECTED_BUNDLE_ID
):
    raise RuntimeError(
        "Bundle ID changed during "
        "display-name finalization"
    )

if (
    plist.get("CFBundleDisplayName")
    != "JerkGram"
):
    raise RuntimeError(
        "CFBundleDisplayName != JerkGram"
    )

if plist.get("CFBundleName") != "JerkGram":
    raise RuntimeError(
        "CFBundleName != JerkGram"
    )

print(
    "CFBundleIdentifier: "
    "ph.telegra.Telegraph (preserved)"
)

print(
    "CFBundleDisplayName: JerkGram"
)

print(
    "CFBundleName: JerkGram"
)
