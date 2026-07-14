#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src"
))
dry_run = os.environ.get("GHOSTBASE_DRY_RUN") == "1"

path = root / "submodules/TelegramCore/Sources/Authorization.swift"

if not path.is_file():
    raise SystemExit(f"missing source: {path}")

text = path.read_text(encoding="utf-8")
marker = "// MARK: GhostBase v1.0Y Bot Authorization Core"
anchor = "public enum PasswordRecoveryError {"

parts = []

parts.append(r'''
// MARK: GhostBase v1.0Y Bot Authorization Core

public enum GhostBaseBotAuthorizationError {
    case invalidToken
    case floodWait
    case apiIdInvalid
    case botMethodInvalid
    case signUpRequired
    case generic
}

public func ghostBaseAuthorizeBot(
    accountManager: AccountManager<TelegramAccountManagerTypes>,
    account: UnauthorizedAccount,
    apiId: Int32,
    apiHash: String,
    botAuthToken: String
) -> Signal<Never, GhostBaseBotAuthorizationError> {
    return account.network.request(
        Api.functions.auth.importBotAuthorization(
            flags: 0,
            apiId: apiId,
            apiHash: apiHash,
            botAuthToken: botAuthToken
        ),
        automaticFloodWait: false
    )
    |> mapError { error -> GhostBaseBotAuthorizationError in
        let description = error.errorDescription

        if description == "ACCESS_TOKEN_INVALID"
            || description == "BOT_TOKEN_INVALID" {
            return .invalidToken
        } else if description.hasPrefix("FLOOD_WAIT") {
            return .floodWait
        } else if description == "API_ID_INVALID" {
            return .apiIdInvalid
        } else if description == "BOT_METHOD_INVALID" {
            return .botMethodInvalid
        } else {
            return .generic
        }
    }
''')

parts.append(r'''
    |> mapToSignal { authorization
        -> Signal<Never, GhostBaseBotAuthorizationError> in

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

            return account.postbox.transaction {
                transaction -> Signal<Void, NoError> in

                let state = AuthorizedAccountState(
                    isTestingEnvironment: account.testingEnvironment,
                    masterDatacenterId: account.masterDatacenterId,
                    peerId: user.id,
                    state: nil,
                    invalidatedChannels: []
                )

                initializedAppSettingsAfterLogin(
                    transaction: transaction,
                    appVersion: account.networkArguments.appVersion,
                    syncContacts: false
                )

                transaction.setState(state)

                return accountManager.transaction {
                    transaction -> Void in

                    switchToAuthorizedAccount(
                        transaction: transaction,
                        account: account,
                        isSupportUser: isSupportUser
                    )
                }
            }
            |> switchToLatest
            |> ignoreValues
            |> castError(GhostBaseBotAuthorizationError.self)

        case .authorizationSignUpRequired:
            return .fail(.signUpRequired)
        }
    }
}
''')

addition = "\n".join(parts) + "\n\n"

if marker in text:
    patched = text
    print("[v1.0Y] Bot Authorization Core already present")
else:
    if anchor not in text:
        raise SystemExit("Authorization.swift insertion anchor not found")

    patched = text.replace(anchor, addition + anchor, 1)

    if dry_run:
        print(f"[DRY RUN] would update {path}")
    else:
        path.write_text(patched, encoding="utf-8")
        print("[v1.0Y] Bot Authorization Core added")

required = [
    marker,
    "auth.importBotAuthorization(",
    "AuthorizedAccountState(",
    "initializedAppSettingsAfterLogin(",
    "switchToAuthorizedAccount("
]

for value in required:
    if value not in patched:
        raise SystemExit(f"missing generated proof: {value}")

print("[v1.0Y] Official post-auth lifecycle anchors OK")
