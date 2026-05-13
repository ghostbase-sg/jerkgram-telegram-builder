from pathlib import Path
import re

KEY = "com.apple.developer.carplay-messaging"
roots = [Path("Telegram"), Path("Swiftgram"), Path("build-system")]

changed = []

def patch_text(s):
    old = s

    # XML plist:
    # <key>com.apple.developer.carplay-messaging</key>
    # <true/>
    s = re.sub(
        r'\n[ \t]*<key>com\.apple\.developer\.carplay-messaging</key>\s*\n[ \t]*<(true|false)/>\s*',
        '\n',
        s
    )

    # Starlark/Python-style dict entries:
    # "com.apple.developer.carplay-messaging": True,
    s = re.sub(
        r'\n[ \t]*["\']com\.apple\.developer\.carplay-messaging["\'][ \t]*:[ \t]*(True|False|true|false|["\'][^"\']*["\']),?[ \t]*',
        '\n',
        s
    )

    # Plain list/string occurrence line.
    s = re.sub(
        r'\n[ \t]*["\']com\.apple\.developer\.carplay-messaging["\'],?[ \t]*',
        '\n',
        s
    )

    return s, s != old

for root in roots:
    if not root.exists():
        continue
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix not in ["", ".plist", ".entitlements", ".bzl", ".BUILD", ".build"] and p.name not in ["BUILD", "BUILD.bazel"]:
            continue
        try:
            s = p.read_text(errors="ignore")
        except Exception:
            continue
        if KEY not in s:
            continue
        ns, did = patch_text(s)
        if did:
            p.write_text(ns)
            changed.append(str(p))

print("patched entitlements files:", len(changed))
for x in changed:
    print(x)

left = []
for root in roots:
    if not root.exists():
        continue
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        try:
            if KEY in p.read_text(errors="ignore"):
                left.append(str(p))
        except Exception:
            pass

if left:
    print("ERROR: carplay entitlement leftovers:")
    for x in left:
        print(x)
    raise SystemExit(1)

print("Unsupported entitlement patch OK")
