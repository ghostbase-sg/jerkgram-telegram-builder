from pathlib import Path

p = Path("Swiftgram/SGLogging/Sources/SGLogger.swift")
s = p.read_text()

old = "guard let baseAppBundleId = sgBaseBundleIdentifier() else {"
if old not in s:
    print("SGLogger guard already patched or not found")
else:
    lines = s.splitlines()
    out = []
    i = 0
    while i < len(lines):
        if old in lines[i]:
            indent = lines[i].split("guard")[0]
            out.append(indent + "let baseAppBundleId = sgBaseBundleIdentifier()")
            i += 1
            while i < len(lines):
                if "return SGLogger(rootPath:" in lines[i]:
                    i += 1
                    if i < len(lines) and lines[i].strip() == "}":
                        i += 1
                    break
                i += 1
            continue
        out.append(lines[i])
        i += 1
    s = "\n".join(out) + "\n"
    p.write_text(s)
    print("patched SGLogger guard let")

s2 = p.read_text()
if "guard let baseAppBundleId = sgBaseBundleIdentifier()" in s2:
    raise SystemExit("SGLogger patch failed: guard let still exists")
