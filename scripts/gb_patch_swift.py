from pathlib import Path
import re

BASE = "app.pumpkin6584.lion7414"
GROUP = "group.4a348a9b186b700c.1"
root = Path("Swiftgram")
changed = []

def drop_unused_var(s, var):
    lines = s.splitlines()
    keep_nl = s.endswith("\n")

    for i, line in enumerate(lines):
        m = re.match(rf'^(\s*)let\s+{var}\s*=.*$', line)
        if not m:
            continue

        indent = m.group(1)
        rest = "\n".join(lines[:i] + lines[i+1:])

        if indent and not re.search(rf'\b{var}\b', rest):
            lines[i] = f'{indent}_ = "{BASE}"'

    return "\n".join(lines) + ("\n" if keep_nl else "")

def has_unused_base_var(s):
    lines = s.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r'^(\s+)let\s+(baseAppBundleId|baseAppBundleIdentifier)\s*=.*$', line)
        if not m:
            continue
        var = m.group(2)
        rest = "\n".join(lines[:i] + lines[i+1:])
        if not re.search(rf'\b{var}\b', rest):
            return True
    return False

for p in root.rglob("*.swift"):
    s = p.read_text(errors="ignore")
    old = s

    s = re.sub(
        r'(?m)^(\s*)guard\s+let\s+baseAppBundleId\s*=.*?else\s*\{\s*$',
        rf'\1let baseAppBundleId = Bundle.main.bundleIdentifier ?? "{BASE}"\n\1if Bundle.main.bundleIdentifier == nil {{',
        s
    )

    s = re.sub(
        r'(?m)^(\s*)guard\s+let\s+baseAppBundleIdentifier\s*=.*?else\s*\{\s*$',
        rf'\1let baseAppBundleIdentifier = Bundle.main.bundleIdentifier ?? "{BASE}"\n\1if Bundle.main.bundleIdentifier == nil {{',
        s
    )

    s = re.sub(
        r'(?m)^(\s*)let\s+appGroupName\s*=.*$',
        rf'\1let appGroupName = "{GROUP}"',
        s
    )

    s = re.sub(r'group\.\\\(baseAppBundleId\)', GROUP, s)
    s = re.sub(r'group\.\\\(baseAppBundleIdentifier\)', GROUP, s)
    s = re.sub(r'group\.\(baseAppBundleId\)', GROUP, s)
    s = re.sub(r'group\.\(baseAppBundleIdentifier\)', GROUP, s)

    s = drop_unused_var(s, "baseAppBundleId")
    s = drop_unused_var(s, "baseAppBundleIdentifier")

    if s != old:
        p.write_text(s)
        changed.append(str(p))

print("patched swift files:", len(changed))
for x in changed:
    print(x)

bad = []
for p in root.rglob("*.swift"):
    s = p.read_text(errors="ignore")

    if "guard let baseAppBundle" in s:
        bad.append(str(p))
    if re.search(r'let\s+baseAppBundle(Id|Identifier)\s*=\s*"\s*$', s, re.M):
        bad.append(str(p))
    if re.search(r'group\.\\\(baseAppBundle(Id|Identifier)\)', s):
        bad.append(str(p))
    if re.search(r'appGroupName\s*=\s*"group\.\\\(', s):
        bad.append(str(p))
    if has_unused_base_var(s):
        bad.append(str(p))

if bad:
    print("bad Swift AppGroup leftovers:")
    for x in sorted(set(bad)):
        print(x)
    raise SystemExit(1)

print("Swift AppGroup patch OK")
