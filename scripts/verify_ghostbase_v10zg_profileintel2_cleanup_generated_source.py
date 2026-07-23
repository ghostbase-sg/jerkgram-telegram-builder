#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
path = root / "submodules/TelegramCore/Sources/TelegramEngine/Peers/TelegramEnginePeers.swift"
if not path.is_file():
    raise SystemExit(f"[V10ZG PROFILEINTEL2 cleanup verifier] missing: {path}")

text = path.read_text(encoding="utf-8")
marker = "GhostBase v1.0ZG PROFILEINTEL2 no-change events are report-only"
phrase = "Изменений с прошлого снимка нет"

if marker not in text:
    raise SystemExit("[V10ZG PROFILEINTEL2 cleanup verifier] marker missing")

position = 0
while True:
    position = text.find(phrase, position)
    if position == -1:
        break
    window = text[max(0, position - 1500): position + 300]
    if "events.append(" in window:
        raise SystemExit(
            "[V10ZG PROFILEINTEL2 cleanup verifier] no-change phrase is still near events.append"
        )
    position += len(phrase)

print("[V10ZG verifier] PROFILEINTEL2 no-change cleanup OK")
