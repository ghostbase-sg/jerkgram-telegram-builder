#!/usr/bin/env python3
"""Fast structural verifier for the Build131 core policy."""
from pathlib import Path
import os


ROOT = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", os.environ.get("JERKGRAM_SRC", "/root/gb_builder/work/swiftgram-src")))
BLOCKED = ROOT / "submodules/TelegramCore/Sources/TelegramEngine/Privacy/BlockedPeers.swift"
STATE = ROOT / "submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift"


def fail(message):
    raise SystemExit(f"[Build131 verify] FAIL: {message}")


for path in (BLOCKED, STATE):
    if not path.is_file():
        fail(f"missing {path}")

blocked = BLOCKED.read_text(encoding="utf-8")
state = STATE.read_text(encoding="utf-8")

required_blocked = (
    "JERKGRAM_BUILD131_BLOCKED_GROUP_AUTHOR_PURGE",
    "transaction.chatListGetAllPeerIds()",
    "transaction.removeAllMessagesWithAuthor(",
    "authorId: authorId",
    "namespace: Namespaces.Message.Cloud",
    "if isBlocked {\n                                jerkgramBuild131PurgeBlockedAuthorFromGroupHistories",
)
for marker in required_blocked:
    if marker not in blocked:
        fail(f"BlockedPeers marker missing: {marker}")

required_state = (
    "JERKGRAM_BUILD131_BLOCKED_GROUP_INGRESS_GATE",
    "case let .AddMessages(messagesValue, location):",
    "var messages = messagesValue",
    "messages.removeAll { message in",
    "jerkgramBuild131ShouldDropIncomingBlockedGroupMessage(transaction: transaction, message: message)",
    "if case .UpperHistoryBlock = location {\n                    for message in messages {",
)
for marker in required_state:
    if marker not in state:
        fail(f"AccountState marker missing: {marker}")

if "var messages = messages\n" in state:
    fail("obsolete duplicate AddMessages binding remains")
if "UserDefaults" in blocked or "UserDefaults" in state[state.index("JERKGRAM_BUILD131_BLOCKED_GROUP_INGRESS_GATE"):state.index("func replayFinalState(")]:
    fail("policy must not use UserDefaults in transaction path")
if "ChatHistoryEntriesForView" in blocked or "ChatListNodeEntries" in state:
    fail("policy must not install a UI scroll/list filter")

print("[Build131 verify] PASS: indexed purge + pre-insert ingress gate")
