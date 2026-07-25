#!/usr/bin/env python3
import os
from pathlib import Path
p = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src")) / "submodules/TelegramCore/Sources/Authorization.swift"
text = p.read_text(encoding="utf-8")
required = [
    "GhostBase v1.1B BOTBACKFILL3 resumable guarded import",
    "GhostBase v1.1B BOTBACKFILL3 trigger",
    "ghostBaseSaveBotBackfillCursor",
    "duplicate start suppressed",
    "location: .UpperHistoryBlock",
    "updates.getDifference(",
]
missing = [x for x in required if x not in text]
forbidden = ["GhostBase v1.1A BOTBACKFILL2 isolated history import", "BOTBOOTSTRAP1 armed pts=0"]
present_forbidden = [x for x in forbidden if x in text]
if missing or present_forbidden:
    raise SystemExit(f"BOTBACKFILL3 verify failed missing={missing} forbidden={present_forbidden}")
print("BOTBACKFILL3 VERIFY OK")
