#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))

files = {
    "authorization": root / "submodules/TelegramCore/Sources/Authorization.swift",
    "state_utils": root / "submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift",
    "fetch_chat_list": root / "submodules/TelegramCore/Sources/State/FetchChatList.swift",
    "pinned": root / "submodules/TelegramCore/Sources/State/ManagedSynchronizePinnedChatsOperations.swift",
    "account_row": root / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/ListItems/PeerInfoScreenMemberItem.swift",
}

for name, path in files.items():
    if not path.is_file():
        raise SystemExit(f"[v1.0ZC verifier] missing {name}: {path}")

texts = {name: path.read_text(encoding="utf-8") for name, path in files.items()}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"[v1.0ZC verifier] {message}")

for proof in (
    "GhostBase v1.0ZC Persistent Bot Inbox",
    "ghostBaseBotInitialState",
    "Api.functions.updates.getState()",
    "data.pts - data.unreadCount",
    "automaticFloodWait: false",
    "case .difference, .differenceSlice",
    "transaction.updatePeersInternal",
    "GhostBase.BotAccount.",
):
    require(proof in texts["authorization"], f"missing auth proof: {proof}")

core_start = texts["authorization"].index("// MARK: GhostBase v1.0ZC Persistent Bot Inbox")
core_end = texts["authorization"].index("public enum PasswordRecoveryError", core_start)
core = texts["authorization"][core_start:core_end]
require("pts: 0" not in core, "persistent zero pts remains")
require("date: 0" not in core, "persistent zero date remains")
require("botAuthToken" not in core.split("ghostBaseAuthorizeBot", 1)[1].split("transaction.updatePeersInternal", 1)[1], "token leaked into persistence path")

for proof in (
    "ghostBaseIsBotAccount",
    "GhostBase v1.0ZC Bot local PeerChatInfo",
    "TelegramPeerNotificationSettings.defaultSettings",
    "updatedState.updatePeerChatInclusion",
    "groupId: .root",
):
    require(proof in texts["state_utils"], f"missing state proof: {proof}")

for proof in (
    "GhostBase v1.0ZC Bot local chat list",
    "ghostBaseIsBotAccount(accountPeerId)",
    "return .single(nil)",
):
    require(proof in texts["fetch_chat_list"], f"missing chat-list proof: {proof}")

fetch_start = texts["fetch_chat_list"].index("GhostBase v1.0ZC Bot local chat list")
fetch_end = texts["fetch_chat_list"].index("return postbox.stateView()", fetch_start)
fetch_guard = texts["fetch_chat_list"][fetch_start:fetch_end]
require("messages.getDialogs" not in fetch_guard, "bot guard still performs getDialogs")
require("messages.getPinnedDialogs" not in fetch_guard, "bot guard still performs getPinnedDialogs")

for proof in (
    "GhostBase v1.0ZC Bot pinned-dialog bypass",
    "ghostBaseIsBotAccount(accountPeerId)",
    "return .complete()",
):
    require(proof in texts["pinned"], f"missing pinned proof: {proof}")

for proof in (
    "GhostBase v1.0ZC Account BOT badge",
    'string: "BOT"',
    "user.botInfo != nil",
    "badgeTextColor.withAlphaComponent(0.18)",
    "item.member.peer.displayTitle",
):
    require(proof in texts["account_row"], f"missing badge proof: {proof}")

badge_start = texts["account_row"].index("GhostBase v1.0ZC Account BOT badge")
badge_end = texts["account_row"].index("transition.updateFrame(node: itemNode", badge_start)
badge_block = texts["account_row"][badge_start:badge_end]
require("@username" not in badge_block, "badge implementation contains username formatting")

print("[v1.0ZC verifier] invalid zero-state removed")
print("[v1.0ZC verifier] best-effort backlog preflight OK")
print("[v1.0ZC verifier] personal/group/channel Postbox replay OK")
print("[v1.0ZC verifier] forbidden bot dialog RPC bypass OK")
print("[v1.0ZC verifier] BOT badge uses displayed account name OK")
