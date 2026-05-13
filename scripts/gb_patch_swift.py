from pathlib import Path
import re

p = Path("Swiftgram/SGLogging/Sources/SGLogger.swift")
lines = p.read_text().splitlines()

out = []
i = 0
patched = 0

while i < len(lines):
    line = lines[i]

    if "guard let baseAppBundle" in line:
        indent = line[:len(line) - len(line.lstrip())]

        stmt = line.strip()
        j = i + 1
        while " else" not in stmt and j < len(lines):
            stmt += " " + lines[j].strip()
            j += 1

        m = re.search(r"guard\s+let\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s+else\s*\{", stmt)
        if not m:
            raise SystemExit("Cannot parse SGLogger guard: " + stmt)

        var = m.group(1)
        expr = m.group(2).strip()

        out.append(f"{indent}let {var} = {expr}")
        patched += 1

        i = j
        depth = stmt.count("{") - stmt.count("}")
        while i < len(lines):
            depth += lines[i].count("{") - lines[i].count("}")
            i += 1
            if depth <= 0:
                break
        continue

    out.append(line)
    i += 1

new = "\n".join(out) + "\n"

if patched != 1:
    print("SGLogger patch count:", patched)
    for n, l in enumerate(lines, 1):
        if "baseAppBundle" in l or "guard let" in l:
            print(f"{n}: {l}")
    raise SystemExit("SGLogger patch failed")

if re.search(r"guard\s+let\s+baseAppBundle", new):
    raise SystemExit("SGLogger guard still exists")

p.write_text(new)
print("SGLogger patched OK")
