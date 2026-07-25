#!/usr/bin/env python3
import os
from pathlib import Path

root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
path = root / "submodules/TelegramCore/Sources/UpdatePeers.swift"
if not path.is_file():
    raise SystemExit(f"missing source: {path}")
text = path.read_text(encoding="utf-8")
required = (
    "// MARK: GhostBase v1.1B PRESENCEGLOBAL2 transition archive",
    "private func ghostBasePresenceTransitionKey(",
    "private func ghostBaseCompactPresenceEvents(",
    "guard let event = ghostBasePresenceEvent(presence) else",
    "История присутствия: \\(events.count) переходов",
)
for value in required:
    if value not in text:
        raise SystemExit(f"FAIL missing: {value}")
for forbidden in (
    'status = "нет данных"',
    "previous.lastActivity == event.lastActivity",
    "previous.until == event.until",
):
    if forbidden in text:
        raise SystemExit(f"FAIL forbidden legacy logic: {forbidden}")
print("OK: PRESENCEGLOBAL2 generated source passed structural verification")
