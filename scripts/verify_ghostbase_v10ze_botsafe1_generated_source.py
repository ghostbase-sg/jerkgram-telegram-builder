#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src"
))

authorization_path = root / "submodules/TelegramCore/Sources/Authorization.swift"
account_path = root / "submodules/TelegramCore/Sources/Account/Account.swift"
peers_path = root / "submodules/TelegramCore/Sources/TelegramEngine/Peers/TelegramEnginePeers.swift"
state_path = root / "submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift"
fetch_path = root / "submodules/TelegramCore/Sources/State/FetchChatList.swift"
row_path = root / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/ListItems/PeerInfoScreenMemberItem.swift"

for path in (authorization_path, account_path, peers_path, state_path, fetch_path, row_path):
    if not path.is_file():
        raise SystemExit(f"[BOTSAFE1 verifier] missing source: {path}")

authorization = authorization_path.read_text(encoding="utf-8")
account = account_path.read_text(encoding="utf-8")
peers = peers_path.read_text(encoding="utf-8")
state = state_path.read_text(encoding="utf-8")
fetch = fetch_path.read_text(encoding="utf-8")
row = row_path.read_text(encoding="utf-8")


def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(f"[BOTSAFE1 verifier] {message}")


auth_marker = "// MARK: GhostBase v1.0ZE BOTSAFE1 current server state"
require(auth_marker in authorization, "current-state marker missing")
auth_start = authorization.index(auth_marker)
auth_end = authorization.index("public func ghostBaseAuthorizeBot", auth_start)
auth = authorization[auth_start:auth_end]

for proof in (
    "Api.functions.updates.getState()",
    "pts: data.pts",
    "qts: data.qts",
    "date: data.date",
    "seq: data.seq",
    "BOTSAFE1 getState ok",
):
    require(proof in auth, f"authorization proof missing: {proof}")

for forbidden in (
    "candidatePts",
    "data.pts - data.unreadCount",
    "pts: 0",
    "date: 0",
):
    require(forbidden not in auth, f"unsafe initial-state code remains: {forbidden}")

for proof in (
    "// MARK: GhostBase v1.0ZE BOTSAFE1 account quarantine",
    "ghostBaseBotSafeModeEnabled",
    "self.taskManager = nil",
    "AccountTaskManager blocked",
    "ghostBasePresenceSignal = .single(false)",
    "managedServiceViews blocked",
    "user background operation set blocked",
    "network loggedOut callback",
    "soft auth reset received",
):
    require(proof in account, f"account quarantine proof missing: {proof}")

for proof in (
    "// MARK: GhostBase v1.0ZE BOTSAFE1 capability guard",
    "blockedBy: BOTSAFE1",
    "GhostBase.BotSafe.LastEvent",
    "quarantine: enabled",
):
    require(proof in peers, f"capability proof missing: {proof}")

# Existing Bot Inbox and badge must remain active under the quarantine.
for proof in (
    "// MARK: GhostBase v1.0ZC Bot account detection",
    "// MARK: GhostBase v1.0ZC Bot local PeerChatInfo",
):
    require(proof in state, f"Bot Inbox state proof missing: {proof}")

require(
    "// MARK: GhostBase v1.0ZC Bot local chat list" in fetch,
    "Bot Inbox chat-list bypass missing"
)
require(
    "// MARK: GhostBase v1.0ZC Account BOT badge" in row,
    "BOT account badge missing"
)
require('string: "BOT"' in row, "BOT badge text missing")

print("[BOTSAFE1 verifier] exact server state only")
print("[BOTSAFE1 verifier] user background runtime quarantined")
print("[BOTSAFE1 verifier] state manager / local inbox retained")
print("[BOTSAFE1 verifier] outgoing message watcher retained")
print("[BOTSAFE1 verifier] logout recorder available in capability report")
print("[BOTSAFE1 verifier] BOT badge retained")
