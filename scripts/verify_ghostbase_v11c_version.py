#!/usr/bin/env python3
import os
from pathlib import Path

root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
text = (root / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift").read_text(encoding="utf-8")
if text.count("Version: v1.1C-stage1") != 2:
    raise SystemExit("V11C VERSION VERIFY FAILED: label count")
if "Base: Official Telegram 12.8" in text or "Base: Official Telegram 12.7" in text:
    raise SystemExit("V11C VERSION VERIFY FAILED: stale base")
if text.count("Base: Official Telegram 12.9.2") < 2:
    raise SystemExit("V11C VERSION VERIFY FAILED: base label")
print("V11C VERSION VERIFY OK")
