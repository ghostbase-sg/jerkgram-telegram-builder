from pathlib import Path
import re

KEY = "com.apple.developer.carplay-messaging"

roots = [
    Path("Telegram"),
    Path("Swiftgram"),
    Path("build-system/example-configuration"),
]

changed = []

def ignored(p: Path) -> bool:
    s = str(p)
    return (
        "build-system/bazel-rules/" in s
        or "build-system/fake-codesigning/" in s
        or "/provisioning/" in s
        or p.suffix in [".mobileprovision", ".provisionprofile", ".pyc"]
        or "__pycache__" in s
        or "/.git/" in s
    )

def candidate(p: Path) -> bool:
    return (
        p.name in ["BUILD", "BUILD.bazel"]
        or p.suffix in [".plist", ".entitlements", ".bzl"]
    )

def patch_text(s: str) -> str:
    s = re.sub(
        r'\n[ \t]*<key>com\.apple\.developer\.carplay-messaging</key>\s*\n[ \t]*<(true|false)/>\s*',
        '\n',
        s
    )
    s = re.sub(
        r'\n[ \t]*["\']com\.apple\.developer\.carplay-messaging["\'][ \t]*:[ \t]*(True|False|true|false|["\'][^"\']*["\']),?[ \t]*',
        '\n',
        s
    )
    s = re.sub(
        r'\n[ \t]*["\']com\.apple\.developer\.carplay-messaging["\'],?[ \t]*',
        '\n',
        s
    )
    return s

for root in roots:
    if not root.exists():
        continue

    for p in root.rglob("*"):
        if not p.is_file() or ignored(p) or not candidate(p):
            continue

        try:
            old = p.read_text(errors="ignore")
        except Exception:
            continue

        if KEY not in old:
            continue

        new = patch_text(old)
        if new != old:
            p.write_text(new)
            changed.append(str(p))

print("patched entitlements files:", len(changed))
for x in changed:
    print(x)

left = []
for root in roots:
    if not root.exists():
        continue

    for p in root.rglob("*"):
        if not p.is_file() or ignored(p) or not candidate(p):
            continue

        try:
            if KEY in p.read_text(errors="ignore"):
                left.append(str(p))
        except Exception:
            pass

if left:
    print("ERROR: carplay entitlement leftovers:")
    for x in sorted(set(left)):
        print(x)
    raise SystemExit(1)

print("Unsupported entitlement patch OK")
