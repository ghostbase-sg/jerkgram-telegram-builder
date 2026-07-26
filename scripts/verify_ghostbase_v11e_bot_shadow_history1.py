#!/usr/bin/env python3
import os
from pathlib import Path
root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
account = (root / "submodules/TelegramCore/Sources/Account/Account.swift").read_text(encoding="utf-8")
utils = (root / "submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift").read_text(encoding="utf-8")
manager = (root / "submodules/TelegramCore/Sources/State/AccountStateManager.swift").read_text(encoding="utf-8")
required_account = [
    "GhostBase v1.1E BOTSHADOW1 logout gate",
    "BOTSHADOW1 network loggedOut callback suppressed",
    "stateManager.ghostBaseStartBotShadowHistory()",
]
for value in required_account:
    if value not in account:
        raise SystemExit(f"[VERIFY V11E BOTSHADOW1] account marker missing {value}")
for value in [
    "overrideState: AuthorizedAccountState.State? = nil",
    "resetChannelStates: Bool = false",
    "state: overrideState ??",
    "shouldResetChannels: Bool = true",
    "shouldResetChannels: shouldResetChannels",
]:
    if value not in utils:
        raise SystemExit(f"[VERIFY V11E BOTSHADOW1] shadow state support missing {value}")
for value in [
    "GhostBase v1.1E BOTSHADOW1 official filtered replay",
    "finalStateWithDifference(",
    "replayFinalState(",
    "skipVerification: true",
    "shouldResetChannels: false",
    "safeFinalState.state.operations = safeFinalState.state.operations.filter",
    "safeFinalState.state.state = persistentState",
    "forceRootGroupIfNotExists: true",
    ".UpdateMessageReactions",
    "case .differenceTooLong",
]:
    if value not in manager:
        raise SystemExit(f"[VERIFY V11E BOTSHADOW1] official shadow replay missing {value}")
for forbidden in ["messages.getDialogs", "messages.getPinnedDialogs", "candidatePts", "transaction.setState(AuthorizedAccountState", "BOTBACKFILL4 isolated startup import"]:
    if forbidden in manager + account:
        raise SystemExit(f"[VERIFY V11E BOTSHADOW1] forbidden legacy behavior remains: {forbidden}")
# Permanent state must be explicitly filtered, not replayed from the zero cursor.
filter_region = manager[manager.index("private func ghostBaseBotShadowSafeOperation"):manager.index("private func ghostBaseBotShadowReplay")]
if "case .UpdateState" in filter_region or "case .UpdateChannelState" in filter_region:
    raise SystemExit("[VERIFY V11E BOTSHADOW1] persistent state operation was whitelisted")
print("[VERIFY V11E BOTSHADOW1] OK")
