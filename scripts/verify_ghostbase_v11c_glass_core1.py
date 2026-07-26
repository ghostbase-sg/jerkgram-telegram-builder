#!/usr/bin/env python3
import os
from pathlib import Path

root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
path = root / "submodules/Display/Source/GhostBaseGlass.swift"
text = path.read_text(encoding="utf-8")
required = [
    "GhostBase v1.1C GLASSCORE1",
    'enabledKey = "GhostBase.Glass.Enabled"',
    "UIAccessibility.isReduceTransparencyEnabled",
    "ProcessInfo.processInfo.isLowPowerModeEnabled",
    "coldFillColor",
    "lightweightFillColor",
]
missing = [item for item in required if item not in text]
if missing:
    raise SystemExit(f"[VERIFY V11C GLASSCORE1] missing: {missing}")
if "UIVisualEffectView" in text or "CADisplayLink" in text:
    raise SystemExit("[VERIFY V11C GLASSCORE1] forbidden per-cell/dynamic effect primitive found")
print("[VERIFY V11C GLASSCORE1] OK")
