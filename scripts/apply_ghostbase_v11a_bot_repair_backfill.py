#!/usr/bin/env python3
import os
from pathlib import Path

ROOT = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
AUTH = ROOT / "submodules/TelegramCore/Sources/Authorization.swift"
for path in (AUTH,):
    if not path.is_file():
        raise SystemExit(f"[V11A BOT] missing source: {path}")

text = AUTH.read_text(encoding="utf-8")
if "// MARK: GhostBase v1.1A BOTREPAIR1 live server state" in text:
    print("[V11A] bot repair/backfill already applied")
    raise SystemExit(0)
if "// MARK: GhostBase v1.0ZH BOTBOOTSTRAP1 zero-state backlog" not in text:
    raise SystemExit("[V11A BOT] Build 86 bootstrap marker missing")
if "// MARK: GhostBase v1.0ZH BOTDEDUPE1 token peer id" not in text:
    raise SystemExit("[V11A BOT] Build 86 dedupe marker missing")

start = text.index("// MARK: GhostBase v1.0ZE BOTSAFE1 current server state")
dedupe_start = text.index(
    "// MARK: GhostBase v1.0ZH BOTDEDUPE1 token peer id",
    start
)
bootstrap_start = text.index(
    "// MARK: GhostBase v1.0ZH BOTBOOTSTRAP1 zero-state backlog",
    dedupe_start
)
authorization_start = text.index(
    "public func ghostBaseAuthorizeBot(\n",
    bootstrap_start
)
state_replacement = r'''// MARK: GhostBase v1.0ZE BOTSAFE1 current server state
// MARK: GhostBase v1.1A BOTREPAIR1 live server state
private func ghostBaseBotInitialState(
    account: UnauthorizedAccount
) -> Signal<AuthorizedAccountState.State?, NoError> {
    return account.network.request(
        Api.functions.updates.getState(),
        automaticFloodWait: false
    )
    |> map { state -> AuthorizedAccountState.State? in
        switch state {
        case let .state(data):
            Logger.shared.log(
                "GhostBase.BotRepair1",
                "live state pts=\(data.pts) qts=\(data.qts) date=\(data.date) seq=\(data.seq)"
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
        Logger.shared.log(
            "GhostBase.BotRepair1",
            "getState failed code=\(error.errorCode) description=\(error.errorDescription ?? "nil")"
        )
        return .single(nil)
    }
}

'''
backfill_helpers = r'''// MARK: GhostBase v1.1A BOTBACKFILL2 isolated history import
private struct GhostBaseBotBackfillCursor {
    let pts: Int32
    let qts: Int32
    let date: Int32
    let slice: Int
}

private func ghostBaseBotBackfillKey(_ peerId: PeerId) -> String {
    return "GhostBase.BotBackfill2.Completed.\(peerId.toInt64())"
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
            peers: AccumulatedPeers(
                transaction: transaction,
                chats: chats,
                users: users
            )
        )

        var storedMessages: [StoreMessage] = []
        var minTimestamps: [PeerId: Int32] = [:]
        for apiMessage in messages {
            guard let peerId = apiMessage.peerId else {
                continue
            }
            let peerIsForum = transaction.getPeer(peerId)?.isForumOrMonoForum ?? false
            guard let stored = StoreMessage(
                apiMessage: apiMessage,
                accountPeerId: accountPeerId,
                peerIsForum: peerIsForum
            ) else {
                continue
            }
            storedMessages.append(stored)
            if let current = minTimestamps[peerId] {
                minTimestamps[peerId] = min(current, stored.timestamp)
            } else {
                minTimestamps[peerId] = stored.timestamp
            }
        }

        if !storedMessages.isEmpty {
            let _ = transaction.addMessages(
                storedMessages,
                location: .UpperHistoryBlock
            )
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
    guard cursor.slice < 32 else {
        Logger.shared.log("GhostBase.BotBackfill2", "slice limit reached")
        return .single(false)
    }

    return account.network.request(
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
        Logger.shared.log(
            "GhostBase.BotBackfill2",
            "difference failed code=\(error.errorCode) description=\(error.errorDescription ?? "nil")"
        )
        return .single(nil)
    }
    |> mapToSignal { difference -> Signal<Bool, NoError> in
        guard let difference else {
            return .single(false)
        }

        switch difference {
        case let .difference(data):
            return ghostBaseImportBotBackfillPage(
                account: account,
                accountPeerId: accountPeerId,
                messages: data.newMessages,
                chats: data.chats,
                users: data.users
            )
            |> map { count in
                Logger.shared.log("GhostBase.BotBackfill2", "final imported=\(count)")
                UserDefaults.standard.set(true, forKey: ghostBaseBotBackfillKey(accountPeerId))
                return true
            }

        case let .differenceSlice(data):
            return ghostBaseImportBotBackfillPage(
                account: account,
                accountPeerId: accountPeerId,
                messages: data.newMessages,
                chats: data.chats,
                users: data.users
            )
            |> mapToSignal { count -> Signal<Bool, NoError> in
                switch data.intermediateState {
                case let .state(state):
                    Logger.shared.log(
                        "GhostBase.BotBackfill2",
                        "slice=\(cursor.slice) imported=\(count) nextPts=\(state.pts)"
                    )
                    return ghostBaseBotBackfillPage(
                        account: account,
                        accountPeerId: accountPeerId,
                        cursor: GhostBaseBotBackfillCursor(
                            pts: state.pts,
                            qts: state.qts,
                            date: state.date,
                            slice: cursor.slice + 1
                        )
                    )
                }
            }

        case .differenceEmpty:
            UserDefaults.standard.set(true, forKey: ghostBaseBotBackfillKey(accountPeerId))
            Logger.shared.log("GhostBase.BotBackfill2", "empty completed")
            return .single(true)

        case .differenceTooLong:
            Logger.shared.log("GhostBase.BotBackfill2", "differenceTooLong stopped safely")
            return .single(false)
        }
    }
}

private func ghostBaseStartBotBackfill(
    account: UnauthorizedAccount,
    accountPeerId: PeerId
) {
    let key = ghostBaseBotBackfillKey(accountPeerId)
    guard !UserDefaults.standard.bool(forKey: key) else {
        return
    }
    Queue.concurrentDefaultQueue().after(1.5) {
        let _ = ghostBaseBotBackfillPage(
            account: account,
            accountPeerId: accountPeerId,
            cursor: GhostBaseBotBackfillCursor(
                pts: 0,
                qts: 0,
                date: 0,
                slice: 0
            )
        ).start()
    }
}

'''
text = (
    text[:start]
    + state_replacement
    + text[dedupe_start:bootstrap_start]
    + backfill_helpers
    + text[authorization_start:]
)


trigger_marker = "// MARK: GhostBase v1.1A BOTBACKFILL2 trigger"
if trigger_marker not in text:
    function_start = text.index("public func ghostBaseAuthorizeBot(\n")
    state_line = "transaction.setState(state)"
    line_pos = text.index(state_line, function_start)
    line_end = text.index("\n", line_pos) + 1
    indent = text[text.rfind("\n", 0, line_pos) + 1:line_pos]
    insert = (
        "\n"
        + indent + "// MARK: GhostBase v1.1A BOTBACKFILL2 trigger\n"
        + indent + "ghostBaseStartBotBackfill(\n"
        + indent + "    account: authorizedAccount,\n"
        + indent + "    accountPeerId: user.id\n"
        + indent + ")\n"
    )
    text = text[:line_end] + insert + text[line_end:]

AUTH.write_text(text, encoding="utf-8")
updated = AUTH.read_text(encoding="utf-8")
for proof in (
    "GhostBase v1.1A BOTREPAIR1 live server state",
    "GhostBase v1.1A BOTBACKFILL2 isolated history import",
    "updatePeerChatInclusionWithMinTimestamp(",
    "location: .UpperHistoryBlock",
    "ghostBaseStartBotBackfill(",
    "GhostBase v1.0ZH BOTDEDUPE1 token peer id",
):
    if proof not in updated:
        raise SystemExit(f"[V11A BOT] proof missing: {proof}")
if "BOTBOOTSTRAP1 armed pts=0" in updated:
    raise SystemExit("[V11A BOT] broken persistent zero-state implementation remains")
print("[V11A] bot live updates restored; isolated backfill installed; dedupe preserved")
