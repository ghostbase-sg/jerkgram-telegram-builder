#!/usr/bin/env python3
import os
from pathlib import Path
root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
path = root / "submodules/Display/Source/GhostBaseGlass.swift"
text = path.read_text(encoding="utf-8")
required = [
    "GhostBase v1.1E GLASSRUNTIME3",
    "UIAccessibility.isReduceTransparencyEnabled",
    "ProcessInfo.processInfo.isLowPowerModeEnabled",
    "static let ghostBaseGlassDidChange",
    "private static var peerColors",
]
for value in required:
    if value not in text:
        raise SystemExit(f"[VERIFY V11E GLASSRUNTIME3] missing {value}")
for forbidden in ["systemPurple", "activeTintColor", "lightweightTintColor", "largeCardTintColor", "compactControlTintColor"]:
    if forbidden in text:
        raise SystemExit(f"[VERIFY V11E GLASSRUNTIME3] forbidden legacy API/color: {forbidden}")
print("[VERIFY V11E GLASSRUNTIME3] OK")
