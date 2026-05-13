from pathlib import Path
import re, sys

p = Path("Swiftgram/SGLogging/Sources/SGLogger.swift")
s = p.read_text()

APP_GROUP = "group.4a348a9b186b700c.1"

start = 'print("SGLogger setup...")'
end = 'let maybeAppGroupUrl = FileManager.default.containerURL'

if start not in s or end not in s:
    print("SGLogger structure not found")
    print("matches:")
    for n, l in enumerate(s.splitlines(), 1):
        if "SGLogger setup" in l or "baseAppBundle" in l or "appGroupName" in l or "maybeAppGroupUrl" in l:
            print(f"{n}: {l}")
    sys.exit(1)

pattern = re.compile(
    r'(print\("SGLogger setup\.\.\."\)\s*)'
    r'.*?'
    r'(let maybeAppGroupUrl = FileManager\.default\.containerURL)',
    re.S
)

s2, count = pattern.subn(
    r'\1let appGroupName = "' + APP_GROUP + r'"\n            \2',
    s,
    count=1
)

p.write_text(s2)

bad = False
for n, l in enumerate(s2.splitlines(), 1):
    if "baseAppBundle" in l:
        print(f"BAD baseAppBundle remains at {n}: {l}")
        bad = True
    if re.search(r"let\s+\w+\s*=\s*$", l):
        print(f"BAD empty assignment at {n}: {l}")
        bad = True

if count != 1 or bad or APP_GROUP not in s2:
    print("SGLogger patch failed")
    for n, l in enumerate(s2.splitlines(), 1):
        if 34 <= n <= 48:
            print(f"{n}: {l}")
    sys.exit(1)

print("SGLogger patched OK")
for n, l in enumerate(s2.splitlines(), 1):
    if 34 <= n <= 48:
        print(f"{n}: {l}")
