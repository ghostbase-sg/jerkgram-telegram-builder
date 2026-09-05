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
BUILD132_BLOCKED_REACTIONS_APPLY = SCRIPTS / "apply_build132_blocked_reactions_visibility.py"
BUILD132_BLOCKED_REACTIONS_RICH_APPLY = SCRIPTS / "apply_build132_blocked_reactions_rich_data.py"
BUILD132_BLOCKED_REACTION_LIST_APPLY = SCRIPTS / "apply_build132_blocked_reaction_list_filter.py"
BUILD132_BLOCKED_REACTIONS_VERIFY = SCRIPTS / "verify_build132_blocked_reactions_visibility.py"
BUILD132_SETTINGS_AVATAR_PERF_APPLY = SCRIPTS / "apply_build132_settings_avatar_video_perf.py"
BUILD132_SETTINGS_AVATAR_PERF_VERIFY = SCRIPTS / "verify_build132_settings_avatar_video_perf.py"
BUILD132_BUNDLE_IDENTITY_APPLY = SCRIPTS / "apply_build132_bundle_identity.py"
BUILD132_BUNDLE_IDENTITY_VERIFY = SCRIPTS / "verify_build132_active_bundle_identity.py"
BUILD132_TELEGRAM_CLIENT_IDENTITY_APPLY = SCRIPTS / "apply_build132_telegram_client_identity.py"
BUILD132_TELEGRAM_CLIENT_IDENTITY_VERIFY = SCRIPTS / "verify_build132_telegram_client_identity.py"
BUILD132_SIGNER_VERSION_APPLY = SCRIPTS / "apply_build132_signer_version.py"
BUILD132_SIGNER_VERSION_VERIFY = SCRIPTS / "verify_build132_signer_version.py"


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


def verify_python_syntax(*scripts):
    for script in scripts:
        if not script.is_file():
            fail(f"Build132 syntax-gate script missing: {script}")
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", *[str(script) for script in scripts]],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        fail("Build132 telemetry Python syntax gate failed")


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

verify_python_syntax(BUILD132_TELEMETRY_APPLY, BUILD132_TELEMETRY_VERIFY)
print("[Build132 pre-Bazel] PASS: telemetry patcher/verifier Python syntax")

# STEP1: release identity + About
for script in (BUILD132_APPLY, BUILD132_VERIFY):
    run_gate(script)
print("[Build132 pre-Bazel] PASS: release identity + About verifier")

# STEP2: telemetry v2/v2.1 + privacy
for script in (BUILD132_TELEMETRY_APPLY, BUILD132_TELEMETRY_VERIFY):
    run_gate(script)
print("[Build132 pre-Bazel] PASS: telemetry + privacy verifier")

telemetry_owners = (
    ROOT / "submodules/TelegramUI/Sources/AppDelegate.swift",
    ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift",
    ROOT / "submodules/TelegramPresentationData/Sources/JerkgramStrings.swift",
    ROOT / "submodules/TelegramCore/Sources/JerkgramReleaseIdentity.swift",
)
for path in telemetry_owners:
    if not path.is_file():
        fail(f"telemetry idempotence owner missing: {path}")
before_second_apply = {path: path.read_bytes() for path in telemetry_owners}
run_gate(BUILD132_TELEMETRY_APPLY)
after_second_apply = {path: path.read_bytes() for path in telemetry_owners}
if before_second_apply != after_second_apply:
    changed = [str(path.relative_to(ROOT)) for path in telemetry_owners if before_second_apply[path] != after_second_apply[path]]
    fail(f"telemetry second apply is not byte-identical: {changed}")
run_gate(BUILD132_TELEMETRY_VERIFY)
print("[Build132 pre-Bazel] PASS: telemetry second apply is byte-identical")

# STEP3: native Settings footers
for script in (BUILD132_FOOTERS_APPLY, BUILD132_FOOTERS_VERIFY):
    run_gate(script)
print("[Build132 pre-Bazel] PASS: native About/Appearance/Messages footers")

# STEP4: reversible blocked-message visibility
for script in (BUILD132_BLOCKED_MESSAGES_APPLY, BUILD132_BLOCKED_MESSAGES_VERIFY):
    run_gate(script)
print("[Build132 pre-Bazel] PASS: reversible blocked-message visibility + toggle")

# STEP5: blocked reactions in groups/supergroups
for script in (
    BUILD132_BLOCKED_REACTIONS_APPLY,
    BUILD132_BLOCKED_REACTIONS_RICH_APPLY,
    BUILD132_BLOCKED_REACTION_LIST_APPLY,
    BUILD132_BLOCKED_REACTIONS_VERIFY,
):
    run_gate(script)
print("[Build132 pre-Bazel] PASS: blocked reaction visibility + both toggles default OFF")

# STEP6: Settings animated-avatar performance
for script in (BUILD132_SETTINGS_AVATAR_PERF_APPLY, BUILD132_SETTINGS_AVATAR_PERF_VERIFY):
    run_gate(script)
print("[Build132 pre-Bazel] PASS: Settings animated-avatar collapse keeps video content attached")

# STEP7: installed Bundle ID + Telegram network compatibility identity
for script in (
    BUILD132_BUNDLE_IDENTITY_APPLY,
    BUILD132_TELEGRAM_CLIENT_IDENTITY_APPLY,
    BUILD132_BUNDLE_IDENTITY_VERIFY,
    BUILD132_TELEGRAM_CLIENT_IDENTITY_VERIFY,
):
    run_gate(script)
print("[Build132 pre-Bazel] PASS: InstalledIdentity prod/test + TelegramClientIdentity compatibility separation")

# Release-critical invariant: Telegram signer-visible marketing version must stay
# at the upstream base version. This gate intentionally runs last so no older
# patch can leak a Jerkgram product version into CFBundleShortVersionString.
for script in (BUILD132_SIGNER_VERSION_APPLY, BUILD132_SIGNER_VERSION_VERIFY):
    run_gate(script)
print("[Build132 pre-Bazel] PASS: signer-visible Telegram version = 12.9.2")
