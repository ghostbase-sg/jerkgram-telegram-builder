#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

SETTINGS = Path("submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift")
ATTRIBUTE = Path("submodules/TelegramCore/Sources/SyncCore/GhostBaseMessageAttribute.swift")
BLOCKED = Path("submodules/TelegramCore/Sources/TelegramEngine/Privacy/BlockedPeers.swift")
STATE = Path("submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift")
HISTORY = Path("submodules/TelegramUI/Sources/ChatHistoryEntriesForView.swift")
POSTBOX = Path("submodules/Postbox/Sources/Postbox.swift")
PATCHER = Path("scripts/apply_build132_blocked_messages_visibility.py")


def fail(message: str) -> None:
    raise SystemExit(f"[Build132 blocked messages verify] FAIL: {message}")


def read(root: Path, rel: Path) -> str:
    path = root / rel
    if not path.is_file():
        fail(f"missing exact owner: {rel}")
    return path.read_text(encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: verify_build132_blocked_messages_visibility.py <materialized-source-root>")

    root = Path(sys.argv[1]).expanduser().resolve()
    settings = read(root, SETTINGS)
    attribute = read(root, ATTRIBUTE)
    blocked = read(root, BLOCKED)
    state = read(root, STATE)
    history = read(root, HISTORY)
    postbox = read(root, POSTBOX)
    patcher = read(root, PATCHER)

    # STEP4 must retire the irreversible Build131 policy.
    destructive = (
        "JERKGRAM_BUILD131_BLOCKED_GROUP_AUTHOR_PURGE",
        "jerkgramBuild131PurgeBlockedAuthorFromGroupHistories",
        "removeAllMessagesWithAuthor(",
        "JERKGRAM_BUILD131_BLOCKED_GROUP_INGRESS_GATE",
        "jerkgramBuild131ShouldDropIncomingBlockedGroupMessage",
        "messages.removeAll { message in",
    )
    for token in destructive:
        if token in blocked or token in state:
            fail(f"destructive Build131 policy still present: {token}")

    # Separate user-facing toggle in Messages settings.
    for token in (
        "JERKGRAM_BUILD132_HIDE_BLOCKED_MESSAGES_SETTING",
        'static let hideBlockedMessages = "GhostBase.Messages.HideBlockedMessages"',
        "var hideBlockedMessages: Bool",
        "GhostBaseKey.hideBlockedMessages",
        '"Скрывать сообщения заблокированных"',
        "state.hideBlockedMessages",
    ):
        if token not in settings:
            fail(f"Messages toggle/state missing: {token}")

    # Reversible local message state. The existing GhostBase attribute is
    # backwards-compatible because missing `ibh` decodes as false.
    for token in (
        "JERKGRAM_BUILD132_BLOCKED_HIDDEN_ATTRIBUTE",
        "isBlockedHidden: Bool",
        'decodeInt32ForKey("ibh", orElse: 0) != 0',
        'encodeInt32(self.isBlockedHidden ? 1 : 0, forKey: "ibh")',
        "withUpdatedBlockedHidden(isBlockedHidden:",
        "isBlockedHidden: self.isBlockedHidden",
    ):
        if token not in attribute:
            fail(f"reversible blocked-hidden attribute missing: {token}")

    # We reuse Postbox's existing author index, exposed through one bounded
    # Transaction bridge. No chat-history scan is introduced.
    for token in (
        "JERKGRAM_BUILD132_MESSAGE_IDS_WITH_AUTHOR",
        "public func jerkgramMessageIdsWithAuthor(",
        "messageHistoryTable.allIndicesWithAuthor(",
        ").map(\\.id)",
    ):
        if token not in postbox:
            fail(f"Postbox author-index bridge missing: {token}")

    # Block and unblock both mutate the reversible attribute. These
    # transaction.updateMessage calls invalidate MessageHistoryView immediately.
    # Scope remains group/supergroup only, matching the prior Build131 feature.
    for token in (
        "JERKGRAM_BUILD132_BLOCKED_MESSAGE_INVALIDATION",
        "jerkgramBuild132IsGroupOrSupergroup(",
        "peer is TelegramGroup",
        "case .group = channel.info",
        "jerkgramBuild132UpdateBlockedAuthorVisibility(",
        "transaction.jerkgramMessageIdsWithAuthor(",
        "transaction.updateMessage(messageId, update:",
        "hidden: isBlocked",
    ):
        if token not in blocked:
            fail(f"block/unblock invalidation wiring missing: {token}")

    # New incoming group messages are inserted normally and merely annotated.
    for token in (
        "JERKGRAM_BUILD132_BLOCKED_MESSAGE_INGRESS_ANNOTATION",
        "jerkgramBuild132MarkIncomingBlockedGroupMessage",
        "jerkgramBuild132IsGroupOrSupergroup(chatPeer)",
        "messages = messages.map { message in",
        "customStableId: nil",
        "isBlockedHidden: true",
    ):
        if token not in state:
            fail(f"incoming reversible annotation missing: {token}")
    if "message.customStableId" in state:
        fail("ingress annotation must not depend on StoreMessage.customStableId accessor")

    # UI suppression is cheap and reversible: only annotated messages are
    # skipped, and only while the independent setting is enabled.
    for token in (
        "JERKGRAM_BUILD132_BLOCKED_MESSAGE_HISTORY_FILTER",
        'UserDefaults.standard.bool(forKey: "GhostBase.Messages.HideBlockedMessages")',
        "isBlockedHidden",
        "continue loop",
    ):
        if token not in history:
            fail(f"history visibility filter missing: {token}")

    # Scope guard: exact six owners, no source-tree discovery.
    for rel in (SETTINGS, ATTRIBUTE, BLOCKED, STATE, HISTORY, POSTBOX):
        if str(rel) not in patcher:
            fail(f"patcher not bound to exact owner: {rel}")
    if "rglob(" in patcher or ".glob(" in patcher or "os.walk(" in patcher:
        fail("broad source discovery is forbidden")

    # STEP5 belongs to the next task.
    for text, label in (
        (settings, "settings"),
        (attribute, "attribute"),
        (blocked, "blocked"),
        (state, "state"),
        (history, "history"),
        (postbox, "postbox"),
    ):
        if "JERKGRAM_BUILD132_BLOCKED_REACTION" in text:
            fail(f"reaction filtering leaked into STEP4 {label}")

    print("[Build132 blocked messages verify] PASS: reversible storage + author index + group-only toggle + block/unblock invalidation + history filter")


if __name__ == "__main__":
    main()
