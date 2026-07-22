#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))

paths = {
    "authorization": root / "submodules/TelegramCore/Sources/Authorization.swift",
    "state_utils": root / "submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift",
    "fetch_chat_list": root / "submodules/TelegramCore/Sources/State/FetchChatList.swift",
    "pinned": root / "submodules/TelegramCore/Sources/State/ManagedSynchronizePinnedChatsOperations.swift",
    "account_row": root / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/ListItems/PeerInfoScreenMemberItem.swift",
}

for name, path in paths.items():
    if not path.is_file():
        raise SystemExit(f"[v1.0ZC Bot Inbox] missing {name}: {path}")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"[v1.0ZC Bot Inbox] {label} anchor count: {count}")
    return text.replace(old, new, 1)

# 1) Safe bot authorization + best-effort backlog bootstrap.
authorization_path = paths["authorization"]
authorization = authorization_path.read_text(encoding="utf-8")
start_marker = "// MARK: GhostBase v1.0Y Bot Authorization Core"
end_marker = "public enum PasswordRecoveryError"
if start_marker not in authorization or end_marker not in authorization:
    raise SystemExit("[v1.0ZC Bot Inbox] authorization markers missing")
start = authorization.index(start_marker)
end = authorization.index(end_marker, start)

core = r'''// MARK: GhostBase v1.0Y Bot Authorization Core
// MARK: GhostBase v1.0ZC Persistent Bot Inbox

public enum GhostBaseBotAuthorizationError {
    case invalidToken
    case floodWait
    case apiIdInvalid
    case botMethodInvalid
    case signUpRequired
    case rpc(String)
    case generic
}

private func ghostBaseBotSafeRpcCode(
    _ description: String
) -> String {
    let normalized = description.uppercased().filter { character in
        character.isLetter
        || character.isNumber
        || character == "_"
        || character == "-"
        || character == "."
    }

    if normalized.isEmpty {
        return "UNKNOWN_RPC_ERROR"
    }

    return String(normalized.prefix(96))
}

private func ghostBaseBotMigrationDatacenterId(
    _ description: String
) -> Int32? {
    for prefix in [
        "PHONE_MIGRATE_",
        "USER_MIGRATE_",
        "NETWORK_MIGRATE_"
    ] {
        guard description.hasPrefix(prefix) else {
            continue
        }

        return Int32(description.dropFirst(prefix.count))
    }

    return nil
}

private func ghostBaseImportBotAuthorization(
    accountManager: AccountManager<TelegramAccountManagerTypes>,
    account: UnauthorizedAccount,
    apiId: Int32,
    apiHash: String,
    botAuthToken: String,
    didMigrate: Bool
) -> Signal<
    (Api.auth.Authorization, UnauthorizedAccount),
    GhostBaseBotAuthorizationError
> {
    return account.network.request(
        Api.functions.auth.importBotAuthorization(
            flags: 0,
            apiId: apiId,
            apiHash: apiHash,
            botAuthToken: botAuthToken
        ),
        automaticFloodWait: false
    )
    |> map { authorization in
        return (authorization, account)
    }
    |> `catch` {
        error -> Signal<
            (Api.auth.Authorization, UnauthorizedAccount),
            GhostBaseBotAuthorizationError
        > in

        let description = error.errorDescription ?? ""
        let safeCode = ghostBaseBotSafeRpcCode(description)

        if !didMigrate,
           let datacenterId =
                ghostBaseBotMigrationDatacenterId(description),
           datacenterId != account.masterDatacenterId {
            return account.changedMasterDatacenterId(
                accountManager: accountManager,
                masterDatacenterId: datacenterId
            )
            |> castError(GhostBaseBotAuthorizationError.self)
            |> mapToSignal { updatedAccount in
                return ghostBaseImportBotAuthorization(
                    accountManager: accountManager,
                    account: updatedAccount,
                    apiId: apiId,
                    apiHash: apiHash,
                    botAuthToken: botAuthToken,
                    didMigrate: true
                )
            }
        }

        if description == "ACCESS_TOKEN_INVALID"
            || description == "BOT_TOKEN_INVALID" {
            return .fail(.invalidToken)
        } else if description.hasPrefix("FLOOD_WAIT") {
            return .fail(.floodWait)
        } else if description == "API_ID_INVALID" {
            return .fail(.apiIdInvalid)
        } else if description == "BOT_METHOD_INVALID" {
            return .fail(.botMethodInvalid)
        } else {
            return .fail(.rpc(safeCode))
        }
    }
}

private func ghostBaseBotInitialState(
    account: UnauthorizedAccount
) -> Signal<AuthorizedAccountState.State?, NoError> {
    let remoteState = account.network.request(
        Api.functions.updates.getState(),
        automaticFloodWait: false
    )
    |> map(Optional.init)
    |> `catch` { _ -> Signal<Api.updates.State?, NoError> in
        return .single(nil)
    }

    return remoteState
    |> mapToSignal {
        remoteState -> Signal<AuthorizedAccountState.State?, NoError> in

        guard let remoteState else {
            return .single(nil)
        }

        switch remoteState {
        case let .state(data):
            let currentState = AuthorizedAccountState.State(
                pts: data.pts,
                qts: data.qts,
                date: data.date,
                seq: data.seq
            )

            guard data.unreadCount > 0, data.pts > 1 else {
                return .single(currentState)
            }

            let candidatePts = max(
                Int32(1),
                data.pts - data.unreadCount
            )

            guard candidatePts < data.pts else {
                return .single(currentState)
            }

            return account.network.request(
                Api.functions.updates.getDifference(
                    flags: 0,
                    pts: candidatePts,
                    ptsLimit: nil,
                    ptsTotalLimit: nil,
                    date: data.date,
                    qts: data.qts,
                    qtsLimit: nil
                ),
                automaticFloodWait: false
            )
            |> map { difference -> AuthorizedAccountState.State? in
                switch difference {
                case .difference, .differenceSlice:
                    return AuthorizedAccountState.State(
                        pts: candidatePts,
                        qts: data.qts,
                        date: data.date,
                        seq: data.seq
                    )
                case .differenceEmpty, .differenceTooLong:
                    return currentState
                }
            }
            |> `catch` { _ -> Signal<AuthorizedAccountState.State?, NoError> in
                return .single(currentState)
            }
        }
    }
}

public func ghostBaseAuthorizeBot(
    accountManager: AccountManager<TelegramAccountManagerTypes>,
    account: UnauthorizedAccount,
    apiId: Int32,
    apiHash: String,
    botAuthToken: String
) -> Signal<Never, GhostBaseBotAuthorizationError> {
    return ghostBaseImportBotAuthorization(
        accountManager: accountManager,
        account: account,
        apiId: apiId,
        apiHash: apiHash,
        botAuthToken: botAuthToken,
        didMigrate: false
    )
    |> mapToSignal {
        result -> Signal<Never, GhostBaseBotAuthorizationError> in

        let (authorization, authorizedAccount) = result

        switch authorization {
        case let .authorization(data):
            if let futureAuthToken = data.futureAuthToken {
                storeFutureLoginToken(
                    accountManager: accountManager,
                    token: futureAuthToken.makeData()
                )
            }

            let user = TelegramUser(user: data.user)

            var isSupportUser = false
            if let phone = user.phone, phone.hasPrefix("42") {
                isSupportUser = true
            }

            return ghostBaseBotInitialState(account: authorizedAccount)
            |> castError(GhostBaseBotAuthorizationError.self)
            |> mapToSignal {
                initialState -> Signal<Never, GhostBaseBotAuthorizationError> in

                return authorizedAccount.postbox.transaction {
                    transaction -> Signal<Void, NoError> in

                    let state = AuthorizedAccountState(
                        isTestingEnvironment:
                            authorizedAccount.testingEnvironment,
                        masterDatacenterId:
                            authorizedAccount.masterDatacenterId,
                        peerId: user.id,
                        state: initialState,
                        invalidatedChannels: []
                    )

                    initializedAppSettingsAfterLogin(
                        transaction: transaction,
                        appVersion:
                            authorizedAccount.networkArguments.appVersion,
                        syncContacts: false
                    )

                    transaction.updatePeersInternal(
                        [user],
                        update: { _, updated in
                            return updated
                        }
                    )
                    transaction.setState(state)

                    UserDefaults.standard.set(
                        true,
                        forKey:
                            "GhostBase.BotAccount.\(user.id.toInt64())"
                    )

                    return accountManager.transaction {
                        transaction -> Void in

                        switchToAuthorizedAccount(
                            transaction: transaction,
                            account: authorizedAccount,
                            isSupportUser: isSupportUser
                        )
                    }
                }
                |> switchToLatest
                |> ignoreValues
                |> castError(GhostBaseBotAuthorizationError.self)
            }

        case .authorizationSignUpRequired:
            return .fail(.signUpRequired)
        }
    }
}


'''
authorization = authorization[:start] + core + authorization[end:]
authorization_path.write_text(authorization, encoding="utf-8")

# 2) Bot account marker helper and no getPeerDialogs discard.
state_path = paths["state_utils"]
state = state_path.read_text(encoding="utf-8")
helper_marker = "// MARK: GhostBase v1.0ZC Bot account detection"
if helper_marker not in state:
    anchor = "private func resolveMissingPeerChatInfos(accountPeerId: PeerId, network: Network, state: AccountMutableState) -> Signal<(AccountMutableState, Bool), NoError> {\n"
    helper = '''// MARK: GhostBase v1.0ZC Bot account detection\nfunc ghostBaseIsBotAccount(_ accountPeerId: PeerId) -> Bool {\n    return UserDefaults.standard.bool(\n        forKey: "GhostBase.BotAccount.\\(accountPeerId.toInt64())"\n    )\n}\n\n'''
    state = replace_once(state, anchor, helper + anchor, "state helper")

skip_marker = "// MARK: GhostBase v1.0ZC Bot local PeerChatInfo"
if skip_marker not in state:
    anchor = '''    if missingPeers.isEmpty {
        return .single((state, hadError))
    } else {
'''
    replacement = '''    // MARK: GhostBase v1.0ZC Bot local PeerChatInfo
    if ghostBaseIsBotAccount(accountPeerId) {
        var updatedState = state

        for peerId in missingPeers.keys {
            updatedState.peerChatInfos[peerId] = PeerChatInfo(
                notificationSettings:
                    TelegramPeerNotificationSettings.defaultSettings
            )
            updatedState.updatePeerChatInclusion(
                peerId: peerId,
                groupId: .root,
                changedGroup: false
            )
        }

        return .single((updatedState, false))
    }

    if missingPeers.isEmpty {
        return .single((state, hadError))
    } else {
'''
    state = replace_once(state, anchor, replacement, "PeerChatInfo bypass")
state_path.write_text(state, encoding="utf-8")

# 3) Never call getDialogs/getPinnedDialogs for bot accounts.
fetch_path = paths["fetch_chat_list"]
fetch = fetch_path.read_text(encoding="utf-8")
fetch_marker = "// MARK: GhostBase v1.0ZC Bot local chat list"
if fetch_marker not in fetch:
    anchor = '''func fetchChatList(accountPeerId: PeerId, postbox: Postbox, network: Network, location: FetchChatListLocation, upperBound: MessageIndex, hash: Int64, limit: Int32) -> Signal<FetchedChatList?, NoError> {
    return postbox.stateView()
'''
    replacement = '''func fetchChatList(accountPeerId: PeerId, postbox: Postbox, network: Network, location: FetchChatListLocation, upperBound: MessageIndex, hash: Int64, limit: Int32) -> Signal<FetchedChatList?, NoError> {
    // MARK: GhostBase v1.0ZC Bot local chat list
    if ghostBaseIsBotAccount(accountPeerId) {
        return .single(nil)
    }

    return postbox.stateView()
'''
    fetch = replace_once(fetch, anchor, replacement, "fetchChatList")
fetch_path.write_text(fetch, encoding="utf-8")

pinned_path = paths["pinned"]
pinned = pinned_path.read_text(encoding="utf-8")
pinned_marker = "// MARK: GhostBase v1.0ZC Bot pinned-dialog bypass"
if pinned_marker not in pinned:
    anchor = '''private func synchronizePinnedChats(transaction: Transaction, postbox: Postbox, network: Network, accountPeerId: PeerId, stateManager: AccountStateManager, groupId: PeerGroupId, operation: SynchronizePinnedChatsOperation) -> Signal<Void, NoError> {
    let initialRemoteItemIds = operation.previousItemIds
'''
    replacement = '''private func synchronizePinnedChats(transaction: Transaction, postbox: Postbox, network: Network, accountPeerId: PeerId, stateManager: AccountStateManager, groupId: PeerGroupId, operation: SynchronizePinnedChatsOperation) -> Signal<Void, NoError> {
    // MARK: GhostBase v1.0ZC Bot pinned-dialog bypass
    if ghostBaseIsBotAccount(accountPeerId) {
        return .complete()
    }

    let initialRemoteItemIds = operation.previousItemIds
'''
    pinned = replace_once(pinned, anchor, replacement, "pinned bypass")
pinned_path.write_text(pinned, encoding="utf-8")

# 4) Purple BOT capsule immediately after the displayed account name.
row_path = paths["account_row"]
row = row_path.read_text(encoding="utf-8")
row_marker = "// MARK: GhostBase v1.0ZC Account BOT badge"
if row_marker not in row:
    row = replace_once(
        row,
        '''    private let bottomSeparatorNode: ASDisplayNode
    
    private var item: PeerInfoScreenMemberItem?
''',
        '''    private let bottomSeparatorNode: ASDisplayNode

    // MARK: GhostBase v1.0ZC Account BOT badge
    private let ghostBaseBotBadgeBackgroundNode: ASDisplayNode
    private let ghostBaseBotBadgeTextNode: ImmediateTextNode
    
    private var item: PeerInfoScreenMemberItem?
''',
        "badge properties"
    )

    row = replace_once(
        row,
        '''        self.bottomSeparatorNode = ASDisplayNode()
        self.bottomSeparatorNode.isLayerBacked = true
        
        super.init()
''',
        '''        self.bottomSeparatorNode = ASDisplayNode()
        self.bottomSeparatorNode.isLayerBacked = true

        self.ghostBaseBotBadgeBackgroundNode = ASDisplayNode()
        self.ghostBaseBotBadgeBackgroundNode.isUserInteractionEnabled = false
        self.ghostBaseBotBadgeTextNode = ImmediateTextNode()
        self.ghostBaseBotBadgeTextNode.isUserInteractionEnabled = false
        
        super.init()
''',
        "badge init"
    )

    row = replace_once(
        row,
        '''        self.addSubnode(self.bottomSeparatorNode)
        self.addSubnode(self.selectionNode)
''',
        '''        self.addSubnode(self.bottomSeparatorNode)
        self.addSubnode(self.selectionNode)
        self.addSubnode(self.ghostBaseBotBadgeBackgroundNode)
        self.addSubnode(self.ghostBaseBotBadgeTextNode)
''',
        "badge subnodes"
    )

    row = replace_once(
        row,
        '''        self.item = item
        
        self.selectionNode.pressed = item.action.flatMap { action in
''',
        '''        self.item = item

        let ghostBaseIsBotAccountRow: Bool
        if item.isAccount,
           case let .user(user) = item.member.peer,
           user.botInfo != nil {
            ghostBaseIsBotAccountRow = true
        } else {
            ghostBaseIsBotAccountRow = false
        }
        
        self.selectionNode.pressed = item.action.flatMap { action in
''',
        "badge bot flag"
    )

    row = replace_once(
        row,
        '''        let height = itemNode.contentSize.height
        
        transition.updateFrame(node: itemNode, frame: CGRect(origin: CGPoint(), size: itemNode.bounds.size))
''',
        '''        let height = itemNode.contentSize.height

        if ghostBaseIsBotAccountRow {
            let badgeTextColor = UIColor(rgb: 0x8f5bd7)
            let badgeBackgroundColor = badgeTextColor.withAlphaComponent(0.18)
            let badgeFont = Font.semibold(10.0)

            self.ghostBaseBotBadgeTextNode.attributedText = NSAttributedString(
                string: "BOT",
                font: badgeFont,
                textColor: badgeTextColor
            )

            let textSize = self.ghostBaseBotBadgeTextNode.updateLayout(
                CGSize(width: 40.0, height: 20.0)
            )
            let badgeSize = CGSize(
                width: ceil(textSize.width) + 10.0,
                height: 18.0
            )

            let displayTitle = item.member.peer.displayTitle(
                strings: presentationData.strings,
                displayOrder: presentationData.nameDisplayOrder
            )
            let titleWidth = ceil((displayTitle as NSString).size(
                withAttributes: [
                    .font: Font.regular(17.0)
                ]
            ).width)

            let titleOriginX = sideInset + 49.0
            let reservedRightWidth: CGFloat = item.badge == nil ? 16.0 : 58.0
            let maximumBadgeX = width
                - safeInsets.right
                - reservedRightWidth
                - badgeSize.width
            let badgeX = max(
                titleOriginX,
                min(titleOriginX + titleWidth + 7.0, maximumBadgeX)
            )
            let badgeY = floor((height - badgeSize.height) * 0.5)

            self.ghostBaseBotBadgeBackgroundNode.backgroundColor = badgeBackgroundColor
            self.ghostBaseBotBadgeBackgroundNode.cornerRadius = badgeSize.height * 0.5
            self.ghostBaseBotBadgeBackgroundNode.isHidden = false
            self.ghostBaseBotBadgeTextNode.isHidden = false

            transition.updateFrame(
                node: self.ghostBaseBotBadgeBackgroundNode,
                frame: CGRect(origin: CGPoint(x: badgeX, y: badgeY), size: badgeSize)
            )
            transition.updateFrame(
                node: self.ghostBaseBotBadgeTextNode,
                frame: CGRect(
                    origin: CGPoint(
                        x: badgeX + floor((badgeSize.width - textSize.width) * 0.5),
                        y: badgeY + floor((badgeSize.height - textSize.height) * 0.5)
                    ),
                    size: textSize
                )
            )
        } else {
            self.ghostBaseBotBadgeBackgroundNode.isHidden = true
            self.ghostBaseBotBadgeTextNode.isHidden = true
        }
        
        transition.updateFrame(node: itemNode, frame: CGRect(origin: CGPoint(), size: itemNode.bounds.size))
''',
        "badge layout"
    )

row_path.write_text(row, encoding="utf-8")

# Proofs.
proofs = {
    authorization_path: [
        "GhostBase v1.0ZC Persistent Bot Inbox",
        "ghostBaseBotInitialState",
        "data.pts - data.unreadCount",
        "transaction.updatePeersInternal",
        "GhostBase.BotAccount.",
    ],
    state_path: [
        "ghostBaseIsBotAccount",
        "GhostBase v1.0ZC Bot local PeerChatInfo",
        "TelegramPeerNotificationSettings.defaultSettings",
        "updatedState.updatePeerChatInclusion",
    ],
    fetch_path: [
        "GhostBase v1.0ZC Bot local chat list",
        "return .single(nil)",
    ],
    pinned_path: [
        "GhostBase v1.0ZC Bot pinned-dialog bypass",
        "return .complete()",
    ],
    row_path: [
        "GhostBase v1.0ZC Account BOT badge",
        'string: "BOT"',
        "user.botInfo != nil",
        "badgeTextColor.withAlphaComponent(0.18)",
    ],
}

for path, required in proofs.items():
    text = path.read_text(encoding="utf-8")
    for value in required:
        if value not in text:
            raise SystemExit(f"[v1.0ZC Bot Inbox] missing proof {value} in {path}")

if "pts: 0,\n                        qts: 0,\n                        date: 0" in authorization:
    raise SystemExit("[v1.0ZC Bot Inbox] invalid persistent zero state remains")

print("[v1.0ZC] safe bot authorization state installed")
print("[v1.0ZC] best-effort unread backlog bootstrap installed")
print("[v1.0ZC] bot getPeerDialogs discard bypassed")
print("[v1.0ZC] bot getDialogs/getPinnedDialogs bypassed")
print("[v1.0ZC] persistent personal/group/channel inbox enabled")
print("[v1.0ZC] purple BOT badge added after displayed account name")
