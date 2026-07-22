#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src"
))
dry_run = os.environ.get("GHOSTBASE_DRY_RUN") == "1"

authorization_path = root / (
    "submodules/TelegramCore/Sources/Authorization.swift"
)

controller_path = root / (
    "submodules/AuthorizationUI/Sources/"
    "AuthorizationSequencePhoneEntryController.swift"
)

for path in (authorization_path, controller_path):
    if not path.is_file():
        raise SystemExit(f"missing generated source: {path}")

authorization = authorization_path.read_text(encoding="utf-8")
controller = controller_path.read_text(encoding="utf-8")

core_start_marker = (
    "// MARK: GhostBase v1.0Y Bot Authorization Core"
)
core_end_marker = "public enum PasswordRecoveryError"

if core_start_marker not in authorization:
    raise SystemExit("v1.0Y Bot Authorization Core marker not found")

core_start = authorization.index(core_start_marker)
core_end = authorization.index(core_end_marker, core_start)

core_block = r'''// MARK: GhostBase v1.0Y Bot Authorization Core
// MARK: GhostBase v1.0Z Bot Login migration and RPC diagnostics

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

            return authorizedAccount.postbox.transaction {
                transaction -> Signal<Void, NoError> in

                let state = AuthorizedAccountState(
                    isTestingEnvironment:
                        authorizedAccount.testingEnvironment,
                    masterDatacenterId:
                        authorizedAccount.masterDatacenterId,
                    peerId: user.id,
                    state: nil,
                    invalidatedChannels: []
                )

                initializedAppSettingsAfterLogin(
                    transaction: transaction,
                    appVersion:
                        authorizedAccount.networkArguments.appVersion,
                    syncContacts: false
                )

                transaction.setState(state)

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

        case .authorizationSignUpRequired:
            return .fail(.signUpRequired)
        }
    }
}


'''

authorization = (
    authorization[:core_start]
    + core_block
    + authorization[core_end:]
)

property_anchor = (
    "    private let hapticFeedback = HapticFeedback()\n"
)

properties = (
    "    private var ghostBaseBotLoginOpening = false\n"
    "    private var ghostBaseBotLoginActive = false\n"
)

if properties not in controller:
    if property_anchor not in controller:
        raise SystemExit("Bot Login runtime property anchor not found")

    controller = controller.replace(
        property_anchor,
        property_anchor + "\n" + properties,
        1
    )

function_start_marker = (
    "    private func openGhostBaseBotLogin() {"
)
function_end_marker = (
    "    private func loadAndPresentPasskey(force: Bool) {"
)

if function_start_marker not in controller:
    raise SystemExit("openGhostBaseBotLogin function not found")

function_start = controller.index(function_start_marker)
function_end = controller.index(
    function_end_marker,
    function_start
)

function_block = r'''    private func openGhostBaseBotLogin() {
        guard self.otherAccountPhoneNumbers.0 != nil,
              self.account != nil,
              !self.ghostBaseBotLoginOpening else {
            return
        }

        self.ghostBaseBotLoginOpening = true
        self.ghostBaseBotLoginActive = true

        self.view.endEditing(true)
        self.controllerNode.view.endEditing(true)

        DispatchQueue.main.asyncAfter(
            deadline: .now() + 0.2
        ) { [weak self] in
            guard let self, let account = self.account else {
                self?.ghostBaseBotLoginOpening = false
                self?.ghostBaseBotLoginActive = false
                return
            }

            let controller =
                AuthorizationSequencePasswordEntryController(
                    sharedContext: self.sharedContext,
                    presentationData: self.presentationData,
                    back: { [weak self] in
                        self?.ghostBaseBotLoginActive = false
                        self?.navigationController?
                            .popViewController(animated: true)
                    },
                    mode: .ghostBaseBotToken
                )

            controller.loginWithPassword = {
                [weak self, weak controller] rawToken in

                guard let self, let controller else {
                    return
                }

                let token = rawToken.trimmingCharacters(
                    in: .whitespacesAndNewlines
                )

                guard !token.isEmpty else {
                    controller.passwordIsInvalid()
                    return
                }

                controller.inProgress = true

                self.ghostBaseBotAuthorizationDisposable.set((
                    ghostBaseAuthorizeBot(
                        accountManager:
                            self.sharedContext.accountManager,
                        account: account,
                        apiId: self.apiId,
                        apiHash: self.apiHash,
                        botAuthToken: token
                    )
                    |> deliverOnMainQueue
                ).start(
                    error: {
                        [weak self, weak controller] error in

                        guard let self, let controller else {
                            return
                        }

                        controller.inProgress = false

                        let text: String

                        switch error {
                        case .invalidToken:
                            controller.passwordIsInvalid()
                            text = "Токен бота недействителен."

                        case .floodWait:
                            text =
                                "Слишком много попыток. "
                                + "Попробуйте позже."

                        case .apiIdInvalid:
                            text =
                                "Telegram отклонил API ID клиента."

                        case .botMethodInvalid:
                            text =
                                "Сервер не разрешил авторизацию бота."

                        case .signUpRequired:
                            text =
                                "Сервер запросил регистрацию "
                                + "вместо входа."

                        case let .rpc(code):
                            text =
                                "Сервер отклонил вход: \(code)"

                        case .generic:
                            text =
                                "Не удалось войти в аккаунт бота."
                        }

                        controller.present(
                            textAlertController(
                                sharedContext: self.sharedContext,
                                title: "Вход как бот",
                                text: text,
                                actions: [
                                    TextAlertAction(
                                        type: .defaultAction,
                                        title: self.presentationData
                                            .strings.Common_OK,
                                        action: {}
                                    )
                                ]
                            ),
                            in: .window(.root)
                        )
                    },
                    completed: { [weak controller] in
                        controller?.inProgress = false
                    }
                ))
            }

            self.ghostBaseBotLoginOpening = false
            self.push(controller)
        }
    }

'''

controller = (
    controller[:function_start]
    + function_block
    + controller[function_end:]
)

passkey_start_old = (
    "    private func loadAndPresentPasskey(force: Bool) {\n"
    "        if #available(iOS 16.0, *) {\n"
)

passkey_start_new = (
    "    private func loadAndPresentPasskey(force: Bool) {\n"
    "        if self.ghostBaseBotLoginActive {\n"
    "            return\n"
    "        }\n"
    "\n"
    "        if #available(iOS 16.0, *) {\n"
)

if passkey_start_new not in controller:
    if passkey_start_old not in controller:
        raise SystemExit("loadAndPresentPasskey start anchor not found")

    controller = controller.replace(
        passkey_start_old,
        passkey_start_new,
        1
    )

auth_controller_anchor = (
    "                let authController = "
    "ASAuthorizationController("
    "authorizationRequests: [platformKeyRequest])\n"
)

auth_controller_guard = (
    "                guard !self.ghostBaseBotLoginActive else {\n"
    "                    return\n"
    "                }\n"
    "\n"
    + auth_controller_anchor
)

if auth_controller_guard not in controller:
    if auth_controller_anchor not in controller:
        raise SystemExit("passkey controller creation anchor not found")

    controller = controller.replace(
        auth_controller_anchor,
        auth_controller_guard,
        1
    )

for proof in (
    "ghostBaseBotMigrationDatacenterId",
    "changedMasterDatacenterId",
    "case rpc(String)",
    "authorizedAccount.masterDatacenterId"
):
    if proof not in authorization:
        raise SystemExit(f"missing Bot Core proof: {proof}")

for proof in (
    "ghostBaseBotLoginOpening",
    "ghostBaseBotLoginActive",
    "DispatchQueue.main.asyncAfter",
    "case let .rpc(code)",
    "guard !self.ghostBaseBotLoginActive"
):
    if proof not in controller:
        raise SystemExit(f"missing Bot UI proof: {proof}")

if dry_run:
    print(f"[DRY RUN] would update {authorization_path}")
    print(f"[DRY RUN] would update {controller_path}")
else:
    authorization_path.write_text(
        authorization,
        encoding="utf-8"
    )
    controller_path.write_text(
        controller,
        encoding="utf-8"
    )

print("[v1.0Z] Bot Login runtime and migration retry OK")
