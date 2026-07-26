#!/usr/bin/env python3
import os
from pathlib import Path
root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
auth = (root / "submodules/TelegramCore/Sources/Authorization.swift").read_text(encoding="utf-8")
account = (root / "submodules/TelegramCore/Sources/Account/Account.swift").read_text(encoding="utf-8")
for marker in ["BOTBACKFILL4 isolated startup import", "BOTBACKFILL4 startup trigger", "location: .UpperHistoryBlock", "forceRootGroupIfNotExists: true", "total > 0", "no account-state mutation"]:
    if marker not in account: raise SystemExit(f"[VERIFY V11D BOT] missing {marker}")
for forbidden in ["candidatePts", "messages.getDialogs", "messages.getPinnedDialogs", "transaction.setState(state)"]:
    # setState exists elsewhere in authorization legitimately; only forbid it in the new Account helper.
    if forbidden == "transaction.setState(state)":
        helper = account.split("// MARK: GhostBase v1.1D BOTBACKFILL4 isolated startup import", 1)[1].split("public class Account", 1)[0]
        if forbidden in helper: raise SystemExit("[VERIFY V11D BOT] backfill mutates account state")
    elif forbidden in account.split("// MARK: GhostBase v1.1D BOTBACKFILL4 isolated startup import", 1)[1].split("public class Account", 1)[0]:
        raise SystemExit(f"[VERIFY V11D BOT] forbidden {forbidden}")
if "BOTBACKFILL3 resumable guarded import" in auth: raise SystemExit("[VERIFY V11D BOT] BOTBACKFILL3 remains")
if "BOTSTATE4 startup replay" in account: raise SystemExit("[VERIFY V11D BOT] rejected BOTSTATE4 remains")
print("[VERIFY V11D BOT] OK")
