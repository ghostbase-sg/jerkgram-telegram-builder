#!/usr/bin/env python3
"""Fast structural verifier for Build131 plus approved Build132 pre-Bazel gates."""
from pathlib import Path
import os
import subprocess
import sys


ROOT = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", os.environ.get("JERKGRAM_SRC", "/root/gb_builder/work/swiftgram-src")))
BLOCKED = ROOT / "submodules/TelegramCore/Sources/TelegramEngine/Privacy/BlockedPeers.swift"
STATE = ROOT / "submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift"
SCRIPTS = Path(__file__).resolve().parent
BUILD132_APPLY = SCRIPTS / "apply_build132_release_identity_about.py"
BUILD132_VERIFY = SCRIPTS / "verify_build132_release_identity_about.py"
BUILD132_TELEMETRY_APPLY = SCRIPTS / "apply_build132_telemetry_v2.py"
BUILD132_TELEMETRY_VERIFY = SCRIPTS / "verify_build132_telemetry_v2.py"
BUILD132_FOOTERS_APPLY = SCRIPTS / "apply_build132_native_settings_footers.py"
BUILD132_FOOTERS_VERIFY = SCRIPTS / "verify_build132_native_settings_footers.py"
BUILD132_BLOCKED_MESSAGES_APPLY = SCRIPTS / "apply_build132_blocked_messages_visibility.py"
BUILD132_BLOCKED_MESSAGES_VERIFY = SCRIPTS / "verify_build132_blocked_messages_visibility.py"


def fail(message):
    raise SystemExit(f"[Build131 verify] FAIL: {message}")


def run_gate(script):
    if not script.is_file():
        fail(f"Build132 gate script missing: {script}")
    result = subprocess.run(
        [sys.executable, str(script), str(ROOT)],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        fail(f"Build132 gate failed in {script.name} with exit {result.returncode}")


for path in (BLOCKED, STATE):
    if not path.is_file():
        fail(f"missing {path}")

blocked = BLOCKED.read_text(encoding="utf-8")
state = STATE.read_text(encoding="utf-8")

step4_blocked = "JERKGRAM_BUILD132_BLOCKED_MESSAGE_INVALIDATION" in blocked
step4_state = "JERKGRAM_BUILD132_BLOCKED_MESSAGE_INGRESS_ANNOTATION" in state
if step4_blocked != step4_state:
    fail("partial Build132 STEP4 state: blocked/state markers disagree")

if step4_blocked:
    for token in (
        "JERKGRAM_BUILD131_BLOCKED_GROUP_AUTHOR_PURGE",
        "jerkgramBuild131PurgeBlockedAuthorFromGroupHistories",
        "JERKGRAM_BUILD131_BLOCKED_GROUP_INGRESS_GATE",
        "jerkgramBuild131ShouldDropIncomingBlockedGroupMessage",
        "messages.removeAll { message in",
    ):
        if token in blocked or token in state:
            fail(f"obsolete destructive Build131 token survived STEP4: {token}")
    print("[Build131 verify] PASS: destructive policy superseded by reversible Build132 STEP4")
else:
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

# Approved Build132 chain only. Later numbered steps remain intentionally
# unwired until the user explicitly approves each one.

# JERKGRAM_BUILD132_RELEASE_IDENTITY_PREBAZEL_HOOK
for script in (BUILD132_APPLY, BUILD132_VERIFY):
    run_gate(script)
print("[Build132 pre-Bazel] PASS: release identity + About verifier")

# JERKGRAM_BUILD132_TELEMETRY_V2_PREBAZEL_HOOK
for script in (BUILD132_TELEMETRY_APPLY, BUILD132_TELEMETRY_VERIFY):
    run_gate(script)
print("[Build132 pre-Bazel] PASS: telemetry v2 + privacy verifier")

# JERKGRAM_BUILD132_NATIVE_SETTINGS_FOOTERS_PREBAZEL_HOOK
for script in (BUILD132_FOOTERS_APPLY, BUILD132_FOOTERS_VERIFY):
    run_gate(script)
print("[Build132 pre-Bazel] PASS: native About/Appearance/Messages footers")

# JERKGRAM_BUILD132_BLOCKED_MESSAGES_VISIBILITY_PREBAZEL_HOOK
for script in (BUILD132_BLOCKED_MESSAGES_APPLY, BUILD132_BLOCKED_MESSAGES_VERIFY):
    run_gate(script)
print("[Build132 pre-Bazel] PASS: reversible blocked-message visibility + toggle")

print("[Build132 pre-Bazel] STOP: approved chain ends after STEP4; STEP5-STEP7 remain unwired")
