#!/usr/bin/env python3
import os
from pathlib import Path
root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
text = (root / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift").read_text(encoding="utf-8")
for marker in ["GLOBALGLASSTOGGLE2", "GhostBaseGlassStyle.setEnabled(value)", "полностью возвращает штатные поверхности"]:
    if marker not in text: raise SystemExit(f"[VERIFY V11D SETTINGS] missing {marker}")
print("[VERIFY V11D SETTINGS] OK")
