#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
path = root / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoProfileItems.swift"
if not path.is_file():
    raise SystemExit(f"[V10ZH verifier] missing: {path}")
text = path.read_text(encoding="utf-8")
for proof in (
    "// MARK: GhostBase v1.0ZH PROFILEUI1 integrated profile cards",
    "GhostBase · Подарки",
    "GhostBase · Прикреплённый канал",
    "GhostBase · Присутствие",
    "ghostBasePresenceHistoryReport(",
    "Скопировать полную историю присутствия",
):
    if proof not in text:
        raise SystemExit(f"[V10ZH verifier] PROFILEUI1 proof missing: {proof}")
if text.count("id: 9872001") != 1 or text.count("id: 9872002") != 1 or text.count("id: 9872003") != 1:
    raise SystemExit("[V10ZH verifier] profile card ids are missing or duplicated")
print("[V10ZH verifier] PROFILEUI1 OK")
