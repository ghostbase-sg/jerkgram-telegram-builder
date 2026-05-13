from pathlib import Path

p = Path("Swiftgram/SGLogging/Sources/SGLogger.swift")
s = p.read_text()
lines = s.splitlines()

out = []
i = 0
patched = 0

while i < len(lines):
    line = lines[i]

    if "guard let " in line and "= sgBaseBundleIdentifier()" in line and "else" in line:
        indent = line[:len(line) - len(line.lstrip())]
        var = line.split("guard let ", 1)[1].split("=", 1)[0].strip()

        out.append(f"{indent}let {var} = sgBaseBundleIdentifier()")
        patched += 1

        i += 1
        seen_return = False
        while i < len(lines):
            if "return SGLogger(" in lines[i]:
                seen_return = True
            if seen_return and lines[i].strip() == "}":
                i += 1
                break
            i += 1
        continue

    out.append(line)
    i += 1

new = "\n".join(out) + "\n"
p.write_text(new)

if "guard let " in new and "sgBaseBundleIdentifier()" in new:
    raise SystemExit("SGLogger patch failed: guard let still exists")

print(f"patched SGLogger guard count: {patched}")
