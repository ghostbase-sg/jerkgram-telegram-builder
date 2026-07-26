#!/usr/bin/env python3
import os
from pathlib import Path
root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
settings = (root / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift").read_text(encoding="utf-8")
if settings.count("Version: v1.1E-audit") < 1:
    raise SystemExit("[VERIFY V11E VERSION] visible version missing")
if "Base: Official Telegram 12.9.2" not in settings:
    raise SystemExit("[VERIFY V11E VERSION] base missing")
print("[VERIFY V11E VERSION] OK")
