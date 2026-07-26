#!/usr/bin/env python3
import os
from pathlib import Path

root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
account_path = root / "submodules/TelegramCore/Sources/Account/Account.swift"
utils_path = root / "submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift"
manager_path = root / "submodules/TelegramCore/Sources/State/AccountStateManager.swift"
for path in (account_path, utils_path, manager_path):
    if not path.exists():
        raise SystemExit(f"[V11E BOTSHADOW1] missing {path}")

account = account_path.read_text(encoding="utf-8")
utils = utils_path.read_text(encoding="utf-8")
manager = manager_path.read_text(encoding="utf-8")

if (
    "GhostBase v1.1E BOTSHADOW1 logout gate" in account
    and "GhostBase v1.1E BOTSHADOW1 state override" in utils
    and "GhostBase v1.1E BOTSHADOW1 official filtered replay" in manager
):
    print("[V11E] BOTSHADOW1 already installed")
    raise SystemExit(0)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"[V11E BOTSHADOW1] {label}: expected 1 anchor, found {count}")
    return text.replace(old, new, 1)

# Remove rejected v1.1D manual messages/chats/users importer.
old_begin = "// MARK: GhostBase v1.1D BOTBACKFILL4 isolated startup import\n"
class_anchor = "public class Account {\n"
if old_begin in account:
    start = account.index(old_begin)
    end = account.index(class_anchor, start)
    account = account[:start] + account[end:]

old_trigger = "        // MARK: GhostBase v1.1D BOTBACKFILL4 startup trigger\n"
if old_trigger in account:
    start = account.index(old_trigger)
    end_anchor = "        /*#if DEBUG\n"
    end = account.index(end_anchor, start)
    account = account[:start] + account[end:]

# Process-local gate: zero cursor never enters Postbox; logout is suppressed only while
# this isolated historical request is in flight.
gate = r'''// MARK: GhostBase v1.1E BOTSHADOW1 logout gate
// This gate is process-local. It never changes account authorization state.
enum GhostBaseBotHistoryGate {
    private static let lock = NSLock()
    private static var activePeerIds = Set<Int64>()

    static func set(peerId: PeerId, active: Bool) {
        self.lock.lock()
        if active {
            self.activePeerIds.insert(peerId.toInt64())
        } else {
            self.activePeerIds.remove(peerId.toInt64())
        }
        self.lock.unlock()
    }

    static func isActive(peerId: PeerId) -> Bool {
        self.lock.lock()
        let result = self.activePeerIds.contains(peerId.toInt64())
        self.lock.unlock()
        return result
    }
}

'''
if "GhostBase v1.1E BOTSHADOW1 logout gate" not in account:
    account = replace_once(account, class_anchor, gate + class_anchor, "Account class")

old_logged_out = '''        self.network.loggedOut = { [weak self] in
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
'''
new_logged_out = '''        self.network.loggedOut = { [weak self] in
            Logger.shared.log("Account", "network logged out")
            if let strongSelf = self {
                if ghostBaseBotSafeMode && GhostBaseBotHistoryGate.isActive(peerId: peerId) {
                    // MARK: GhostBase v1.1E BOTSHADOW1 logout gate
                    // A zero historical cursor may provoke a logout-like transport callback.
                    // Suppress it only for this request; never mark the account logged out.
                    ghostBaseBotSafeRecord(
                        peerId: peerId,
                        event: "BOTSHADOW1 network loggedOut callback suppressed"
                    )
                    return
                }
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
'''
if "BOTSHADOW1 network loggedOut callback suppressed" not in account:
    account = replace_once(account, old_logged_out, new_logged_out, "network.loggedOut")

startup_anchor = "        self.automaticCacheEvictionContext = AutomaticCacheEvictionContext(postbox: postbox, accountManager: accountManager)\n"
startup = r'''

        // MARK: GhostBase v1.1E BOTSHADOW1 startup
        if ghostBaseBotSafeMode && !supplementary {
            Queue.concurrentDefaultQueue().after(1.5) { [weak self] in
                self?.stateManager.ghostBaseStartBotShadowHistory()
            }
        }
'''
if "GhostBase v1.1E BOTSHADOW1 startup" not in account:
    account = replace_once(account, startup_anchor, startup_anchor + startup, "startup")

# Official initial-state builder gets an in-memory shadow state. Existing callers keep
# their exact behavior through default arguments.
old_sig = "func initialStateWithPeerIds(_ transaction: Transaction, peerIds: Set<PeerId>, activeChannelIds: Set<PeerId>, referencedReplyMessageIds: ReferencedReplyMessageIds, referencedGeneralMessageIds: Set<MessageId>, peerIdsRequiringLocalChatState: Set<PeerId>, locallyGeneratedMessageTimestamps: [PeerId: [(MessageId.Namespace, Int32)]], storedStories: [StoryId: UpdatesStoredStory]) -> AccountMutableState {"
new_sig = "func initialStateWithPeerIds(_ transaction: Transaction, peerIds: Set<PeerId>, activeChannelIds: Set<PeerId>, referencedReplyMessageIds: ReferencedReplyMessageIds, referencedGeneralMessageIds: Set<MessageId>, peerIdsRequiringLocalChatState: Set<PeerId>, locallyGeneratedMessageTimestamps: [PeerId: [(MessageId.Namespace, Int32)]], storedStories: [StoryId: UpdatesStoredStory], overrideState: AuthorizedAccountState.State? = nil, resetChannelStates: Bool = false) -> AccountMutableState { // MARK: GhostBase v1.1E BOTSHADOW1 state override"
if "GhostBase v1.1E BOTSHADOW1 state override" not in utils:
    utils = replace_once(utils, old_sig, new_sig, "initialStateWithPeerIds signature")

    old_channel = '''        if peerId.namespace == Namespaces.Peer.CloudChannel {
            if let channelState = transaction.getPeerChatState(peerId) as? ChannelState {
                channelStates[peerId] = AccountStateChannelState(pts: channelState.pts)
            }
'''
    new_channel = '''        if peerId.namespace == Namespaces.Peer.CloudChannel {
            if resetChannelStates {
                channelStates[peerId] = AccountStateChannelState(pts: 0)
            } else if let channelState = transaction.getPeerChatState(peerId) as? ChannelState {
                channelStates[peerId] = AccountStateChannelState(pts: channelState.pts)
            }
'''
    utils = replace_once(utils, old_channel, new_channel, "channel state override")

    old_state = "    let state = AccountMutableState(initialState: AccountInitialState(state: (transaction.getState() as? AuthorizedAccountState)!.state!, peerIds: peerIds,"
    new_state = "    let state = AccountMutableState(initialState: AccountInitialState(state: overrideState ?? (transaction.getState() as? AuthorizedAccountState)!.state!, peerIds: peerIds,"
    utils = replace_once(utils, old_state, new_state, "mutable state override")

    old_diff_sig = "func initialStateWithDifference(postbox: Postbox, difference: Api.updates.Difference) -> Signal<AccountMutableState, NoError> {"
    new_diff_sig = "func initialStateWithDifference(postbox: Postbox, difference: Api.updates.Difference, overrideState: AuthorizedAccountState.State? = nil, resetChannelStates: Bool = false) -> Signal<AccountMutableState, NoError> {"
    utils = replace_once(utils, old_diff_sig, new_diff_sig, "initialStateWithDifference signature")

    old_diff_call = "        return initialStateWithPeerIds(transaction, peerIds: peerIds, activeChannelIds: activeChannelIds, referencedReplyMessageIds: associatedMessageIds.replyIds, referencedGeneralMessageIds: associatedMessageIds.generalIds, peerIdsRequiringLocalChatState: peerIdsRequiringLocalChatState, locallyGeneratedMessageTimestamps: locallyGeneratedMessageTimestampsFromDifference(difference), storedStories: associatedStoredStories(difference))"
    new_diff_call = "        return initialStateWithPeerIds(transaction, peerIds: peerIds, activeChannelIds: activeChannelIds, referencedReplyMessageIds: associatedMessageIds.replyIds, referencedGeneralMessageIds: associatedMessageIds.generalIds, peerIdsRequiringLocalChatState: peerIdsRequiringLocalChatState, locallyGeneratedMessageTimestamps: locallyGeneratedMessageTimestampsFromDifference(difference), storedStories: associatedStoredStories(difference), overrideState: overrideState, resetChannelStates: resetChannelStates)"
    utils = replace_once(utils, old_diff_call, new_diff_call, "initialStateWithDifference call")

# Keep the official default for every normal caller, but let the isolated shadow
# replay avoid channel-reset network work while processing historical slices.
old_final_sig = "func finalStateWithDifference(accountPeerId: PeerId, postbox: Postbox, network: Network, state: AccountMutableState, difference: Api.updates.Difference, asyncResetChannels: (([(peer: Peer, pts: Int32?)]) -> Void)?) -> Signal<AccountFinalState, NoError> {"
new_final_sig = "func finalStateWithDifference(accountPeerId: PeerId, postbox: Postbox, network: Network, state: AccountMutableState, difference: Api.updates.Difference, asyncResetChannels: (([(peer: Peer, pts: Int32?)]) -> Void)?, shouldResetChannels: Bool = true) -> Signal<AccountFinalState, NoError> {"
utils = replace_once(utils, old_final_sig, new_final_sig, "finalStateWithDifference signature")
old_final_return = "    return finalStateWithUpdates(accountPeerId: accountPeerId, postbox: postbox, network: network, state: updatedState, updates: updates, shouldPoll: false, missingUpdates: false, shouldResetChannels: true, updatesDate: nil, asyncResetChannels: asyncResetChannels)"
new_final_return = "    return finalStateWithUpdates(accountPeerId: accountPeerId, postbox: postbox, network: network, state: updatedState, updates: updates, shouldPoll: false, missingUpdates: false, shouldResetChannels: shouldResetChannels, updatesDate: nil, asyncResetChannels: asyncResetChannels)"
utils = replace_once(utils, old_final_return, new_final_return, "finalStateWithDifference reset policy")

# Add the actual shadow replay to the existing official state manager.
if "GhostBase v1.1E BOTSHADOW1 official filtered replay" not in manager:
    property_anchor = "        private let updateEmojiGameInfoDisposable = MetaDisposable()\n"
    manager = replace_once(
        manager,
        property_anchor,
        property_anchor + "        private let ghostBaseBotShadowHistoryDisposable = MetaDisposable()\n",
        "shadow disposable"
    )

    deinit_anchor = "            self.updateEmojiGameInfoDisposable.dispose()\n"
    manager = replace_once(
        manager,
        deinit_anchor,
        deinit_anchor + "            self.ghostBaseBotShadowHistoryDisposable.dispose()\n            GhostBaseBotHistoryGate.set(peerId: self.accountPeerId, active: false)\n",
        "shadow deinit"
    )

    insert_anchor = "        private func insertProcessEvents(_ events: AccountFinalStateEvents) {\n"
    implementation = r'''        // MARK: GhostBase v1.1E BOTSHADOW1 official filtered replay
        private struct GhostBaseBotShadowCursor {
            let state: AuthorizedAccountState.State
            let slice: Int
        }

        private func ghostBaseBotShadowPrefix() -> String {
            return "GhostBase.BotShadow1.\(self.accountPeerId.toInt64())"
        }

        private func ghostBaseBotShadowSet(_ key: String, _ value: Any) {
            UserDefaults.standard.set(value, forKey: self.ghostBaseBotShadowPrefix() + "." + key)
        }

        private func ghostBaseBotShadowRelease() {
            GhostBaseBotHistoryGate.set(peerId: self.accountPeerId, active: false)
            UserDefaults.standard.removeObject(forKey: self.ghostBaseBotShadowPrefix() + ".RunningAt")
        }

        private func ghostBaseBotShadowLoadCursor() -> GhostBaseBotShadowCursor {
            let defaults = UserDefaults.standard
            let prefix = self.ghostBaseBotShadowPrefix() + ".Cursor."
            if defaults.object(forKey: prefix + "pts") != nil {
                let state = AuthorizedAccountState.State(
                    pts: Int32(defaults.integer(forKey: prefix + "pts")),
                    qts: Int32(defaults.integer(forKey: prefix + "qts")),
                    date: Int32(defaults.integer(forKey: prefix + "date")),
                    seq: Int32(defaults.integer(forKey: prefix + "seq"))
                )
                if state.pts != 0 || state.qts != 0 || state.date != 0 || state.seq != 0 {
                    return GhostBaseBotShadowCursor(state: state, slice: defaults.integer(forKey: prefix + "slice"))
                }
            }
            // The all-zero cursor exists only in memory and is never written to Postbox.
            return GhostBaseBotShadowCursor(state: AuthorizedAccountState.State(pts: 0, qts: 0, date: 0, seq: 0), slice: 0)
        }

        private func ghostBaseBotShadowSaveCursor(_ cursor: GhostBaseBotShadowCursor) {
            guard cursor.state.pts != 0 || cursor.state.qts != 0 || cursor.state.date != 0 || cursor.state.seq != 0 else {
                return
            }
            let defaults = UserDefaults.standard
            let prefix = self.ghostBaseBotShadowPrefix() + ".Cursor."
            defaults.set(Int(cursor.state.pts), forKey: prefix + "pts")
            defaults.set(Int(cursor.state.qts), forKey: prefix + "qts")
            defaults.set(Int(cursor.state.date), forKey: prefix + "date")
            defaults.set(Int(cursor.state.seq), forKey: prefix + "seq")
            defaults.set(cursor.slice, forKey: prefix + "slice")
        }

        private func ghostBaseBotShadowClearCursor() {
            let defaults = UserDefaults.standard
            let prefix = self.ghostBaseBotShadowPrefix() + ".Cursor."
            for key in ["pts", "qts", "date", "seq", "slice"] {
                defaults.removeObject(forKey: prefix + key)
            }
        }

        private func ghostBaseBotShadowSafeOperation(_ operation: AccountStateMutationOperation) -> Bool {
            switch operation {
            case .AddMessages,
                 .DeleteMessagesWithGlobalIds,
                 .DeleteMessages,
                 .EditMessage,
                 .UpdateMessagePoll,
                 .UpdateMessageReactions,
                 .UpdateMedia,
                 .MergeApiChats,
                 .UpdatePeer,
                 .UpdateCachedPeerData,
                 .UpdateMessagesPinned,
                 .MergeApiUsers,
                 .UpdateMessageImpressionCount,
                 .UpdateMessageForwardsCount,
                 .UpdateExtendedMedia,
                 .UpdateAudioTranscription:
                return true
            default:
                // In particular: never replay UpdateState, channel pts/state, read
                // state, notification settings, stories, calls or authorization data.
                return false
            }
        }

        private func ghostBaseBotShadowReplay(difference: Api.updates.Difference, cursor: GhostBaseBotShadowCursor) -> Signal<Int, NoError> {
            let accountPeerId = self.accountPeerId
            let accountManager = self.accountManager
            let postbox = self.postbox
            let network = self.network
            let mediaBox = self.postbox.mediaBox
            let auxiliaryMethods = self.auxiliaryMethods
            let messagesRemovedContext = self.messagesRemovedContext

            return postbox.transaction { transaction -> AuthorizedAccountState.State? in
                return (transaction.getState() as? AuthorizedAccountState)?.state
            }
            |> mapToSignal { persistentState -> Signal<Int, NoError> in
                guard let persistentState else {
                    return .single(0)
                }
                return initialStateWithDifference(
                    postbox: postbox,
                    difference: difference,
                    overrideState: cursor.state,
                    resetChannelStates: cursor.slice == 0 && cursor.state.pts == 0
                )
                |> mapToSignal { initialState -> Signal<Int, NoError> in
                    return finalStateWithDifference(
                        accountPeerId: accountPeerId,
                        postbox: postbox,
                        network: network,
                        state: initialState,
                        difference: difference,
                        asyncResetChannels: nil,
                        shouldResetChannels: false
                    )
                    |> mapToSignal { finalState -> Signal<Int, NoError> in
                        var safeFinalState = finalState
                        safeFinalState.state.operations = safeFinalState.state.operations.filter(self.ghostBaseBotShadowSafeOperation)
                        safeFinalState.state.state = persistentState
                        safeFinalState.shouldPoll = false
                        safeFinalState.incomplete = false
                        safeFinalState.missingUpdatesFromChannels.removeAll()
                        safeFinalState.discard = false

                        var messageIds = Set<MessageId>()
                        var minTimestamps: [PeerId: Int32] = [:]
                        for operation in safeFinalState.state.operations {
                            if case let .AddMessages(messages, _) = operation {
                                for message in messages {
                                    if case let .Id(id) = message.id {
                                        messageIds.insert(id)
                                        minTimestamps[id.peerId] = min(minTimestamps[id.peerId] ?? message.timestamp, message.timestamp)
                                    }
                                }
                            }
                        }

                        for (resource, data) in safeFinalState.state.preCachedResources {
                            mediaBox.storeResourceData(resource.id, data: data)
                        }

                        return postbox.transaction { transaction -> (Int, [DeletedMessageId]) in
                            let existingIds = transaction.filterStoredMessageIds(messageIds)
                            guard let replayed = replayFinalState(
                                accountManager: accountManager,
                                postbox: postbox,
                                accountPeerId: accountPeerId,
                                mediaBox: mediaBox,
                                encryptionProvider: network.encryptionProvider,
                                transaction: transaction,
                                auxiliaryMethods: auxiliaryMethods,
                                finalState: safeFinalState,
                                removePossiblyDeliveredMessagesUniqueIds: [:],
                                ignoreDate: true,
                                skipVerification: true
                            ) else {
                                return (0, [])
                            }
                            for (peerId, timestamp) in minTimestamps {
                                updatePeerChatInclusionWithMinTimestamp(
                                    transaction: transaction,
                                    id: peerId,
                                    minTimestamp: timestamp,
                                    forceRootGroupIfNotExists: true
                                )
                            }
                            return (max(0, messageIds.count - existingIds.count), replayed.deletedMessageIds)
                        }
                        |> map { added, deletedIds in
                            if !deletedIds.isEmpty {
                                messagesRemovedContext.addIsMessagesDeletedInteractively(ids: deletedIds)
                                messagesRemovedContext.addIsMessagesDeletedRemotely(ids: deletedIds)
                            }
                            return added
                        }
                    }
                }
            }
        }

        private func ghostBaseBotShadowPage(cursor: GhostBaseBotShadowCursor, importedTotal: Int) -> Signal<Bool, NoError> {
            guard cursor.slice < 96 else {
                self.ghostBaseBotShadowSet("LastResult", "sliceLimit")
                self.ghostBaseBotShadowRelease()
                return .single(false)
            }
            self.ghostBaseBotShadowSet("LastRequest", "pts=\(cursor.state.pts) qts=\(cursor.state.qts) date=\(cursor.state.date) seq=\(cursor.state.seq) slice=\(cursor.slice)")

            return self.network.request(
                Api.functions.updates.getDifference(
                    flags: 0,
                    pts: cursor.state.pts,
                    ptsLimit: nil,
                    ptsTotalLimit: nil,
                    date: cursor.state.date,
                    qts: cursor.state.qts,
                    qtsLimit: nil
                ),
                automaticFloodWait: false
            )
            |> map(Optional.init)
            |> `catch` { error -> Signal<Api.updates.Difference?, NoError> in
                self.ghostBaseBotShadowSet("LastResult", "rpcError")
                self.ghostBaseBotShadowSet("LastErrorCode", Int(error.errorCode))
                self.ghostBaseBotShadowSet("LastError", error.errorDescription ?? "nil")
                Logger.shared.log("GhostBase.BotShadow1", "getDifference failed \(error.errorCode) \(error.errorDescription ?? "nil")")
                self.ghostBaseBotShadowRelease()
                return .single(nil)
            }
            |> mapToSignal { difference -> Signal<Bool, NoError> in
                guard let difference else {
                    return .single(false)
                }
                switch difference {
                case let .difference(data):
                    self.ghostBaseBotShadowSet("LastResult", "difference")
                    self.ghostBaseBotShadowSet("LastMessages", data.newMessages.count)
                    self.ghostBaseBotShadowSet("LastOtherUpdates", data.otherUpdates.count)
                    return self.ghostBaseBotShadowReplay(difference: difference, cursor: cursor)
                    |> map { added in
                        let total = importedTotal + added
                        self.ghostBaseBotShadowSet("Imported", total)
                        self.ghostBaseBotShadowSet("Completed", total > 0)
                        self.ghostBaseBotShadowClearCursor()
                        self.ghostBaseBotShadowRelease()
                        Logger.shared.log("GhostBase.BotShadow1", "final added=\(total)")
                        return total > 0
                    }
                case let .differenceSlice(data):
                    self.ghostBaseBotShadowSet("LastResult", "differenceSlice")
                    self.ghostBaseBotShadowSet("LastMessages", data.newMessages.count)
                    self.ghostBaseBotShadowSet("LastOtherUpdates", data.otherUpdates.count)
                    return self.ghostBaseBotShadowReplay(difference: difference, cursor: cursor)
                    |> mapToSignal { added -> Signal<Bool, NoError> in
                        switch data.intermediateState {
                        case let .state(state):
                            let next = GhostBaseBotShadowCursor(
                                state: AuthorizedAccountState.State(pts: state.pts, qts: state.qts, date: state.date, seq: state.seq),
                                slice: cursor.slice + 1
                            )
                            self.ghostBaseBotShadowSaveCursor(next)
                            return self.ghostBaseBotShadowPage(cursor: next, importedTotal: importedTotal + added)
                        }
                    }
                case .differenceEmpty:
                    self.ghostBaseBotShadowSet("LastResult", "differenceEmpty")
                    self.ghostBaseBotShadowSet("Imported", importedTotal)
                    if importedTotal > 0 {
                        self.ghostBaseBotShadowSet("Completed", true)
                        self.ghostBaseBotShadowClearCursor()
                    }
                    self.ghostBaseBotShadowRelease()
                    return .single(importedTotal > 0)
                case .differenceTooLong:
                    self.ghostBaseBotShadowSet("LastResult", "differenceTooLong")
                    self.ghostBaseBotShadowRelease()
                    Logger.shared.log("GhostBase.BotShadow1", "differenceTooLong; no state mutation and no dialog RPC")
                    return .single(false)
                }
            }
        }

        func ghostBaseStartBotShadowHistory() {
            assert(self.queue.isCurrent())
            let defaults = UserDefaults.standard
            let prefix = self.ghostBaseBotShadowPrefix()
            guard !defaults.bool(forKey: prefix + ".Completed") else {
                return
            }
            let now = Int64(Date().timeIntervalSince1970)
            let runningAt = Int64(defaults.double(forKey: prefix + ".RunningAt"))
            guard runningAt == 0 || now - runningAt > 600 else {
                return
            }
            defaults.set(Double(now), forKey: prefix + ".RunningAt")
            GhostBaseBotHistoryGate.set(peerId: self.accountPeerId, active: true)
            let cursor = self.ghostBaseBotShadowLoadCursor()
            self.ghostBaseBotShadowHistoryDisposable.set((self.ghostBaseBotShadowPage(cursor: cursor, importedTotal: 0)
            |> deliverOn(self.queue)).start())
        }

'''
    manager = replace_once(manager, insert_anchor, implementation + insert_anchor, "manager implementation")

    public_anchor = '''    public func standalonePollDifference() -> Signal<Bool, NoError> {
        return self.impl.signalWith { impl, subscriber in
            return impl.standalonePollDifference().start(next: subscriber.putNext, error: subscriber.putError, completed: subscriber.putCompletion)
        }
    }
'''
    public_block = public_anchor + '''
    // MARK: GhostBase v1.1E BOTSHADOW1 public startup
    public func ghostBaseStartBotShadowHistory() {
        self.impl.with { impl in
            impl.ghostBaseStartBotShadowHistory()
        }
    }
'''
    manager = replace_once(manager, public_anchor, public_block, "public wrapper")

account_path.write_text(account, encoding="utf-8")
utils_path.write_text(utils, encoding="utf-8")
manager_path.write_text(manager, encoding="utf-8")
print("[V11E] BOTSHADOW1 installed: in-memory zero cursor + official filtered replay + logout gate")
