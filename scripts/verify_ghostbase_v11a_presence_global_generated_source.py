#!/usr/bin/env python3
import os
from pathlib import Path
root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
path = root / "submodules/TelegramCore/Sources/UpdatePeers.swift"
text = path.read_text(encoding="utf-8")
for proof in (
    "GhostBase v1.1A PRESENCEGLOBAL1 known-user registry",
    "public struct GhostBaseKnownUser",
    "ghostBaseRegisterKnownUser(",
    "GhostBase.PresenceGlobal1.KnownUserIds.",
    "TelegramUserPresence(status: .none",
    "public func ghostBaseKnownUsersReport",
):
    if proof not in text:
        raise SystemExit(f"[V11A verifier] presence proof missing: {proof}")
print("[V11A verifier] global presence registry OK")
