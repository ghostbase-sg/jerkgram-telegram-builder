#!/usr/bin/env python3
import os
from pathlib import Path
root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
auth_path = root / "submodules/TelegramCore/Sources/Authorization.swift"
account_path = root / "submodules/TelegramCore/Sources/Account/Account.swift"
auth = auth_path.read_text(encoding="utf-8")
account = account_path.read_text(encoding="utf-8")

# Remove BOTBACKFILL3 when v1.1C is not in the chain, and remove rejected BOTSTATE4.
marker = "// MARK: GhostBase v1.1B BOTBACKFILL3 resumable guarded import\n"
if marker in auth:
    start = auth.index(marker)
    end = auth.index("public func ghostBaseAuthorizeBot(\n", start)
    auth = auth[:start] + auth[end:]
trigger = '''                    // MARK: GhostBase v1.1B BOTBACKFILL3 trigger\n                    ghostBaseStartBotBackfill(\n                        account: authorizedAccount,\n                        accountPeerId: user.id\n                    )\n\n'''
auth = auth.replace(trigger, "")
auth_path.write_text(auth, encoding="utf-8")

state4_start = "        // MARK: GhostBase v1.1C BOTSTATE4 startup replay\n"
if state4_start in account:
    start = account.index(state4_start)
    end_anchor = "        /*#if DEBUG\n"
    end = account.index(end_anchor, start)
    account = account[:start] + account[end:]

if "GhostBase v1.1D BOTBACKFILL4 isolated startup import" not in account:
    class_anchor = "public class Account {\n"
    helper = r'''// MARK: GhostBase v1.1D BOTBACKFILL4 isolated startup import
private struct GhostBaseBotBackfill4Cursor {
    let pts: Int32
    let qts: Int32
    let date: Int32
    let slice: Int
}

private func ghostBaseBotBackfill4Prefix(_ peerId: PeerId) -> String {
    return "GhostBase.BotBackfill4.\(peerId.toInt64())"
}

private func ghostBaseBotBackfill4Release(_ peerId: PeerId) {
    UserDefaults.standard.removeObject(forKey: ghostBaseBotBackfill4Prefix(peerId) + ".RunningAt")
}

private func ghostBaseBotBackfill4Finish(_ peerId: PeerId, imported: Int) {
    let defaults = UserDefaults.standard
    defaults.set(true, forKey: ghostBaseBotBackfill4Prefix(peerId) + ".Completed")
    defaults.set(imported, forKey: ghostBaseBotBackfill4Prefix(peerId) + ".Imported")
    defaults.removeObject(forKey: ghostBaseBotBackfill4Prefix(peerId) + ".RunningAt")
    for field in ["pts", "qts", "date", "slice"] {
        defaults.removeObject(forKey: ghostBaseBotBackfill4Prefix(peerId) + ".Cursor." + field)
    }
}

private func ghostBaseBotBackfill4LoadCursor(_ peerId: PeerId) -> GhostBaseBotBackfill4Cursor {
    let defaults = UserDefaults.standard
    let prefix = ghostBaseBotBackfill4Prefix(peerId) + ".Cursor."
    guard defaults.object(forKey: prefix + "pts") != nil else {
        // Zero exists only in memory for an isolated Difference request. It is
        // never written into AuthorizedAccountState or Postbox state.
        return GhostBaseBotBackfill4Cursor(pts: 0, qts: 0, date: 0, slice: 0)
    }
    return GhostBaseBotBackfill4Cursor(
        pts: Int32(defaults.integer(forKey: prefix + "pts")),
        qts: Int32(defaults.integer(forKey: prefix + "qts")),
        date: Int32(defaults.integer(forKey: prefix + "date")),
        slice: defaults.integer(forKey: prefix + "slice")
    )
}

private func ghostBaseBotBackfill4SaveCursor(_ peerId: PeerId, cursor: GhostBaseBotBackfill4Cursor) {
    // Persist only server-returned, non-zero intermediate state.
    guard cursor.pts != 0 || cursor.qts != 0 || cursor.date != 0 else { return }
    let defaults = UserDefaults.standard
    let prefix = ghostBaseBotBackfill4Prefix(peerId) + ".Cursor."
    defaults.set(Int(cursor.pts), forKey: prefix + "pts")
    defaults.set(Int(cursor.qts), forKey: prefix + "qts")
    defaults.set(Int(cursor.date), forKey: prefix + "date")
    defaults.set(cursor.slice, forKey: prefix + "slice")
}

private func ghostBaseBotBackfill4Import(
    postbox: Postbox,
    accountPeerId: PeerId,
    messages: [Api.Message],
    chats: [Api.Chat],
    users: [Api.User]
) -> Signal<Int, NoError> {
    return postbox.transaction { transaction -> Int in
        updatePeers(
            transaction: transaction,
            accountPeerId: accountPeerId,
            peers: AccumulatedPeers(transaction: transaction, chats: chats, users: users)
        )
        var storedMessages: [StoreMessage] = []
        var minTimestamps: [PeerId: Int32] = [:]
        for apiMessage in messages {
            guard let peerId = apiMessage.peerId else { continue }
            let isForum = transaction.getPeer(peerId)?.isForumOrMonoForum ?? false
            guard let message = StoreMessage(apiMessage: apiMessage, accountPeerId: accountPeerId, peerIsForum: isForum) else { continue }
            storedMessages.append(message)
            minTimestamps[peerId] = min(minTimestamps[peerId] ?? message.timestamp, message.timestamp)
        }
        if !storedMessages.isEmpty {
            let _ = transaction.addMessages(storedMessages, location: .UpperHistoryBlock)
        }
        for (peerId, timestamp) in minTimestamps {
            updatePeerChatInclusionWithMinTimestamp(
                transaction: transaction,
                id: peerId,
                minTimestamp: timestamp,
                forceRootGroupIfNotExists: true
            )
        }
        return storedMessages.count
    }
}

private func ghostBaseBotBackfill4Page(
    network: Network,
    postbox: Postbox,
    accountPeerId: PeerId,
    cursor: GhostBaseBotBackfill4Cursor,
    importedTotal: Int
) -> Signal<Bool, NoError> {
    guard cursor.slice < 96 else {
        Logger.shared.log("GhostBase.BotBackfill4", "slice limit reached imported=\(importedTotal)")
        ghostBaseBotBackfill4Release(accountPeerId)
        return .single(false)
    }
    return network.request(
        Api.functions.updates.getDifference(
            flags: 0,
            pts: cursor.pts,
            ptsLimit: nil,
            ptsTotalLimit: nil,
            date: cursor.date,
            qts: cursor.qts,
            qtsLimit: nil
        ),
        automaticFloodWait: false
    )
    |> map(Optional.init)
    |> `catch` { error -> Signal<Api.updates.Difference?, NoError> in
        Logger.shared.log("GhostBase.BotBackfill4", "difference failed code=\(error.errorCode) description=\(error.errorDescription ?? "nil")")
        ghostBaseBotBackfill4Release(accountPeerId)
        return .single(nil)
    }
    |> mapToSignal { difference -> Signal<Bool, NoError> in
        guard let difference else { return .single(false) }
        switch difference {
        case let .difference(data):
            return ghostBaseBotBackfill4Import(postbox: postbox, accountPeerId: accountPeerId, messages: data.newMessages, chats: data.chats, users: data.users)
            |> map { count in
                let total = importedTotal + count
                if total > 0 {
                    ghostBaseBotBackfill4Finish(accountPeerId, imported: total)
                } else {
                    ghostBaseBotBackfill4Release(accountPeerId)
                }
                Logger.shared.log("GhostBase.BotBackfill4", "final imported=\(total)")
                return total > 0
            }
        case let .differenceSlice(data):
            return ghostBaseBotBackfill4Import(postbox: postbox, accountPeerId: accountPeerId, messages: data.newMessages, chats: data.chats, users: data.users)
            |> mapToSignal { count -> Signal<Bool, NoError> in
                switch data.intermediateState {
                case let .state(state):
                    let next = GhostBaseBotBackfill4Cursor(pts: state.pts, qts: state.qts, date: state.date, slice: cursor.slice + 1)
                    ghostBaseBotBackfill4SaveCursor(accountPeerId, cursor: next)
                    return ghostBaseBotBackfill4Page(network: network, postbox: postbox, accountPeerId: accountPeerId, cursor: next, importedTotal: importedTotal + count)
                }
            }
        case .differenceEmpty:
            if importedTotal > 0 {
                ghostBaseBotBackfill4Finish(accountPeerId, imported: importedTotal)
            } else {
                ghostBaseBotBackfill4Release(accountPeerId)
            }
            Logger.shared.log("GhostBase.BotBackfill4", "empty imported=\(importedTotal); completion=\(importedTotal > 0)")
            return .single(importedTotal > 0)
        case .differenceTooLong:
            ghostBaseBotBackfill4Release(accountPeerId)
            Logger.shared.log("GhostBase.BotBackfill4", "differenceTooLong; no account-state mutation")
            return .single(false)
        }
    }
}

private func ghostBaseStartBotBackfill4(network: Network, postbox: Postbox, accountPeerId: PeerId) -> Signal<Bool, NoError> {
    let defaults = UserDefaults.standard
    let prefix = ghostBaseBotBackfill4Prefix(accountPeerId)
    guard !defaults.bool(forKey: prefix + ".Completed") else {
        return .single(true)
    }
    let now = Int64(Date().timeIntervalSince1970)
    let runningAt = Int64(defaults.double(forKey: prefix + ".RunningAt"))
    guard runningAt == 0 || now - runningAt > 600 else {
        Logger.shared.log("GhostBase.BotBackfill4", "duplicate startup suppressed")
        return .single(false)
    }
    defaults.set(Double(now), forKey: prefix + ".RunningAt")
    let cursor = ghostBaseBotBackfill4LoadCursor(accountPeerId)
    return ghostBaseBotBackfill4Page(network: network, postbox: postbox, accountPeerId: accountPeerId, cursor: cursor, importedTotal: 0)
}

'''
    if class_anchor not in account: raise SystemExit("[V11D BOT] Account class anchor missing")
    account = account.replace(class_anchor, helper + class_anchor, 1)

    init_anchor = "        self.automaticCacheEvictionContext = AutomaticCacheEvictionContext(postbox: postbox, accountManager: accountManager)\n"
    block = r'''

        // MARK: GhostBase v1.1D BOTBACKFILL4 startup trigger
        if ghostBaseBotSafeMode && !supplementary {
            let backfillPeerId = peerId
            Queue.concurrentDefaultQueue().after(1.5) { [weak self] in
                guard let self else { return }
                self.managedOperationsDisposable.add((ghostBaseStartBotBackfill4(network: self.network, postbox: self.postbox, accountPeerId: backfillPeerId)
                |> deliverOnMainQueue).start(next: { imported in
                    ghostBaseBotSafeRecord(peerId: backfillPeerId, event: "BOTBACKFILL4 imported=\(imported)")
                }))
            }
        }
'''
    if init_anchor not in account: raise SystemExit("[V11D BOT] Account init anchor missing")
    account = account.replace(init_anchor, init_anchor + block, 1)

account_path.write_text(account, encoding="utf-8")
print("[V11D] BOTBACKFILL4 isolated startup import installed")
