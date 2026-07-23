#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
path = root / "submodules/TelegramCore/Sources/UpdatePeers.swift"
if not path.is_file():
    raise SystemExit(f"[V10ZH verifier] missing: {path}")
text = path.read_text(encoding="utf-8")
for proof in (
    "// MARK: GhostBase v1.0ZH PRESENCEHISTORY1 observed presence archive",
    "public struct GhostBasePresenceHistoryEvent",
    "public func ghostBasePresenceHistoryEvents(",
    "public func ghostBasePresenceHistoryReport(",
    "GhostBase.PresenceHistory1.",
    "status = \"онлайн\"",
    "status = \"был недавно\"",
    "lastActivity",
):
    if proof not in text:
        raise SystemExit(f"[V10ZH verifier] PRESENCEHISTORY1 proof missing: {proof}")
if text.count("ghostBaseRecordPresence(") < 4:
    raise SystemExit("[V10ZH verifier] presence recorder is not connected to all update paths")
print("[V10ZH verifier] PRESENCEHISTORY1 OK")
