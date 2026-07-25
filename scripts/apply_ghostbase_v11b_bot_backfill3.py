#!/usr/bin/env python3
import os
from pathlib import Path

ROOT = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
PATH = ROOT / "submodules/TelegramCore/Sources/Authorization.swift"
if not PATH.is_file():
    raise SystemExit(f"[V11B BOTBACKFILL3] missing source: {PATH}")

text = PATH.read_text(encoding="utf-8")
MARKER = "// MARK: GhostBase v1.1B BOTBACKFILL3 resumable guarded import"
if MARKER in text:
    print("[V11B] BOTBACKFILL3 already applied")
    raise SystemExit(0)
if "// MARK: GhostBase v1.1A BOTBACKFILL2 isolated history import" not in text:
    raise SystemExit("[V11B BOTBACKFILL3] BOTBACKFILL2 marker missing; apply v1.1A bot patch first")

start = text.index("// MARK: GhostBase v1.1A BOTBACKFILL2 isolated history import")
end = text.index("public func ghostBaseAuthorizeBot(\n", start)

block = r'''// MARK: GhostBase v1.1B BOTBACKFILL3 resumable guarded import
private struct GhostBaseBotBackfillCursor {
    let pts: Int32
    let qts: Int32
    let date: Int32
    let slice: Int
}

private func ghostBaseBotBackfillPrefix(_ peerId: PeerId) -> String {
    return "GhostBase.BotBackfill3.\(peerId.toInt64())"
}

private func ghostBaseBotBackfillCompletedKey(_ peerId: PeerId) -> String {
    return ghostBaseBotBackfillPrefix(peerId) + ".Completed"
}

private func ghostBaseBotBackfillRunningAtKey(_ peerId: PeerId) -> String {
    return ghostBaseBotBackfillPrefix(peerId) + ".RunningAt"
}

private func ghostBaseBotBackfillCursorKey(_ peerId: PeerId, _ field: String) -> String {
    return ghostBaseBotBackfillPrefix(peerId) + ".Cursor." + field
}

private func ghostBaseLoadBotBackfillCursor(_ peerId: PeerId) -> GhostBaseBotBackfillCursor {
    let defaults = UserDefaults.standard
    let prefix = ghostBaseBotBackfillPrefix(peerId) + ".Cursor."
    if defaults.object(forKey: prefix + "pts") == nil {
        return GhostBaseBotBackfillCursor(pts: 0, qts: 0, date: 0, slice: 0)
    }
    return GhostBaseBotBackfillCursor(
        pts: Int32(defaults.integer(forKey: prefix + "pts")),
        qts: Int32(defaults.integer(forKey: prefix + "qts")),
        date: Int32(defaults.integer(forKey: prefix + "date")),
        slice: defaults.integer(forKey: prefix + "slice")
    )
}

private func ghostBaseSaveBotBackfillCursor(_ peerId: PeerId, _ cursor: GhostBaseBotBackfillCursor) {
    let defaults = UserDefaults.standard
    defaults.set(Int(cursor.pts), forKey: ghostBaseBotBackfillCursorKey(peerId, "pts"))
    defaults.set(Int(cursor.qts), forKey: ghostBaseBotBackfillCursorKey(peerId, "qts"))
    defaults.set(Int(cursor.date), forKey: ghostBaseBotBackfillCursorKey(peerId, "date"))
    defaults.set(cursor.slice, forKey: ghostBaseBotBackfillCursorKey(peerId, "slice"))
}

private func ghostBaseFinishBotBackfill(_ peerId: PeerId) {
    let defaults = UserDefaults.standard
    defaults.set(true, forKey: ghostBaseBotBackfillCompletedKey(peerId))
    defaults.removeObject(forKey: ghostBaseBotBackfillRunningAtKey(peerId))
    for field in ["pts", "qts", "date", "slice"] {
        defaults.removeObject(forKey: ghostBaseBotBackfillCursorKey(peerId, field))
    }
}

private func ghostBaseReleaseBotBackfill(_ peerId: PeerId) {
    UserDefaults.standard.removeObject(forKey: ghostBaseBotBackfillRunningAtKey(peerId))
}

private func ghostBaseImportBotBackfillPage(
    account: UnauthorizedAccount,
    accountPeerId: PeerId,
    messages: [Api.Message],
    chats: [Api.Chat],
    users: [Api.User]
) -> Signal<Int, NoError> {
    return account.postbox.transaction { transaction -> Int in
        updatePeers(
            transaction: transaction,
            accountPeerId: accountPeerId,
            peers: AccumulatedPeers(transaction: transaction, chats: chats, users: users)
        )
        var storedMessages: [StoreMessage] = []
        var minTimestamps: [PeerId: Int32] = [:]
        for apiMessage in messages {
            guard let peerId = apiMessage.peerId else { continue }
            let peerIsForum = transaction.getPeer(peerId)?.isForumOrMonoForum ?? false
            guard let stored = StoreMessage(apiMessage: apiMessage, accountPeerId: accountPeerId, peerIsForum: peerIsForum) else { continue }
            storedMessages.append(stored)
            minTimestamps[peerId] = min(minTimestamps[peerId] ?? stored.timestamp, stored.timestamp)
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

private func ghostBaseBotBackfillPage(
    account: UnauthorizedAccount,
    accountPeerId: PeerId,
    cursor: GhostBaseBotBackfillCursor
) -> Signal<Bool, NoError> {
    guard cursor.slice < 64 else {
        Logger.shared.log("GhostBase.BotBackfill3", "slice limit reached; cursor preserved")
        ghostBaseReleaseBotBackfill(accountPeerId)
        return .single(false)
    }
    ghostBaseSaveBotBackfillCursor(accountPeerId, cursor)
    return account.network.request(
        Api.functions.updates.getDifference(
            flags: 0, pts: cursor.pts, ptsLimit: nil, ptsTotalLimit: nil,
            date: cursor.date, qts: cursor.qts, qtsLimit: nil
        ),
        automaticFloodWait: false
    )
    |> map(Optional.init)
    |> `catch` { error -> Signal<Api.updates.Difference?, NoError> in
        Logger.shared.log("GhostBase.BotBackfill3", "difference failed code=\(error.errorCode) description=\(error.errorDescription ?? "nil")")
        ghostBaseReleaseBotBackfill(accountPeerId)
        return .single(nil)
    }
    |> mapToSignal { difference -> Signal<Bool, NoError> in
        guard let difference else { return .single(false) }
        switch difference {
        case let .difference(data):
            return ghostBaseImportBotBackfillPage(account: account, accountPeerId: accountPeerId, messages: data.newMessages, chats: data.chats, users: data.users)
            |> map { count in
                Logger.shared.log("GhostBase.BotBackfill3", "final imported=\(count)")
                ghostBaseFinishBotBackfill(accountPeerId)
                return true
            }
        case let .differenceSlice(data):
            return ghostBaseImportBotBackfillPage(account: account, accountPeerId: accountPeerId, messages: data.newMessages, chats: data.chats, users: data.users)
            |> mapToSignal { count -> Signal<Bool, NoError> in
                switch data.intermediateState {
                case let .state(state):
                    let next = GhostBaseBotBackfillCursor(pts: state.pts, qts: state.qts, date: state.date, slice: cursor.slice + 1)
                    ghostBaseSaveBotBackfillCursor(accountPeerId, next)
                    Logger.shared.log("GhostBase.BotBackfill3", "slice=\(cursor.slice) imported=\(count) nextPts=\(state.pts)")
                    return ghostBaseBotBackfillPage(account: account, accountPeerId: accountPeerId, cursor: next)
                }
            }
        case .differenceEmpty:
            ghostBaseFinishBotBackfill(accountPeerId)
            Logger.shared.log("GhostBase.BotBackfill3", "empty completed")
            return .single(true)
        case .differenceTooLong:
            Logger.shared.log("GhostBase.BotBackfill3", "differenceTooLong; cursor preserved for retry")
            ghostBaseReleaseBotBackfill(accountPeerId)
            return .single(false)
        }
    }
}

private func ghostBaseStartBotBackfill(account: UnauthorizedAccount, accountPeerId: PeerId) {
    let defaults = UserDefaults.standard
    let oldCompleted = defaults.bool(forKey: "GhostBase.BotBackfill2.Completed.\(accountPeerId.toInt64())")
    if oldCompleted {
        defaults.set(true, forKey: ghostBaseBotBackfillCompletedKey(accountPeerId))
    }
    guard !defaults.bool(forKey: ghostBaseBotBackfillCompletedKey(accountPeerId)) else { return }

    let now = Int64(Date().timeIntervalSince1970)
    let runningKey = ghostBaseBotBackfillRunningAtKey(accountPeerId)
    let runningAt = Int64(defaults.double(forKey: runningKey))
    guard runningAt == 0 || now - runningAt > 600 else {
        Logger.shared.log("GhostBase.BotBackfill3", "duplicate start suppressed")
        return
    }
    defaults.set(Double(now), forKey: runningKey)
    let cursor = ghostBaseLoadBotBackfillCursor(accountPeerId)
    Queue.concurrentDefaultQueue().after(1.5) {
        let _ = ghostBaseBotBackfillPage(account: account, accountPeerId: accountPeerId, cursor: cursor).start()
    }
}

'''
text = text[:start] + block + text[end:]
# Upgrade trigger marker without moving the call.
text = text.replace("// MARK: GhostBase v1.1A BOTBACKFILL2 trigger", "// MARK: GhostBase v1.1B BOTBACKFILL3 trigger", 1)
PATH.write_text(text, encoding="utf-8")

updated = PATH.read_text(encoding="utf-8")
for proof in (MARKER, "duplicate start suppressed", "ghostBaseSaveBotBackfillCursor", "slice limit reached; cursor preserved", "GhostBase v1.1B BOTBACKFILL3 trigger", "location: .UpperHistoryBlock"):
    if proof not in updated:
        raise SystemExit(f"[V11B BOTBACKFILL3] proof missing: {proof}")
if "// MARK: GhostBase v1.1A BOTBACKFILL2 isolated history import" in updated:
    raise SystemExit("[V11B BOTBACKFILL3] old helper block remains")
print("[V11B] BOTBACKFILL3 applied: resumable cursor, stale-lock recovery, completion migration, duplicate-start guard")
