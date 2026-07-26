#!/usr/bin/env python3
import os
from pathlib import Path
root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
path = root / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
text = path.read_text(encoding="utf-8")
required = [
    "GhostBase v1.1C SETTINGSGLASS1",
    'static let glassEnabled = "GhostBase.Glass.Enabled"',
    "var glassEnabled: Bool",
    "GhostBaseKey.glassEnabled,\n                defaultValue: true",
    '"GhostBase Glass"',
    "case GhostBaseKey.glassEnabled:",
]
missing = [x for x in required if x not in text]
if missing:
    raise SystemExit(f"[VERIFY V11C SETTINGSGLASS1] missing: {missing}")
if text.count('"GhostBase Glass"') != 1:
    raise SystemExit("[VERIFY V11C SETTINGSGLASS1] expected exactly one user-facing toggle")
print("[VERIFY V11C SETTINGSGLASS1] OK")
