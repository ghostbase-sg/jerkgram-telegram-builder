from pathlib import Path
import re

BASE = "app.pumpkin6584.lion7414"
GROUP = "group.4a348a9b186b700c.1"

root = Path("Swiftgram")
changed = []

for p in root.rglob("*.swift"):
    s = p.read_text(errors="ignore")
    old = s

    s = re.sub(
        r'(?m)^(\s*)guard\s+let\s+baseAppBundleId\s*=.*?else\s*\{\s*$',
        rf'\1if false {{',
        s
    )

    s = re.sub(
        r'(?m)^(\s*)guard\s+let\s+baseAppBundleIdentifier\s*=.*?else\s*\{\s*$',
        rf'\1if false {{',
        s
    )

    s = re.sub(
        r'(?m)^(\s*)let\s+baseAppBundleId\s*=.*$',
        rf'\1let baseAppBundleId = "{BASE}"',
        s
    )

    s = re.sub(
        r'(?m)^(\s*)let\s+baseAppBundleIdentifier\s*=.*$',
        rf'\1let baseAppBundleIdentifier = "{BASE}"',
        s
    )

    s = re.sub(
        r'(?m)^(\s*)let\s+appGroupName\s*=.*$',
        rf'\1let appGroupName = "{GROUP}"',
        s
    )

    s = re.sub(
        r'group\.\(baseAppBundleId\)',
        GROUP,
        s
    )

    s = re.sub(
        r'group\.\(baseAppBundleIdentifier\)',
        GROUP,
        s
    )

    if s != old:
        p.write_text(s)
        changed.append(str(p))

print("patched swift files:", len(changed))
for x in changed:
    print(x)

bad = []
for p in root.rglob("*.swift"):
    s = p.read_text(errors="ignore")
    if re.search(r'let\s+baseAppBundle(Id|Identifier)\s*=\s*"\s*$', s, re.M):
        bad.append(str(p))
    if "guard let baseAppBundle" in s:
        bad.append(str(p))
    if re.search(r'let\s+baseAppBundle(Id|Identifier)\s*=', s):
        bad.append(str(p))

if bad:
    print("bad Swift AppGroup leftovers:")
    for x in bad:
        print(x)
    raise SystemExit(1)

print("Swift AppGroup patch OK")
