#!/usr/bin/env python3
import os
from pathlib import Path
root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/ports/ghostbase_12_9_2_port/telegram-ios-12.9.2-official"))
p = root / "submodules/TelegramCore/Sources/TelegramEngine/Payments/StarGifts.swift"
text = p.read_text(encoding="utf-8")
required = ["GhostBase v1.1B HIDDENGIFTS1", "ghostBaseHiddenGiftHistoryEntries", "ghostBaseHiddenGiftHistoryReport", "!entry.savedToProfile"]
missing = [x for x in required if x not in text]
if missing: raise SystemExit("[VERIFY HIDDENGIFTS1] missing: " + ", ".join(missing))
print("[VERIFY HIDDENGIFTS1] OK")
