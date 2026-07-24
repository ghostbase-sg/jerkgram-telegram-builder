#!/usr/bin/env python3
import os
from pathlib import Path
root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
path = root / "submodules/TelegramCore/Sources/Authorization.swift"
text = path.read_text(encoding="utf-8")
for proof in (
    "GhostBase v1.1A BOTREPAIR1 live server state",
    "Api.functions.updates.getState()",
    "GhostBase v1.1A BOTBACKFILL2 isolated history import",
    "location: .UpperHistoryBlock",
    "forceRootGroupIfNotExists: true",
    "GhostBase v1.0ZH BOTDEDUPE1 authorization gate",
):
    if proof not in text:
        raise SystemExit(f"[V11A verifier] bot proof missing: {proof}")
for forbidden in (
    "BOTBOOTSTRAP1 armed pts=0",
    "Api.functions.messages.getDialogs(",
    "Api.functions.messages.getPinnedDialogs(",
    "UserDefaults.standard.set(botAuthToken",
):
    if forbidden in text:
        raise SystemExit(f"[V11A verifier] forbidden bot code remains: {forbidden}")
print("[V11A verifier] bot repair/backfill/dedupe OK")
