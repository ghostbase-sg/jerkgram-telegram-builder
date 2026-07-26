#!/usr/bin/env python3
import os
from pathlib import Path

root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
auth = (root / "submodules/TelegramCore/Sources/Authorization.swift").read_text(encoding="utf-8")
account = (root / "submodules/TelegramCore/Sources/Account/Account.swift").read_text(encoding="utf-8")

checks = {
    "BOTBACKFILL3 removed": "BOTBACKFILL3" not in auth and "ghostBaseStartBotBackfill" not in auth,
    "zero cursor absent": "GhostBaseBotBackfillCursor(pts: 0" not in auth,
    "manual UpperHistoryBlock replay absent": "ghostBaseImportBotBackfillPage" not in auth,
    "startup marker": "GhostBase v1.1C BOTSTATE4 startup replay" in account,
    "official replay": "stateManager.standalonePollDifference()" in account,
    "existing bot startup": "if ghostBaseBotSafeMode && !supplementary" in account,
    "duplicate lock": "GhostBase.BotState4." in account and ".RunningAt" in account,
    "forbidden dialog RPC absent": "messages.getDialogs" not in account and "messages.getPinnedDialogs" not in account,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("BOTSTATE4 VERIFY FAILED: " + ", ".join(failed))
print("BOTSTATE4 VERIFY OK")
