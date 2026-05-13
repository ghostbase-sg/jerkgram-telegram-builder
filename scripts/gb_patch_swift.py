from pathlib import Path
import re

p = Path("Swiftgram/SGLogging/Sources/SGLogger.swift")
s = p.read_text()

s = re.sub(
    r'guard let (baseAppBundleId\w*) = sgBaseBundleIdentifier\(\)\s*else\s*\{\s*print\("Can.t setup logger \(1\)!"\)\s*return SGLogger\(rootPath: "", basePath: ""\)\s*\}',
    r'let \1 = sgBaseBundleIdentifier()',
    s,
    flags=re.S
)

s = s.replace(
    "guard let baseAppBundleId = sgBaseBundleIdentifier() else {",
    "let baseAppBundleId = sgBaseBundleIdentifier()\n            if false {"
)

p.write_text(s)
print("patched SGLogger.swift")
