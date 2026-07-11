#!/usr/bin/env python3

from pathlib import Path
import os
import plistlib
import sys
import zipfile

PUBLIC_BUNDLE_ID = "ph.telegra.Telegraph"

ipa = Path(
    sys.argv[1]
    if len(sys.argv) > 1
    else "ghostbase-final/GhostBase.ipa"
)

if not ipa.is_file():
    raise FileNotFoundError(f"IPA not found: {ipa}")

tmp = ipa.with_name(ipa.name + ".public.tmp")
tmp.unlink(missing_ok=True)

try:
    with zipfile.ZipFile(ipa, "r") as source:
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
                f"Expected one main app Info.plist, found: {targets}"
            )

        target = targets[0]
        previous_bundle_id = None

        with zipfile.ZipFile(tmp, "w") as destination:
            for entry in entries:
                data = source.read(entry.filename)

                if entry.filename == target:
                    plist = plistlib.loads(data)
                    previous_bundle_id = plist.get("CFBundleIdentifier")
                    plist["CFBundleIdentifier"] = PUBLIC_BUNDLE_ID

                    plist_format = (
                        plistlib.FMT_BINARY
                        if data.startswith(b"bplist")
                        else plistlib.FMT_XML
                    )

                    data = plistlib.dumps(
                        plist,
                        fmt=plist_format,
                        sort_keys=False,
                    )

                destination.writestr(entry, data)

    os.replace(tmp, ipa)

except Exception:
    tmp.unlink(missing_ok=True)
    raise

with zipfile.ZipFile(ipa, "r") as result:
    plist = plistlib.loads(result.read(target))
    final_bundle_id = plist.get("CFBundleIdentifier")

if final_bundle_id != PUBLIC_BUNDLE_ID:
    raise RuntimeError(
        f"Final Bundle ID mismatch: {final_bundle_id}"
    )

print(f"IPA: {ipa}")
print(f"CFBundleIdentifier: {previous_bundle_id} -> {final_bundle_id}")
print(f"Final size: {ipa.stat().st_size} bytes")
