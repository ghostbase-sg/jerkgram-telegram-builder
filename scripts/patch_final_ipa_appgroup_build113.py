#!/usr/bin/env python3
from pathlib import Path
import os
import sys
import tempfile
import zipfile

OLD = b"group.4a348a9b186b700c.10"
NEW_TEXT = b"group.4a348a9b186b700c.1"
NEW_PADDED = NEW_TEXT + b"\x00"

TEXT_SUFFIXES = (".plist", ".strings", ".json", ".xml", ".entitlements")

def require(v, msg):
    if not v:
        raise RuntimeError("[Build113 AppGroup] " + msg)

ipa = Path(sys.argv[1] if len(sys.argv) > 1 else "ghostbase-final/GhostBase.ipa").resolve()
require(ipa.is_file(), f"IPA missing: {ipa}")

with zipfile.ZipFile(ipa, "r") as zin:
    infos = zin.infolist()
    changed = []
    fd, tmp_name = tempfile.mkstemp(prefix=ipa.name + ".appgroup.", suffix=".tmp", dir=str(ipa.parent))
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        with zipfile.ZipFile(tmp, "w") as zout:
            for item in infos:
                data = zin.read(item)
                count = data.count(OLD)
                if count:
                    lower = item.filename.lower()
                    if lower.endswith(TEXT_SUFFIXES):
                        data = data.replace(OLD, NEW_TEXT)
                    else:
                        data = data.replace(OLD, NEW_PADDED)
                    changed.append((item.filename, count))
                zout.writestr(item, data)
        os.replace(tmp, ipa)
    finally:
        tmp.unlink(missing_ok=True)

with zipfile.ZipFile(ipa, "r") as z:
    leftovers = [x.filename for x in z.infolist() if OLD in z.read(x)]

require(not leftovers, f"forbidden .10 survived: {leftovers[:20]}")
print("[Build113 AppGroup] patched entries:", len(changed))
for name, count in changed:
    print(f"  {name}: {count}")
print("[Build113 AppGroup] forbidden .10 absent")
