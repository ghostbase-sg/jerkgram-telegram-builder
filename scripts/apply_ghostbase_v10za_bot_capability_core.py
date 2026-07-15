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
    raise SystemExit(f"missing TelegramEnginePeers source: {path}")

text = path.read_text(encoding="utf-8")

marker = "// MARK: GhostBase v1.0ZA Bot Account Capability Probe"

def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(f"[v1.0ZA bot core] {message}")

if marker not in text:
    anchor = '''        public func getPossibleStarRefBotTargets() -> Signal<[EnginePeer], NoError> {
            return _internal_getPossibleStarRefBotTargets(account: self.account)
        }
    }
}
'''

    require(anchor in text, "TelegramEngine.Peers tail anchor missing")

    replacement = r'''        public func getPossibleStarRefBotTargets() -> Signal<[EnginePeer], NoError> {
            return _internal_getPossibleStarRefBotTargets(account: self.account)
        }

        // MARK: GhostBase v1.0ZA Bot Account Capability Probe
        public func ghostBaseBotCapabilityProbe() -> Signal<String, NoError> {
            let localState =
                self.account.postbox.transaction {
                    transaction -> String in

                    guard let state =
                        transaction.getState()
                        as? AuthorizedAccountState else {
                        return """
                        LOCAL_STATE
                        authorizedAccountState: missing
                        """
                    }

                    let internalState: String
                    if let value = state.state {
                        internalState = """
                        pts: \(value.pts)
                        qts: \(value.qts)
                        date: \(value.date)
                        seq: \(value.seq)
                        """
                    } else {
                        internalState = "nil"
                    }

                    return """
                    LOCAL_STATE
                    accountPeerId: \(String(describing: self.account.peerId))
                    statePeerId: \(String(describing: state.peerId))
                    masterDc: \(state.masterDatacenterId)
                    testing: \(state.isTestingEnvironment)
                    internalState:
                    \(internalState)
                    """
                }

            let selfUser =
                self.account.network.request(
                    Api.functions.users.getUsers(
                        id: [.inputUserSelf]
                    )
                )
                |> map { users -> String in
                    return """
                    users.getUsers(inputUserSelf)
                    success
                    users: \(users.count)
                    """
                }
                |> `catch` { error -> Signal<String, NoError> in
                    return .single("""
                    users.getUsers(inputUserSelf)
                    rpcError: \(error.errorCode)
                    rpcDescription: \(error.errorDescription ?? "nil")
                    """)
                }

            let updateState =
                self.account.network.request(
                    Api.functions.updates.getState()
                )
                |> map { result -> String in
                    switch result {
                    case let .state(data):
                        return """
                        updates.getState
                        success
                        pts: \(data.pts)
                        qts: \(data.qts)
                        date: \(data.date)
                        seq: \(data.seq)
                        unreadCount: \(data.unreadCount)
                        """
                    }
                }
                |> `catch` { error -> Signal<String, NoError> in
                    return .single("""
                    updates.getState
                    rpcError: \(error.errorCode)
                    rpcDescription: \(error.errorDescription ?? "nil")
                    """)
                }

            let dialogs =
                self.account.network.request(
                    Api.functions.messages.getDialogs(
                        flags: 1 << 1,
                        folderId: 0,
                        offsetDate: 0,
                        offsetId: 0,
                        offsetPeer: .inputPeerEmpty,
                        limit: 100,
                        hash: 0
                    )
                )
                |> map { result -> String in
                    switch result {
                    case let .dialogs(data):
                        return """
                        messages.getDialogs
                        success: dialogs
                        dialogs: \(data.dialogs.count)
                        messages: \(data.messages.count)
                        chats: \(data.chats.count)
                        users: \(data.users.count)
                        lowestBoundary: true
                        """

                    case let .dialogsSlice(data):
                        return """
                        messages.getDialogs
                        success: dialogsSlice
                        serverCount: \(data.count)
                        dialogs: \(data.dialogs.count)
                        messages: \(data.messages.count)
                        chats: \(data.chats.count)
                        users: \(data.users.count)
                        lowestBoundary: false
                        """

                    case .dialogsNotModified:
                        return """
                        messages.getDialogs
                        success: dialogsNotModified
                        """
                    }
                }
                |> `catch` { error -> Signal<String, NoError> in
                    return .single("""
                    messages.getDialogs
                    rpcError: \(error.errorCode)
                    rpcDescription: \(error.errorDescription ?? "nil")
                    """)
                }

            let pinnedDialogs =
                self.account.network.request(
                    Api.functions.messages.getPinnedDialogs(
                        folderId: 0
                    )
                )
                |> map { result -> String in
                    switch result {
                    case let .peerDialogs(data):
                        return """
                        messages.getPinnedDialogs
                        success
                        dialogs: \(data.dialogs.count)
                        messages: \(data.messages.count)
                        chats: \(data.chats.count)
                        users: \(data.users.count)
                        """
                    }
                }
                |> `catch` { error -> Signal<String, NoError> in
                    return .single("""
                    messages.getPinnedDialogs
                    rpcError: \(error.errorCode)
                    rpcDescription: \(error.errorDescription ?? "nil")
                    """)
                }

            let signals: [Signal<String, NoError>] = [
                localState,
                selfUser,
                updateState,
                dialogs,
                pinnedDialogs
            ]

            return combineLatest(signals)
            |> map { sections in
                return sections.joined(separator: "\n\n")
            }
        }
    }
}
'''

    text = text.replace(anchor, replacement, 1)

for proof in (
    marker,
    "ghostBaseBotCapabilityProbe()",
    "users.getUsers(",
    "updates.getState()",
    "messages.getDialogs(",
    "messages.getPinnedDialogs(",
    "rpcDescription:",
):
    require(proof in text, f"missing proof: {proof}")

probe_start = text.index(marker)
probe_source = text[probe_start:]

require(
    "retryRequest" not in probe_source,
    "capability requests must not use retryRequest"
)

bad_optional_description = r'\(error.errorDescription)'
fixed_optional_description = r'\(error.errorDescription ?? "nil")'

if bad_optional_description in text:
    text = text.replace(
        bad_optional_description,
        fixed_optional_description
    )

path.write_text(text, encoding="utf-8")

print("[v1.0ZA] Bot capability core added")
print("[v1.0ZA] four direct RPC probes added without retry")
