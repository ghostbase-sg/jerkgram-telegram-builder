#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
files = {
    "search": root / "submodules/SettingsUI/Sources/Search/SettingsSearchableItems.swift",
    "delete": root / "submodules/SettingsUI/Sources/DeleteAccountOptionsController.swift",
    "actions": root / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoScreenSettingsActions.swift",
}
texts = {}
for name, path in files.items():
    if not path.is_file():
        raise SystemExit(f"[V10ZG account verifier] missing {name}: {path}")
    texts[name] = path.read_text(encoding="utf-8")


def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(f"[V10ZG account verifier] {message}")


require("GhostBase v1.0ZG ACCOUNTUNLOCK1 settings search" in texts["search"], "settings marker missing")
require("accountsAndPeers.1.count + 1 < maximumNumberOfAccounts" not in texts["search"], "settings account gate remains")
require("GhostBase v1.0ZG ACCOUNTUNLOCK1 delete alternatives" in texts["delete"], "delete marker missing")
require("accountsAndPeers.1.count + 1 < maximumNumberOfAccounts" not in texts["delete"], "delete account gate remains")

actions = texts["actions"]
require("GhostBase v1.0ZG ACCOUNTUNLOCK1 main action" in actions, "main action marker missing")
require("GhostBase v1.0ZG BOTLOGOUT1" in actions, "bot logout marker missing")
add_start = actions.index("GhostBase v1.0ZG ACCOUNTUNLOCK1 main action")
logout_start = actions.index("GhostBase v1.0ZG BOTLOGOUT1")
add_block = actions[add_start:logout_start]
require("PremiumLimitScreen" not in add_block, "PremiumLimitScreen remains in Add Account branch")
require("maximumAvailableAccounts" not in add_block, "hardcoded 3/4 account limit remains")
require("beginNewAuth" in add_block, "beginNewAuth missing")
logout_block = actions[logout_start:actions.index("case .rememberPassword", logout_start)]
require("user.botInfo != nil" in logout_block, "bot detection missing")
require("logoutFromAccount(" in logout_block, "standard logout cleanup missing")
require("alreadyLoggedOutRemotely: true" in logout_block, "bot logout is not local-only")
print("[V10ZG verifier] ACCOUNTUNLOCK1 + BOTLOGOUT1 OK")
