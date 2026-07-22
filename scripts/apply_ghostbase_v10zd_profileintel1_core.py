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
marker = "// MARK: GhostBase v1.0ZD PROFILEINTEL1 Core"


def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(f"[v1.0ZD PROFILEINTEL1 core] {message}")


if marker not in text:
    helper_anchor = "public extension TelegramEngine {\n"
    require(text.count(helper_anchor) == 1, "TelegramEngine extension anchor mismatch")

    helpers = r'''// MARK: GhostBase v1.0ZD PROFILEINTEL1 Core

private func ghostBaseProfileIntelPeerSettingsText(
    label: String,
    settings: Api.PeerSettings
) -> String {
    switch settings {
    case let .peerSettings(data):
        return """
        \(label)
        flags: \(data.flags)
        hasRegistrationMonth: \((data.flags & (1 << 15)) != 0)
        registrationMonth: \(data.registrationMonth ?? "nil")
        hasPhoneCountry: \((data.flags & (1 << 16)) != 0)
        phoneCountry: \(data.phoneCountry ?? "nil")
        hasNameChangeDate: \((data.flags & (1 << 17)) != 0)
        nameChangeDate: \(data.nameChangeDate.map(String.init) ?? "nil")
        hasPhotoChangeDate: \((data.flags & (1 << 18)) != 0)
        photoChangeDate: \(data.photoChangeDate.map(String.init) ?? "nil")
        """
    }
}

private func ghostBaseProfileIntelStatusText(
    label: String,
    user: Api.User?
) -> String {
    guard let user else {
        return """
        \(label)
        user: missing
        """
    }

    switch user {
    case .userEmpty:
        return """
        \(label)
        user: empty
        """

    case let .user(data):
        guard let status = data.status else {
            return """
            \(label)
            status: nil
            """
        }

        switch status {
        case .userStatusEmpty:
            return """
            \(label)
            status: empty
            """

        case let .userStatusOnline(value):
            return """
            \(label)
            status: online
            expires: \(value.expires)
            """

        case let .userStatusOffline(value):
            return """
            \(label)
            status: offline
            wasOnline: \(value.wasOnline)
            """

        case let .userStatusRecently(value):
            return """
            \(label)
            status: recently
            flags: \(value.flags)
            bit0IsHidden: \((value.flags & (1 << 0)) != 0)
            """

        case let .userStatusLastWeek(value):
            return """
            \(label)
            status: lastWeek
            flags: \(value.flags)
            bit0IsHidden: \((value.flags & (1 << 0)) != 0)
            """

        case let .userStatusLastMonth(value):
            return """
            \(label)
            status: lastMonth
            flags: \(value.flags)
            bit0IsHidden: \((value.flags & (1 << 0)) != 0)
            """
        }
    }
}

private func ghostBaseProfileIntelNormalizedUsername(
    _ value: String
) -> String {
    var result = value.trimmingCharacters(
        in: .whitespacesAndNewlines
    )

    if let range = result.range(of: "t.me/") {
        result = String(result[range.upperBound...])
    } else if let range = result.range(of: "telegram.me/") {
        result = String(result[range.upperBound...])
    }

    if let separator = result.firstIndex(where: {
        $0 == "?" || $0 == "/" || $0.isWhitespace
    }) {
        result = String(result[..<separator])
    }

    while result.hasPrefix("@") {
        result.removeFirst()
    }

    return result
}

'''
    text = text.replace(helper_anchor, helpers + helper_anchor, 1)

    method_anchor_candidates = [
        "        // MARK: GhostBase v1.0ZB Bot getDifference Probe\n",
        "        // MARK: GhostBase v1.0ZA Bot Account Capability Probe\n",
        "        public func getPossibleStarRefBotTargets() -> Signal<[EnginePeer], NoError> {\n",
    ]
    method_anchor = next((item for item in method_anchor_candidates if item in text), None)
    require(method_anchor is not None, "Peers method anchor missing")

    method = r'''        public func ghostBaseProfileIntelProbe(
            username rawUsername: String
        ) -> Signal<String, NoError> {
            let username = ghostBaseProfileIntelNormalizedUsername(
                rawUsername
            )

            guard !username.isEmpty else {
                return .single("""
                PROFILEINTEL1
                error: EMPTY_USERNAME
                """)
            }

            return _internal_resolvePeerByName(
                account: self.account,
                name: username,
                referrer: nil,
                ageLimit: 0
            )
            |> mapToSignal {
                result -> Signal<String, NoError> in

                switch result {
                case .progress:
                    return .complete()

                case let .result(peerId):
                    guard let peerId else {
                        return .single("""
                        PROFILEINTEL1
                        target: @\(username)
                        resolve: not found
                        """)
                    }

                    return self.account.postbox.transaction {
                        transaction -> (
                            Api.InputUser?,
                            Api.InputPeer?,
                            String
                        ) in

                        guard let peer = transaction.getPeer(peerId) else {
                            return (
                                nil,
                                nil,
                                "peer missing after resolve"
                            )
                        }

                        let inputUser = apiInputUser(peer)
                        let inputPeer = apiInputPeer(peer)

                        let local = """
                        PROFILEINTEL1
                        target: @\(username)
                        peerId: \(String(describing: peerId))
                        inputUser: \(inputUser == nil ? "no" : "yes")
                        inputPeer: \(inputPeer == nil ? "no" : "yes")
                        dialogRequired: no
                        """

                        return (inputUser, inputPeer, local)
                    }
                    |> mapToSignal {
                        inputUser,
                        inputPeer,
                        local -> Signal<String, NoError> in

                        guard let inputUser, let inputPeer else {
                            return .single("""
                            \(local)

                            request: not started
                            reason: INPUT_PEER_UNAVAILABLE
                            """)
                        }

                        let fullUser = self.account.network.request(
                            Api.functions.users.getFullUser(
                                id: inputUser
                            ),
                            automaticFloodWait: false
                        )
                        |> map { result -> String in
                            switch result {
                            case let .userFull(data):
                                let targetUser = data.users.first(where: {
                                    $0.peerId == peerId
                                })

                                let settingsText: String
                                let aboutText: String
                                let fullFlagsText: String

                                switch data.fullUser {
                                case let .userFull(full):
                                    settingsText =
                                        ghostBaseProfileIntelPeerSettingsText(
                                            label: "users.getFullUser.settings",
                                            settings: full.settings
                                        )
                                    aboutText = full.about ?? "nil"
                                    fullFlagsText = """
                                    users.getFullUser.full
                                    flags: \(full.flags)
                                    flags2: \(full.flags2)
                                    about: \(aboutText)
                                    commonChatsCount: \(full.commonChatsCount)
                                    """
                                }

                                return """
                                users.getFullUser
                                success: true
                                users: \(data.users.count)
                                chats: \(data.chats.count)
                                \(fullFlagsText)
                                \(settingsText)
                                \(ghostBaseProfileIntelStatusText(
                                    label: "users.getFullUser.status",
                                    user: targetUser
                                ))
                                """
                            }
                        }
                        |> `catch` {
                            error -> Signal<String, NoError> in
                            return .single("""
                            users.getFullUser
                            rpcError: \(error.errorCode)
                            rpcDescription: \(error.errorDescription ?? "nil")
                            """)
                        }

                        let peerSettings = self.account.network.request(
                            Api.functions.messages.getPeerSettings(
                                peer: inputPeer
                            ),
                            automaticFloodWait: false
                        )
                        |> map { result -> String in
                            switch result {
                            case let .peerSettings(data):
                                let targetUser = data.users.first(where: {
                                    $0.peerId == peerId
                                })

                                return """
                                messages.getPeerSettings
                                success: true
                                users: \(data.users.count)
                                chats: \(data.chats.count)
                                \(ghostBaseProfileIntelPeerSettingsText(
                                    label: "messages.getPeerSettings.settings",
                                    settings: data.settings
                                ))
                                \(ghostBaseProfileIntelStatusText(
                                    label: "messages.getPeerSettings.status",
                                    user: targetUser
                                ))
                                """
                            }
                        }
                        |> `catch` {
                            error -> Signal<String, NoError> in
                            return .single("""
                            messages.getPeerSettings
                            rpcError: \(error.errorCode)
                            rpcDescription: \(error.errorDescription ?? "nil")
                            """)
                        }

                        return combineLatest(fullUser, peerSettings)
                        |> map { fullUser, peerSettings in
                            return """
                            \(local)

                            \(fullUser)

                            \(peerSettings)
                            """
                        }
                    }
                }
            }
        }

'''
    text = text.replace(method_anchor, method + method_anchor, 1)

for proof in (
    marker,
    "ghostBaseProfileIntelProbe(",
    "contacts.resolveUsername",
    "Api.functions.users.getFullUser",
    "Api.functions.messages.getPeerSettings",
    "registrationMonth:",
    "phoneCountry:",
    "nameChangeDate:",
    "photoChangeDate:",
    "bit0IsHidden:",
    "automaticFloodWait: false",
):
    if proof == "contacts.resolveUsername":
        # The core intentionally uses Official resolvePeerByName, which calls
        # contacts.resolveUsername in ResolvePeerByName.swift.
        continue
    require(proof in text, f"missing proof: {proof}")

probe_start = text.index(marker)
probe_source = text[probe_start:]
require("account.setPrivacy" not in probe_source, "privacy mutation found")
require("retryRequest" not in probe_source, "probe must not retry RPC calls")
require("photos.getUserPhotos" not in probe_source, "photo history is outside PROFILEINTEL1")

path.write_text(text, encoding="utf-8")
print("[v1.0ZD] PROFILEINTEL1 core probe added")
