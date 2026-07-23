#!/usr/bin/env python3

import os
from pathlib import Path

ROOT = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
AUTH = ROOT / "submodules/TelegramCore/Sources/Authorization.swift"
CONTROLLER = ROOT / "submodules/AuthorizationUI/Sources/AuthorizationSequenceController.swift"
ACTIONS = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoScreenSettingsActions.swift"

for name, path in {
    "authorization": AUTH,
    "controller": CONTROLLER,
    "settings actions": ACTIONS,
}.items():
    if not path.is_file():
        raise SystemExit(f"[V10ZH] missing {name}: {path}")


def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(f"[V10ZH] {message}")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"[V10ZH] {label} anchor count: {count}")
    return text.replace(old, new, 1)


# ---------------------------------------------------------------------------
# TelegramCore / Authorization.swift
# ---------------------------------------------------------------------------
auth = AUTH.read_text(encoding="utf-8")
require("// MARK: GhostBase v1.0ZC Persistent Bot Inbox" in auth, "BOT inbox core is missing")
require("// MARK: GhostBase v1.0ZE BOTSAFE1 current server state" in auth, "BOTSAFE1 must run first")

# BOTBOOTSTRAP1: reproduce the exact state that previously restored the bot's
# pre-existing dialogs. It is written only into the fresh unauthorized account
# Postbox. AccountStateManager then advances it to the actual server state while
# replaying Difference slices, so zero is not retained after synchronization.
bootstrap_marker = "// MARK: GhostBase v1.0ZH BOTBOOTSTRAP1 zero-state backlog"
if bootstrap_marker not in auth:
    start_marker = "// MARK: GhostBase v1.0ZE BOTSAFE1 current server state"
    end_marker = "public func ghostBaseAuthorizeBot(\n"
    start = auth.index(start_marker)
    end = auth.index(end_marker, start)
    replacement = r'''// MARK: GhostBase v1.0ZE BOTSAFE1 current server state
// MARK: GhostBase v1.0ZH BOTBOOTSTRAP1 zero-state backlog
private func ghostBaseBotInitialState(
    account: UnauthorizedAccount
) -> Signal<AuthorizedAccountState.State?, NoError> {
    let state = AuthorizedAccountState.State(
        pts: 0,
        qts: 0,
        date: 0,
        seq: 0
    )

    UserDefaults.standard.set(
        "BOTBOOTSTRAP1 armed pts=0 qts=0 date=0 seq=0 account=\(account.id)",
        forKey: "GhostBase.BotBootstrap.LastEvent"
    )
    Logger.shared.log(
        "GhostBase.BotBootstrap1",
        "armed zero-state backlog account=\(account.id) dc=\(account.masterDatacenterId)"
    )

    return .single(state)
}

'''
    auth = auth[:start] + replacement + auth[end:]

# BOTDEDUPE1: Telegram bot tokens begin with the bot's numeric user id. Build a
# normal CloudUser PeerId from that prefix and reuse the existing bot-account
# marker. No token or token hash is persisted.
dedupe_marker = "// MARK: GhostBase v1.0ZH BOTDEDUPE1 token peer id"
if dedupe_marker not in auth:
    anchor = bootstrap_marker + "\n"
    helper = r'''// MARK: GhostBase v1.0ZH BOTDEDUPE1 token peer id
private func ghostBaseBotPeerIdFromToken(
    _ botAuthToken: String
) -> PeerId? {
    guard let separator = botAuthToken.firstIndex(of: ":") else {
        return nil
    }
    guard let rawId = Int64(String(botAuthToken[..<separator])), rawId > 0 else {
        return nil
    }

    return PeerId(
        namespace: Namespaces.Peer.CloudUser,
        id: PeerId.Id._internalFromInt64Value(rawId)
    )
}

private func ghostBaseBotAlreadyAdded(
    _ botAuthToken: String
) -> Bool {
    guard let peerId = ghostBaseBotPeerIdFromToken(botAuthToken) else {
        return false
    }

    return UserDefaults.standard.bool(
        forKey: "GhostBase.BotAccount.\(peerId.toInt64())"
    )
}

'''
    auth = replace_once(auth, anchor, helper + anchor, "BOTDEDUPE1 helper")

if "    case alreadyAdded\n" not in auth:
    auth = replace_once(
        auth,
        "public enum GhostBaseBotAuthorizationError {\n    case invalidToken\n",
        "public enum GhostBaseBotAuthorizationError {\n    case alreadyAdded\n    case invalidToken\n",
        "alreadyAdded enum case",
    )

entry_marker = "// MARK: GhostBase v1.0ZH BOTDEDUPE1 authorization gate"
if entry_marker not in auth:
    auth = replace_once(
        auth,
        ") -> Signal<Never, GhostBaseBotAuthorizationError> {\n    return ghostBaseImportBotAuthorization(\n",
        r''') -> Signal<Never, GhostBaseBotAuthorizationError> {
    // MARK: GhostBase v1.0ZH BOTDEDUPE1 authorization gate
    if ghostBaseBotAlreadyAdded(botAuthToken) {
        Logger.shared.log(
            "GhostBase.BotDedupe1",
            "duplicate bot rejected before import"
        )
        return .fail(.alreadyAdded)
    }

    return ghostBaseImportBotAuthorization(
''',
        "authorization dedupe gate",
    )

AUTH.write_text(auth, encoding="utf-8")

# ---------------------------------------------------------------------------
# Authorization UI: explain the duplicate instead of treating it as bad token.
# ---------------------------------------------------------------------------
controller = CONTROLLER.read_text(encoding="utf-8")
require("private func openGhostBaseBotLogin()" in controller, "bot login UI is missing")
ui_marker = "GhostBase v1.0ZH BOTDEDUPE1 duplicate UI"
if ui_marker not in controller:
    section_start = controller.index("    private func openGhostBaseBotLogin()")
    section_end = controller.index("    private func loadAndPresentPasskey(force: Bool)", section_start)
    section = controller[section_start:section_end]
    old = """                        switch error {
                        case .invalidToken:
"""
    new = """                        switch error {
                        // MARK: GhostBase v1.0ZH BOTDEDUPE1 duplicate UI
                        case .alreadyAdded:
                            text = "Этот бот уже добавлен в GhostBase."

                        case .invalidToken:
"""
    count = section.count(old)
    if count != 1:
        raise SystemExit(f"[V10ZH] duplicate UI switch anchor count: {count}")
    section = section.replace(old, new, 1)
    controller = controller[:section_start] + section + controller[section_end:]
CONTROLLER.write_text(controller, encoding="utf-8")

# ---------------------------------------------------------------------------
# Bot logout: clear the peer marker so the same bot can be added again after a
# real user-requested logout. The token itself was never stored.
# ---------------------------------------------------------------------------
actions = ACTIONS.read_text(encoding="utf-8")
require("// MARK: GhostBase v1.0ZG BOTLOGOUT1" in actions, "Build 85 bot logout must run first")
logout_marker = "// MARK: GhostBase v1.0ZH BOTDEDUPE1 clear marker on logout"
if logout_marker not in actions:
    start = actions.index("// MARK: GhostBase v1.0ZG BOTLOGOUT1")
    end = actions.index("        case .rememberPassword:", start)
    section = actions[start:end]
    old = """                                        let _ = logoutFromAccount(
"""
    new = r'''                                        // MARK: GhostBase v1.0ZH BOTDEDUPE1 clear marker on logout
                                        UserDefaults.standard.removeObject(
                                            forKey: "GhostBase.BotAccount.\(user.id.toInt64())"
                                        )
                                        let _ = logoutFromAccount(
'''
    count = section.count(old)
    if count != 1:
        raise SystemExit(f"[V10ZH] bot logout cleanup anchor count: {count}")
    section = section.replace(old, new, 1)
    actions = actions[:start] + section + actions[end:]
ACTIONS.write_text(actions, encoding="utf-8")

print("[V10ZH] BOTBOOTSTRAP1 applied: fresh bot account starts at zero state")
print("[V10ZH] BOTDEDUPE1 applied: duplicate bot id rejected without storing token")
