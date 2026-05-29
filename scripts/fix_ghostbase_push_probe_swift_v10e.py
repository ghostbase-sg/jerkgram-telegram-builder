from pathlib import Path
import re
import sys

rel = Path("submodules/TelegramCore/Sources/TelegramEngine/AccountData/RegisterNotificationToken.swift")

candidates = [
    rel,
    Path("work/swiftgram-src") / rel,
]

p = next((x for x in candidates if x.exists()), None)

if p is None:
    print("[v10e-push-fix] skip: RegisterNotificationToken.swift not found")
    for x in candidates:
        print("  checked:", x)
    sys.exit(0)

s = p.read_text()

pattern = re.compile(
    r'(// MARK: GhostBase v[^\n]* RegisterDevice Probe\n)'
    r'private func (GhostBaseV[0-9A-Za-z_]*PushProbeCore)\.record\(_ name: String, amount: Int = ([^)]+)\) \{\n'
    r'(.*?)'
    r'\n\}\n\n'
    r'private func \2\.set\(_ key: String, _ value: String\) \{\n'
    r'(.*?)'
    r'\n\}',
    re.S
)

m = pattern.search(s)

if not m:
    bad = re.findall(r'private func GhostBaseV[0-9A-Za-z_]*PushProbeCore\.[a-zA-Z_]+', s)
    if bad:
        print("[v10e-push-fix] ERROR: bad helper declarations found, but exact block pattern did not match:")
        for x in bad:
            print("  " + x)
        sys.exit(1)

    if re.search(r'private enum GhostBaseV[0-9A-Za-z_]*PushProbeCore', s):
        print("[v10e-push-fix] OK: helper already valid enum in", p)
        sys.exit(0)

    print("[v10e-push-fix] skip: no v1.0E push helper found in", p)
    sys.exit(0)

mark, type_name, default_amount, record_body, set_body = m.groups()

replacement = (
    f"{mark}"
    f"private enum {type_name} {{\n"
    f"    static func record(_ name: String, amount: Int = {default_amount}) {{\n"
    f"{record_body}\n"
    f"    }}\n\n"
    f"    static func set(_ key: String, _ value: String) {{\n"
    f"{set_body}\n"
    f"    }}\n"
    f"}}"
)

s2 = pattern.sub(replacement, s, count=1)

if re.search(r'private func GhostBaseV[0-9A-Za-z_]*PushProbeCore\.[a-zA-Z_]+', s2):
    print("[v10e-push-fix] ERROR: bad helper declarations still remain after patch")
    sys.exit(1)

p.write_text(s2)
print("[v10e-push-fix] OK: converted helper to enum static methods in", p)
