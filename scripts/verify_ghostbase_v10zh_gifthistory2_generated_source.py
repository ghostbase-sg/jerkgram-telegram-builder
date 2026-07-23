#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
path = root / "submodules/TelegramCore/Sources/TelegramEngine/Payments/StarGifts.swift"
if not path.is_file():
    raise SystemExit(f"[V10ZH verifier] missing: {path}")
text = path.read_text(encoding="utf-8")
for proof in (
    "// MARK: GhostBase v1.0ZH GIFTHISTORY2 disappearance state",
    "public var lastSeenVisibleAt: Int64?",
    "public var missingSince: Int64?",
    "snapshotComplete: initialNextOffset == nil && nextOffset == nil",
    "entries[index].missingSince = observedAt",
    "исчез из публичного профиля",
    "GhostBase.GiftHistory2",
):
    if proof not in text:
        raise SystemExit(f"[V10ZH verifier] GIFTHISTORY2 proof missing: {proof}")
if "guard !gifts.isEmpty else" in text[text.index("private func ghostBaseRecordGiftHistory("):]:
    raise SystemExit("[V10ZH verifier] zero-result complete snapshots are still ignored")
print("[V10ZH verifier] GIFTHISTORY2 OK")
