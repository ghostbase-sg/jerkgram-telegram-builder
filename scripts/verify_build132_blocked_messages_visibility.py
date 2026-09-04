#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

SETTINGS = Path("submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift")
ATTRIBUTE = Path("submodules/TelegramCore/Sources/SyncCore/GhostBaseMessageAttribute.swift")
BLOCKED = Path("submodules/TelegramCore/Sources/TelegramEngine/Privacy/BlockedPeers.swift")
STATE = Path("submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift")
HISTORY = Path("submodules/TelegramUI/Sources/ChatHistoryEntriesForView.swift")
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
    ):
        if token not in settings:
            fail(f"Messages toggle/state missing: {token}")

    # Reversible local message state. Messages stay in Postbox and can be shown
    # again after unblock; no destructive deletion or ingress drop is allowed.
    for token in (
        "JERKGRAM_BUILD132_BLOCKED_HIDDEN_ATTRIBUTE",
        "isBlockedHidden: Bool",
        'decodeBoolForKey("ibh", orElse: false)',
        'encodeBool(self.isBlockedHidden, forKey: "ibh")',
        "withUpdatedBlockedHidden(isBlockedHidden:",
    ):
        if token not in attribute:
            fail(f"reversible blocked-hidden attribute missing: {token}")

    # Block and unblock must both update stored messages so Postbox history
    # views are invalidated immediately instead of depending on app restart.
    for token in (
        "JERKGRAM_BUILD132_BLOCKED_MESSAGE_INVALIDATION",
        "jerkgramBuild132UpdateBlockedAuthorVisibility(",
        "hidden: isBlocked",
    ):
        if token not in blocked:
            fail(f"block/unblock invalidation wiring missing: {token}")

    # New incoming group messages are inserted normally and merely annotated.
    for token in (
        "JERKGRAM_BUILD132_BLOCKED_MESSAGE_INGRESS_ANNOTATION",
        "jerkgramBuild132MarkIncomingBlockedGroupMessage",
    ):
        if token not in state:
            fail(f"incoming reversible annotation missing: {token}")

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

    # Scope guard: STEP4 patcher is bounded to the five exact owners above.
    for rel in (SETTINGS, ATTRIBUTE, BLOCKED, STATE, HISTORY):
        if str(rel) not in patcher:
            fail(f"patcher not bound to exact owner: {rel}")
    if "rglob(" in patcher or ".glob(" in patcher or "os.walk(" in patcher:
        fail("broad source discovery is forbidden")

    # STEP5 belongs to the next task.
    for text, label in ((settings, "settings"), (attribute, "attribute"), (blocked, "blocked"), (state, "state"), (history, "history")):
        if "JERKGRAM_BUILD132_BLOCKED_REACTION" in text:
            fail(f"reaction filtering leaked into STEP4 {label}")

    print("[Build132 blocked messages verify] PASS: reversible storage + toggle + block/unblock invalidation + history filter")


if __name__ == "__main__":
    main()
