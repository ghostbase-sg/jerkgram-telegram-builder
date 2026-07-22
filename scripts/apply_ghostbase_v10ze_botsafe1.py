#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src"
))

paths = {
    "authorization": root / "submodules/TelegramCore/Sources/Authorization.swift",
    "account": root / "submodules/TelegramCore/Sources/Account/Account.swift",
    "peers": root / "submodules/TelegramCore/Sources/TelegramEngine/Peers/TelegramEnginePeers.swift",
}

for name, path in paths.items():
    if not path.is_file():
        raise SystemExit(f"[BOTSAFE1] missing {name}: {path}")


def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(f"[BOTSAFE1] {message}")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"[BOTSAFE1] {label} anchor count: {count}")
    return text.replace(old, new, 1)


# 1) Use only the exact state returned by updates.getState.
authorization_path = paths["authorization"]
authorization = authorization_path.read_text(encoding="utf-8")
authorization_marker = "// MARK: GhostBase v1.0ZE BOTSAFE1 current server state"

require(
    "// MARK: GhostBase v1.0ZC Persistent Bot Inbox" in authorization,
    "v1.0ZC bot inbox must be applied first"
)

if authorization_marker not in authorization:
    start_marker = "private func ghostBaseBotInitialState(\n"
    end_marker = "public func ghostBaseAuthorizeBot(\n"
    require(start_marker in authorization, "bot initial-state function missing")
    start = authorization.index(start_marker)
    end = authorization.index(end_marker, start)

    replacement = r'''// MARK: GhostBase v1.0ZE BOTSAFE1 current server state
private func ghostBaseBotInitialState(
    account: UnauthorizedAccount
) -> Signal<AuthorizedAccountState.State?, NoError> {
    UserDefaults.standard.set(
        "BOTSAFE1 getState requested",
        forKey: "GhostBase.BotSafe.LastEvent"
    )

    return account.network.request(
        Api.functions.updates.getState(),
        automaticFloodWait: false
    )
    |> map { result -> AuthorizedAccountState.State? in
        switch result {
        case let .state(data):
            UserDefaults.standard.set(
                "BOTSAFE1 getState ok pts=\(data.pts) qts=\(data.qts) date=\(data.date) seq=\(data.seq) unread=\(data.unreadCount)",
                forKey: "GhostBase.BotSafe.LastEvent"
            )

            return AuthorizedAccountState.State(
                pts: data.pts,
                qts: data.qts,
                date: data.date,
                seq: data.seq
            )
        }
    }
    |> `catch` { error -> Signal<AuthorizedAccountState.State?, NoError> in
        UserDefaults.standard.set(
            "BOTSAFE1 getState error code=\(error.errorCode) description=\(error.errorDescription ?? "nil")",
            forKey: "GhostBase.BotSafe.LastEvent"
        )
        return .single(nil)
    }
}

'''
    authorization = authorization[:start] + replacement + authorization[end:]

authorization_path.write_text(authorization, encoding="utf-8")

# 2) Quarantine bot accounts from the normal user background runtime.
account_path = paths["account"]
account = account_path.read_text(encoding="utf-8")
account_marker = "// MARK: GhostBase v1.0ZE BOTSAFE1 account quarantine"

if account_marker not in account:
    account = replace_once(
        account,
        "public class Account {\n",
        r'''// MARK: GhostBase v1.0ZE BOTSAFE1 account quarantine
private func ghostBaseBotSafeModeEnabled(_ peerId: PeerId) -> Bool {
    return UserDefaults.standard.bool(
        forKey: "GhostBase.BotAccount.\(peerId.toInt64())"
    )
}

private func ghostBaseBotSafeRecord(
    peerId: PeerId,
    event: String
) {
    let timestamp = Int64(Date().timeIntervalSince1970)
    let value = "BOTSAFE1 t=\(timestamp) peer=\(peerId.toInt64()) \(event)"
    UserDefaults.standard.set(value, forKey: "GhostBase.BotSafe.LastEvent")
    UserDefaults.standard.set(
        value,
        forKey: "GhostBase.BotSafe.LastEvent.\(peerId.toInt64())"
    )
    Logger.shared.log("BOTSAFE1", value)
}

public class Account {
''',
        "account helper"
    )

    account = replace_once(
        account,
        '''        self.peerId = peerId
        
        self.auxiliaryMethods = auxiliaryMethods
''',
        '''        self.peerId = peerId

        let ghostBaseBotSafeMode = ghostBaseBotSafeModeEnabled(peerId)
        if ghostBaseBotSafeMode {
            ghostBaseBotSafeRecord(
                peerId: peerId,
                event: "account init: quarantine enabled"
            )
        }
        
        self.auxiliaryMethods = auxiliaryMethods
''',
        "safe-mode local"
    )

    account = replace_once(
        account,
        '''        if !supplementary {
            self.filteredStorySubscriptionsContext = StorySubscriptionsContext(accountPeerId: peerId, postbox: postbox, network: network, isHidden: false)
            self.hiddenStorySubscriptionsContext = StorySubscriptionsContext(accountPeerId: peerId, postbox: postbox, network: network, isHidden: true)
        } else {
''',
        '''        if !supplementary && !ghostBaseBotSafeMode {
            self.filteredStorySubscriptionsContext = StorySubscriptionsContext(accountPeerId: peerId, postbox: postbox, network: network, isHidden: false)
            self.hiddenStorySubscriptionsContext = StorySubscriptionsContext(accountPeerId: peerId, postbox: postbox, network: network, isHidden: true)
        } else {
''',
        "story subscriptions"
    )

    account = replace_once(
        account,
        '''        self.taskManager = AccountTaskManager(
            stateManager: self.stateManager,
            accountManager: accountManager,
            networkArguments: networkArguments,
            viewTracker: self.viewTracker,
            mediaReferenceRevalidationContext: self.mediaReferenceRevalidationContext,
            isMainApp: !supplementary,
            testingEnvironment: testingEnvironment
        )
''',
        '''        if ghostBaseBotSafeMode {
            self.taskManager = nil
            ghostBaseBotSafeRecord(
                peerId: peerId,
                event: "AccountTaskManager blocked"
            )
        } else {
            self.taskManager = AccountTaskManager(
                stateManager: self.stateManager,
                accountManager: accountManager,
                networkArguments: networkArguments,
                viewTracker: self.viewTracker,
                mediaReferenceRevalidationContext: self.mediaReferenceRevalidationContext,
                isMainApp: !supplementary,
                testingEnvironment: testingEnvironment
            )
        }
''',
        "task manager"
    )

    account = replace_once(
        account,
        '''        self.accountPresenceManager = AccountPresenceManager(shouldKeepOnlinePresence: self.shouldKeepOnlinePresence.get(), network: network)
''',
        '''        let ghostBasePresenceSignal: Signal<Bool, NoError>
        if ghostBaseBotSafeMode {
            ghostBasePresenceSignal = .single(false)
        } else {
            ghostBasePresenceSignal = self.shouldKeepOnlinePresence.get()
        }
        self.accountPresenceManager = AccountPresenceManager(
            shouldKeepOnlinePresence: ghostBasePresenceSignal,
            network: network
        )
''',
        "presence manager"
    )

    account = replace_once(
        account,
        '''        if !supplementary {
            self.pendingStoryManager = PendingStoryManager(postbox: postbox, network: network, accountPeerId: peerId, stateManager: self.stateManager, messageMediaPreuploadManager: self.messageMediaPreuploadManager, revalidationContext: self.mediaReferenceRevalidationContext, auxiliaryMethods: self.auxiliaryMethods)
        } else {
''',
        '''        if !supplementary && !ghostBaseBotSafeMode {
            self.pendingStoryManager = PendingStoryManager(postbox: postbox, network: network, accountPeerId: peerId, stateManager: self.stateManager, messageMediaPreuploadManager: self.messageMediaPreuploadManager, revalidationContext: self.mediaReferenceRevalidationContext, auxiliaryMethods: self.auxiliaryMethods)
        } else {
''',
        "pending story manager"
    )

    account = replace_once(
        account,
        '''        self.network.loggedOut = { [weak self] in
            Logger.shared.log("Account", "network logged out")
            if let strongSelf = self {
                strongSelf._loggedOut.set(true)
                strongSelf.callSessionManager.dropAll()
            }
        }
        self.network.didReceiveSoftAuthResetError = { [weak self] in
            self?.postSmallLogIfNeeded()
        }
''',
        '''        self.network.loggedOut = { [weak self] in
            Logger.shared.log("Account", "network logged out")
            if let strongSelf = self {
                if ghostBaseBotSafeMode {
                    ghostBaseBotSafeRecord(
                        peerId: peerId,
                        event: "network loggedOut callback"
                    )
                }
                strongSelf._loggedOut.set(true)
                strongSelf.callSessionManager.dropAll()
            }
        }
        self.network.didReceiveSoftAuthResetError = { [weak self] in
            if ghostBaseBotSafeMode {
                ghostBaseBotSafeRecord(
                    peerId: peerId,
                    event: "soft auth reset received"
                )
            } else {
                self?.postSmallLogIfNeeded()
            }
        }
''',
        "network callbacks"
    )

    service_start = '''        self.managedServiceViewsDisposable.set(shouldBeMaster.start(next: { [weak self] value in
'''
    service_end = '''        }))
        
        let pendingMessageManager = self.pendingMessageManager
'''
    require(service_start in account, "service views start missing")
    service_pos = account.index(service_start)
    service_end_pos = account.index(service_end, service_pos) + len("        }))\n")
    service_block = account[service_pos:service_end_pos]
    indented_service = "\n".join(
        ("    " + line) if line else line
        for line in service_block.splitlines()
    )
    service_replacement = '''        if ghostBaseBotSafeMode {
            ghostBaseBotSafeRecord(
                peerId: peerId,
                event: "managedServiceViews blocked"
            )
        } else {
''' + indented_service + '''
        }'''
    account = account[:service_pos] + service_replacement + account[service_end_pos:]

    account = replace_once(
        account,
        '''        self.managedOperationsDisposable.add(managedSecretChatOutgoingOperations(auxiliaryMethods: auxiliaryMethods, postbox: self.postbox, network: self.network, accountPeerId: peerId, mode: .all).start())
''',
        '''        if !ghostBaseBotSafeMode {
            self.managedOperationsDisposable.add(managedSecretChatOutgoingOperations(auxiliaryMethods: auxiliaryMethods, postbox: self.postbox, network: self.network, accountPeerId: peerId, mode: .all).start())
''',
        "heavy operations start"
    )

    account = replace_once(
        account,
        '''        self.managedOperationsDisposable.add(importantBackgroundOperationsRunning.start(next: { [weak self] value in
            if let strongSelf = self {
                strongSelf._importantTasksRunning.set(value)
            }
        }))
        self.managedOperationsDisposable.add((accountManager.sharedData(keys: [SharedDataKeys.proxySettings])
''',
        '''        self.managedOperationsDisposable.add(importantBackgroundOperationsRunning.start(next: { [weak self] value in
            if let strongSelf = self {
                strongSelf._importantTasksRunning.set(value)
            }
        }))
        } else {
            ghostBaseBotSafeRecord(
                peerId: peerId,
                event: "user background operation set blocked"
            )
        }
        self.managedOperationsDisposable.add((accountManager.sharedData(keys: [SharedDataKeys.proxySettings])
''',
        "heavy operations end"
    )

    account = replace_once(
        account,
        '''        self.stateManager.updateConfigRequested = { [weak self] in
            self?.restartConfigurationUpdates()
            self?.taskManager?.reloadAppConfiguration()
        }
        self.restartConfigurationUpdates()
''',
        '''        self.stateManager.updateConfigRequested = { [weak self] in
            if ghostBaseBotSafeMode {
                ghostBaseBotSafeRecord(
                    peerId: peerId,
                    event: "config reload request blocked"
                )
            } else {
                self?.restartConfigurationUpdates()
                self?.taskManager?.reloadAppConfiguration()
            }
        }
        if !ghostBaseBotSafeMode {
            self.restartConfigurationUpdates()
        }
''',
        "configuration updates"
    )

account_path.write_text(account, encoding="utf-8")

# 3) Turn the capability screen into a safe recorder screen.
peers_path = paths["peers"]
peers = peers_path.read_text(encoding="utf-8")
peers_marker = "// MARK: GhostBase v1.0ZE BOTSAFE1 capability guard"

require(
    "// MARK: GhostBase v1.0ZA Bot Account Capability Probe" in peers,
    "bot capability probe missing"
)

if peers_marker not in peers:
    old_local = r'''                    return """
                    LOCAL_STATE
                    accountPeerId: \(String(describing: self.account.peerId))
                    statePeerId: \(String(describing: state.peerId))
                    masterDc: \(state.masterDatacenterId)
                    testing: \(state.isTestingEnvironment)
                    internalState:
                    \(internalState)
                    """
'''
    new_local = r'''                    let botSafeLastEvent = UserDefaults.standard.string(
                        forKey: "GhostBase.BotSafe.LastEvent"
                    ) ?? "nil"

                    return """
                    LOCAL_STATE
                    accountPeerId: \(String(describing: self.account.peerId))
                    statePeerId: \(String(describing: state.peerId))
                    masterDc: \(state.masterDatacenterId)
                    testing: \(state.isTestingEnvironment)
                    internalState:
                    \(internalState)

                    BOTSAFE1
                    quarantine: enabled
                    lastEvent: \(botSafeLastEvent)
                    """
'''
    peers = replace_once(peers, old_local, new_local, "capability recorder")

    probe_start = peers.index("public func ghostBaseBotCapabilityProbe")
    dialogs_start = peers.index("            let dialogs =\n", probe_start)
    signals_start = peers.index(
        "            let signals: [Signal<String, NoError>] = [\n",
        dialogs_start
    )
    guarded = r'''            // MARK: GhostBase v1.0ZE BOTSAFE1 capability guard
            let dialogs = Signal<String, NoError>.single("""
            messages.getDialogs
            blockedBy: BOTSAFE1
            reason: user-only dialog bootstrap is disabled for bot accounts
            """)

            let pinnedDialogs = Signal<String, NoError>.single("""
            messages.getPinnedDialogs
            blockedBy: BOTSAFE1
            reason: user-only pinned synchronization is disabled for bot accounts
            """)

'''
    peers = peers[:dialogs_start] + guarded + peers[signals_start:]

peers_path.write_text(peers, encoding="utf-8")

# Proofs.
for proof in (
    authorization_marker,
    "BOTSAFE1 getState ok",
    "pts: data.pts",
    "date: data.date",
):
    require(proof in authorization, f"authorization proof missing: {proof}")

auth_section = authorization[
    authorization.index(authorization_marker):
    authorization.index("public func ghostBaseAuthorizeBot", authorization.index(authorization_marker))
]
require("candidatePts" not in auth_section, "synthetic candidatePts remains")
require("data.pts - data.unreadCount" not in auth_section, "unreadCount still drives pts")

for proof in (
    account_marker,
    "AccountTaskManager blocked",
    "managedServiceViews blocked",
    "user background operation set blocked",
    "ghostBasePresenceSignal = .single(false)",
):
    require(proof in account, f"account proof missing: {proof}")

for proof in (
    peers_marker,
    "blockedBy: BOTSAFE1",
    "lastEvent:",
):
    require(proof in peers, f"capability proof missing: {proof}")

print("[BOTSAFE1] synthetic backlog state removed")
print("[BOTSAFE1] AccountTaskManager quarantined")
print("[BOTSAFE1] presence/story/service/background managers quarantined")
print("[BOTSAFE1] PendingMessageManager and AccountStateManager preserved")
print("[BOTSAFE1] logout/soft-reset recorder enabled")
print("[BOTSAFE1] forbidden capability RPCs blocked")
