#!/usr/bin/env python3
import os
from pathlib import Path
root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
text = (root / "submodules/Display/Source/GhostBaseGlass.swift").read_text(encoding="utf-8")
for marker in ["GhostBase v1.1D GLASSCORE2", "ghostBaseGlassDidChange", "setActiveTintColor", "usesReducedEffects"]:
    if marker not in text:
        raise SystemExit(f"[VERIFY V11D GLASSCORE2] missing {marker}")
print("[VERIFY V11D GLASSCORE2] OK")
