#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
path = root / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoProfileItems.swift"
if not path.is_file():
    raise SystemExit(f"[V10ZG GIFTHISTORY1 UI verifier] missing: {path}")
text = path.read_text(encoding="utf-8")
for proof in (
    "GhostBase v1.0ZG GIFTHISTORY1 profile action",
    "ghostBaseGiftHistoryEntries(",
    "ghostBaseGiftHistoryReport(",
    "История подарков GhostBase",
    "UIPasteboard.general.string",
):
    if proof not in text:
        raise SystemExit(f"[V10ZG GIFTHISTORY1 UI verifier] missing proof: {proof}")
print("[V10ZG verifier] GIFTHISTORY1 UI OK")
