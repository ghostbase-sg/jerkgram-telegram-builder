#!/usr/bin/env python3
import os
from pathlib import Path

root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
path = root / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
text = path.read_text(encoding="utf-8")

if "Version: v1.1C-stage1" in text:
    print("[V11C] version already installed")
    raise SystemExit(0)

if text.count("Version: v1.1a") != 2:
    raise SystemExit("[V11C VERSION] expected exactly two v1.1a labels")
text = text.replace("Version: v1.1a", "Version: v1.1C-stage1")
text = text.replace("Base: Official Telegram 12.8", "Base: Official Telegram 12.9.2")
text = text.replace("Base: Official Telegram 12.7", "Base: Official Telegram 12.9.2")
path.write_text(text, encoding="utf-8")
print("[V11C] visible version updated to v1.1C-stage1 / Official Telegram 12.9.2")
