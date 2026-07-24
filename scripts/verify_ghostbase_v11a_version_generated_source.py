#!/usr/bin/env python3
import os
from pathlib import Path
root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
path = root / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
text = path.read_text(encoding="utf-8")
if "v1.1a" not in text:
    raise SystemExit("[V11A verifier] visible v1.1a label missing")
print("[V11A verifier] version 1.1a OK")
