#!/usr/bin/env python3
import os
import re
from pathlib import Path
root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
path = root / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
if not path.is_file():
    raise SystemExit(f"[V11A VERSION] settings source missing: {path}")
text = path.read_text(encoding="utf-8")
text = text.replace("v1.0ZH", "v1.1a").replace("1.0ZH", "1.1a")
text = re.sub(r"Version: v1\.0[A-Z0-9.+-]*", "Version: v1.1a", text)
if "v1.1a" not in text:
    raise SystemExit("[V11A VERSION] version label anchor not found")
path.write_text(text, encoding="utf-8")
print("[V11A] visible version updated to 1.1a")
