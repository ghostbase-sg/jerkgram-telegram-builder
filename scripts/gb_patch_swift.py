from pathlib import Path
import re
import sys

p = Path("Swiftgram/SGLogging/Sources/SGLogger.swift")
lines = p.read_text().splitlines()

out = []
i = 0
patched = 0

while i < len(lines):
    line = lines[i]

    if re.search(r"\bguard\s+let\s+baseAppBundle\w*", line):
        indent = line[:len(line) - len(line.lstrip())]

        head = line.strip()
        j = i + 1
        while "else" not in head and j < len(lines):
            head += " " + lines[j].strip()
            j += 1

        m = re.search(r"guard\s+let\s+([A-Za-z_][A-Za-z0-9_]*)", head)
        if not m:
            print("Cannot parse SGLogger guard:")
            print(head)
            sys.exit(1)

        var = m.group(1)
        out.append(f"{indent}let {var} = sgBaseBundleIdentifier()")
        patched += 1

        i = j
        depth = head.count("{") - head.count("}")

        while i < len(lines) and depth > 0:
            depth += lines[i].count("{") - lines[i].count("}")
            i += 1

        continue

    out.append(line)
    i += 1

new = "\n".join(out) + "\n"
p.write_text(new)

bad = []
for n, l in enumerate(new.splitlines(), 1):
    if re.search(r"guard\s+let\s+baseAppBundle", l):
        bad.append(f"{n}: guard still exists: {l}")
    if re.search(r"let\s+baseAppBundle\w*\s*=\s*$", l):
        bad.append(f"{n}: empty assignment: {l}")

if patched != 1 or bad:
    print("SGLogger patch FAILED")
    print("patched count:", patched)
    for x in bad:
        print(x)
    print("SGLogger nearby:")
    for n, l in enumerate(new.splitlines(), 1):
        if 32 <= n <= 48:
            print(f"{n}: {l}")
    sys.exit(1)

print("SGLogger patched OK")
