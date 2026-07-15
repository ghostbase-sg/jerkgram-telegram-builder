#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src"
))

path = root / (
    "submodules/TelegramCore/Sources/TelegramEngine/Peers/"
    "TelegramEnginePeers.swift"
)

if not path.is_file():
    raise SystemExit(f"missing core source: {path}")

text = path.read_text(encoding="utf-8")

marker = "// MARK: GhostBase v1.0ZB Bot getDifference Probe"

def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(f"[v1.0ZB bot difference] {message}")

require(
    "GhostBase v1.0ZA Bot Account Capability Probe" in text,
    "v1.0ZA capability core must be applied first"
)

if marker not in text:
    anchor = '''        // MARK: GhostBase v1.0ZA Bot Account Capability Probe
        public func ghostBaseBotCapabilityProbe() -> Signal<String, NoError> {
'''

    require(anchor in text, "capability function anchor missing")

    helper = r'''        // MARK: GhostBase v1.0ZB Bot getDifference Probe
        public func ghostBaseBotDifferenceProbe() -> Signal<String, NoError> {
            return self.account.postbox.transaction {
                transaction -> AuthorizedAccountState.State? in

                guard let accountState =
                    transaction.getState()
                    as? AuthorizedAccountState else {
                    return nil
                }

                return accountState.state
            }
            |> mapToSignal {
                localState -> Signal<String, NoError> in

                guard let localState else {
                    return .single("""
                    updates.getDifference
                    localState: nil
                    request: not started
                    """)
                }

                let request = self.account.network.request(
                    Api.functions.updates.getDifference(
                        flags: 0,
                        pts: localState.pts,
                        ptsLimit: nil,
                        ptsTotalLimit: nil,
                        date: localState.date,
                        qts: localState.qts,
                        qtsLimit: nil
                    )
                )

                return request
                |> map { result -> String in
                    let start = """
                    updates.getDifference
                    requestPts: \(localState.pts)
                    requestQts: \(localState.qts)
                    requestDate: \(localState.date)
                    """

                    switch result {
                    case let .difference(data):
                        let stateText: String
                        switch data.state {
                        case let .state(state):
                            stateText = """
                            finalPts: \(state.pts)
                            finalQts: \(state.qts)
                            finalDate: \(state.date)
                            finalSeq: \(state.seq)
                            finalUnreadCount: \(state.unreadCount)
                            """
                        }

                        return """
                        \(start)
                        result: difference
                        newMessages: \(data.newMessages.count)
                        newEncryptedMessages: \(data.newEncryptedMessages.count)
                        otherUpdates: \(data.otherUpdates.count)
                        chats: \(data.chats.count)
                        users: \(data.users.count)
                        \(stateText)
                        """

                    case let .differenceSlice(data):
                        let stateText: String
                        switch data.intermediateState {
                        case let .state(state):
                            stateText = """
                            intermediatePts: \(state.pts)
                            intermediateQts: \(state.qts)
                            intermediateDate: \(state.date)
                            intermediateSeq: \(state.seq)
                            intermediateUnreadCount: \(state.unreadCount)
                            """
                        }

                        return """
                        \(start)
                        result: differenceSlice
                        newMessages: \(data.newMessages.count)
                        newEncryptedMessages: \(data.newEncryptedMessages.count)
                        otherUpdates: \(data.otherUpdates.count)
                        chats: \(data.chats.count)
                        users: \(data.users.count)
                        \(stateText)
                        """

                    case let .differenceEmpty(data):
                        return """
                        \(start)
                        result: differenceEmpty
                        date: \(data.date)
                        seq: \(data.seq)
                        """

                    case let .differenceTooLong(data):
                        return """
                        \(start)
                        result: differenceTooLong
                        pts: \(data.pts)
                        """
                    }
                }
                |> `catch` { error -> Signal<String, NoError> in
                    return .single("""
                    updates.getDifference
                    requestPts: \(localState.pts)
                    requestQts: \(localState.qts)
                    requestDate: \(localState.date)
                    rpcError: \(error.errorCode)
                    rpcDescription: \(error.errorDescription ?? "nil")
                    """)
                }
            }
        }

'''

    text = text.replace(anchor, helper + anchor, 1)

for proof in (
    marker,
    "ghostBaseBotDifferenceProbe()",
    "Api.functions.updates.getDifference",
    "result: differenceSlice",
    "result: differenceEmpty",
    "result: differenceTooLong",
    "newMessages:",
    'error.errorDescription ?? "nil"',
):
    require(proof in text, f"missing proof: {proof}")

probe_start = text.index(marker)
probe_end = text.index(
    "// MARK: GhostBase v1.0ZA Bot Account Capability Probe",
    probe_start
)

require(
    "retryRequest" not in text[probe_start:probe_end],
    "getDifference probe must not retry"
)

path.write_text(text, encoding="utf-8")

print("[v1.0ZB] Bot getDifference core probe added")
print("[v1.0ZB] direct request without retry added")
