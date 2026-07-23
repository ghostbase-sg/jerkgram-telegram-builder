#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
path = root / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoProfileItems.swift"
if not path.is_file():
    raise SystemExit(f"[V10ZG PRIVATELINK1 verifier] missing: {path}")
text = path.read_text(encoding="utf-8")


def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(f"[V10ZG PRIVATELINK1 verifier] {message}")


require("GhostBase v1.0ZG PRIVATELINK1 cached exported invite" in text, "marker missing")
require(text.count("cachedData.exportedInvitation?.link") == 2, "channel/group cached invite reads missing")
require("UIPasteboard.general.string = ghostBaseInviteLink" in text, "copy action missing")
require("if let ghostBaseInvitePeer = data.peer" in text, "optional peer is not unwrapped")
require("ghostBaseInvitePeer.id.toInt64()" in text, "unwrapped peer id missing")
require("data.peer.id.toInt64()" not in text, "optional data.peer.id access remains")
start = text.index("GhostBase v1.0ZG PRIVATELINK1 cached exported invite")
block = text[start:start + 3200]
for forbidden in ("exportChatInvite", "getExportedChatInvites", "editExportedChatInvite"):
    require(forbidden not in block, f"forbidden invite-management RPC added: {forbidden}")
print("[V10ZG verifier] PRIVATELINK1 read-only probe OK")
