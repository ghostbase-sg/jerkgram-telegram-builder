#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
path = root / "submodules/TelegramCore/Sources/TelegramEngine/Payments/StarGifts.swift"
if not path.is_file():
    raise SystemExit(f"[V10ZG GIFTHISTORY1 verifier] missing: {path}")
text = path.read_text(encoding="utf-8")


def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(f"[V10ZG GIFTHISTORY1 verifier] {message}")


for proof in (
    "GhostBase v1.0ZG GIFTHISTORY1 local archive",
    "GhostBase v1.0ZG GIFTHISTORY1 record server page",
    "public struct GhostBaseGiftHistoryEntry",
    "public func ghostBaseGiftHistoryEntries",
    "public func ghostBaseGiftHistoryReport",
    "nameHidden: Bool",
    "savedToProfile: Bool",
    "fromPeerUsername: String?",
    "originalSenderPeerId: Int64?",
    "visibilityHistory: [GhostBaseGiftVisibilityEvent]",
    "filterRawValue: filter.rawValue",
    "entries.count > 1000",
):
    require(proof in text, f"missing proof: {proof}")
require("Api.functions.payments.getSavedStarGifts" in text, "official saved-gifts RPC disappeared")
print("[V10ZG verifier] GIFTHISTORY1 core OK")
