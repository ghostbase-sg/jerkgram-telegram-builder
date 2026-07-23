#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
path = root / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoProfileItems.swift"
if not path.is_file():
    raise SystemExit(f"[V10ZG PROFILEINTEL3 verifier] missing: {path}")
text = path.read_text(encoding="utf-8")


def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(f"[V10ZG PROFILEINTEL3 verifier] {message}")


for proof in (
    "GhostBase v1.0ZG PROFILEINTEL3 personal channel storage",
    "GhostBase v1.0ZG PROFILEINTEL3 observe personal channel",
    "GhostBase v1.0ZG PROFILEINTEL3 history action",
    "channelPeerId: channelPeer?.id.toInt64()",
    "title: channelPeer?.compactDisplayTitle",
    "username: username",
    "subscriberCount: personalChannel?.subscriberCount",
    "topMessageId: personalChannel?.topMessages.first?.id.id",
    "meaningfulChange",
    "events.count > 200",
):
    require(proof in text, f"missing proof: {proof}")
print("[V10ZG verifier] PROFILEINTEL3 personal channel OK")
