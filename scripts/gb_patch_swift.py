from pathlib import Path
import re, sys

APP_BUNDLE = "app.pumpkin6584.lion7414"
APP_GROUP = "group.4a348a9b186b700c.1"

def kill_guard_block(s: str) -> str:
    lines = s.splitlines()
    out = []
    i = 0

    while i < len(lines):
        line = lines[i]

        if re.search(r"\bguard\s+let\s+baseAppBundle\w*", line):
            indent = line[:len(line) - len(line.lstrip())]
            m = re.search(r"guard\s+let\s+(baseAppBundle\w*)", line)
            var = m.group(1) if m else "baseAppBundleId"

            out.append(f'{indent}let {var} = "{APP_BUNDLE}"')

            head = line
            i += 1
            while "else" not in head and i < len(lines):
                head += lines[i]
                i += 1

            depth = head.count("{") - head.count("}")
            while i < len(lines) and depth > 0:
                depth += lines[i].count("{") - lines[i].count("}")
                i += 1
            continue

        out.append(line)
        i += 1

    return "\n".join(out) + "\n"

changed = []

for p in Path("Swiftgram").rglob("*.swift"):
    s = p.read_text(errors="ignore")
    old = s

    s = kill_guard_block(s)

    s = re.sub(
        r"^(\s*)let\s+(baseAppBundle\w*)\s*=\s*$",
        rf'\1let \2 = "{APP_BUNDLE}"',
        s,
        flags=re.M,
    )

    s = re.sub(
        r'let\s+appGroupName\s*=\s*"group\.[^"]*"',
        f'let appGroupName = "{APP_GROUP}"',
        s,
    )

    s = re.sub(
        r'let\s+appGroupName\s*=\s*"group\.\\\([^)]*\)"',
        f'let appGroupName = "{APP_GROUP}"',
        s,
    )

    s = re.sub(
        r'containerURL\(forSecurityApplicationGroupIdentifier:\s*"group\.[^"]*"\)',
        f'containerURL(forSecurityApplicationGroupIdentifier: "{APP_GROUP}")',
        s,
    )

    if "func sgBaseBundleIdentifier()" in s:
        s = re.sub(
            r"func sgBaseBundleIdentifier\(\)\s*->\s*String\s*\{.*?\n\}",
            f'func sgBaseBundleIdentifier() -> String {{\n    return "{APP_BUNDLE}"\n}}',
            s,
            flags=re.S,
        )

    if "func sgAppGroupIdentifier()" in s:
        s = re.sub(
            r"func sgAppGroupIdentifier\(\)\s*->\s*String\s*\{.*?\n\}",
            f'func sgAppGroupIdentifier() -> String {{\n    return "{APP_GROUP}"\n}}',
            s,
            flags=re.S,
        )

    if s != old:
        p.write_text(s)
        changed.append(str(p))

bad = []
for p in Path("Swiftgram").rglob("*.swift"):
    s = p.read_text(errors="ignore")
    for n, l in enumerate(s.splitlines(), 1):
        if re.search(r"let\s+baseAppBundle\w*\s*=\s*$", l):
            bad.append(f"{p}:{n}: empty baseAppBundle: {l}")
        if re.search(r"guard\s+let\s+baseAppBundle", l):
            bad.append(f"{p}:{n}: guard baseAppBundle remains: {l}")
        if 'let appGroupName = "group.' in l and APP_GROUP not in l:
            bad.append(f"{p}:{n}: wrong appGroupName: {l}")

print("Swift AppGroup changed files:")
for x in changed:
    print(x)

if bad:
    print("Swift AppGroup patch FAILED:")
    for x in bad[:100]:
        print(x)
    sys.exit(1)

print("Swift AppGroup patch OK")
