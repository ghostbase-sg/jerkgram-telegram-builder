#!/usr/bin/env python3
import os
from pathlib import Path
root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
path = root / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
text = path.read_text(encoding="utf-8")
if "Version: v1.1D-reference" in text:
    print("[V11D] version already installed")
    raise SystemExit(0)
for old in ["Version: v1.1C-stage1", "Version: v1.1a"]:
    if old in text:
        text = text.replace(old, "Version: v1.1D-reference")
text = text.replace("Base: Official Telegram 12.8", "Base: Official Telegram 12.9.2")
text = text.replace("Base: Official Telegram 12.7", "Base: Official Telegram 12.9.2")
path.write_text(text, encoding="utf-8")
print("[V11D] visible version updated to v1.1D-reference")
