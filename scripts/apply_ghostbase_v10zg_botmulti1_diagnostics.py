#!/usr/bin/env python3

import os
from pathlib import Path

ROOT = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
AUTH = ROOT / "submodules/TelegramCore/Sources/Authorization.swift"
SHARED = ROOT / "submodules/TelegramUI/Sources/SharedAccountContext.swift"

for path in (AUTH, SHARED):
    if not path.is_file():
        raise SystemExit(f"[V10ZG BOTMULTI1] missing source: {path}")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"[V10ZG BOTMULTI1] {label} anchor count: {count}")
    return text.replace(old, new, 1)


auth = AUTH.read_text(encoding="utf-8")
helper_marker = "// MARK: GhostBase v1.0ZG BOTMULTI1 diagnostics"
if helper_marker not in auth:
    enum_anchor = """public enum AuthorizationCodeRequestError {
    case invalidPhoneNumber
    case limitExceeded
    case generic(info: (Int, String)?)
    case phoneLimitExceeded
    case phoneBanned
    case timeout
    case appOutdated
}
"""
    helper = enum_anchor + r'''
// MARK: GhostBase v1.0ZG BOTMULTI1 diagnostics
private func ghostBaseBotMulti1Log(_ value: String) {
    Logger.shared.log("GhostBase.BotMulti1", value)
}
'''
    auth = replace_once(auth, enum_anchor, helper, "diagnostic helper")

switch_marker = "GhostBase.BotMulti1 switch authorized begin"
if switch_marker not in auth:
    auth = replace_once(
        auth,
        """func switchToAuthorizedAccount(transaction: AccountManagerModifier<TelegramAccountManagerTypes>, account: UnauthorizedAccount, isSupportUser: Bool) {
    let nextSortOrder =""",
        """func switchToAuthorizedAccount(transaction: AccountManagerModifier<TelegramAccountManagerTypes>, account: UnauthorizedAccount, isSupportUser: Bool) {
    ghostBaseBotMulti1Log(
        "GhostBase.BotMulti1 switch authorized begin account=\\(account.id) dc=\\(account.masterDatacenterId)"
    )
    let nextSortOrder =""",
        "switch-to-authorized begin",
    )
    auth = replace_once(
        auth,
        """    transaction.setCurrentId(account.id)
    transaction.removeAuth()
}
""",
        """    transaction.setCurrentId(account.id)
    transaction.removeAuth()
    ghostBaseBotMulti1Log(
        "GhostBase.BotMulti1 switch authorized completed account=\\(account.id)"
    )
}
""",
        "switch-to-authorized completion",
    )

send_start_marker = "GhostBase.BotMulti1 sendCode start"
if send_start_marker not in auth:
    signature = """public func sendAuthorizationCode(accountManager: AccountManager<TelegramAccountManagerTypes>, account: UnauthorizedAccount, phoneNumber: String, apiId: Int32, apiHash: String, pushNotificationConfiguration: AuthorizationCodePushNotificationConfiguration?, firebaseSecretStream: Signal<[String: String], NoError>, syncContacts: Bool, disableAuthTokens: Bool = false, forcedPasswordSetupNotice: @escaping (Int32) -> (NoticeEntryKey, CodableEntry)?) -> Signal<SendAuthorizationCodeResult, AuthorizationCodeRequestError> {
"""
    replacement = signature + """    ghostBaseBotMulti1Log(
        "GhostBase.BotMulti1 sendCode start account=\\(account.id) dc=\\(account.masterDatacenterId) phoneTail=\\(phoneNumber.suffix(4)) disableTokens=\\(disableAuthTokens)"
    )
"""
    auth = replace_once(auth, signature, replacement, "sendCode start")

migration_marker = "GhostBase.BotMulti1 sendCode migrate"
if migration_marker not in auth:
    old = """                    let updatedMasterDatacenterId = Int32(error.errorDescription[range.upperBound ..< error.errorDescription.endIndex])!
                    let updatedAccount = account.changedMasterDatacenterId(accountManager: accountManager, masterDatacenterId: updatedMasterDatacenterId)
"""
    new = """                    let updatedMasterDatacenterId = Int32(error.errorDescription[range.upperBound ..< error.errorDescription.endIndex])!
                    ghostBaseBotMulti1Log(
                        "GhostBase.BotMulti1 sendCode migrate account=\\(account.id) from=\\(account.masterDatacenterId) to=\\(updatedMasterDatacenterId) rpc=\\(error.errorDescription ?? \"unknown\")"
                    )
                    let updatedAccount = account.changedMasterDatacenterId(accountManager: accountManager, masterDatacenterId: updatedMasterDatacenterId)
"""
    auth = replace_once(auth, old, new, "migration log")

rpc_marker = "GhostBase.BotMulti1 sendCode rpc"
if rpc_marker not in auth:
    old = """        |> `catch` { error -> Signal<(SendCodeResult, UnauthorizedAccount), AuthorizationCodeRequestError> in
            if error.errorDescription.hasPrefix("FLOOD_WAIT") {
"""
    new = """        |> `catch` { error -> Signal<(SendCodeResult, UnauthorizedAccount), AuthorizationCodeRequestError> in
            ghostBaseBotMulti1Log(
                "GhostBase.BotMulti1 sendCode rpc account=\\(account.id) dc=\\(account.masterDatacenterId) code=\\(error.errorCode) description=\\(error.errorDescription ?? \"unknown\")"
            )
            if error.errorDescription.hasPrefix("FLOOD_WAIT") {
"""
    auth = replace_once(auth, old, new, "RPC error log")

timeout_marker = "GhostBase.BotMulti1 sendCode timeout"
if timeout_marker not in auth:
    old = """        |> timeout(20.0, queue: Queue.concurrentDefaultQueue(), alternate: .fail(.timeout))
"""
    new = """        |> timeout(
            20.0,
            queue: Queue.concurrentDefaultQueue(),
            alternate: Signal { subscriber in
                ghostBaseBotMulti1Log(
                    "GhostBase.BotMulti1 sendCode timeout account=\\(account.id) dc=\\(account.masterDatacenterId) phoneTail=\\(phoneNumber.suffix(4))"
                )
                subscriber.putError(.timeout)
                return EmptyDisposable
            }
        )
"""
    auth = replace_once(auth, old, new, "timeout diagnostic")

AUTH.write_text(auth, encoding="utf-8")

shared = SHARED.read_text(encoding="utf-8")
shared_marker = "// MARK: GhostBase v1.0ZG BOTMULTI1 auth record"
if shared_marker not in shared:
    old = """    public func beginNewAuth(testingEnvironment: Bool) {
        let _ = self.accountManager.transaction({ transaction -> Void in
            let _ = transaction.createAuth([.environment(AccountEnvironmentAttribute(environment: testingEnvironment ? .test : .production))])
        }).start()
    }
"""
    new = """    public func beginNewAuth(testingEnvironment: Bool) {
        let _ = self.accountManager.transaction({ transaction -> Void in
            // MARK: GhostBase v1.0ZG BOTMULTI1 auth record
            let authId = transaction.createAuth([
                .environment(
                    AccountEnvironmentAttribute(
                        environment: testingEnvironment ? .test : .production
                    )
                )
            ])
            Logger.shared.log(
                "GhostBase.BotMulti1",
                "GhostBase.BotMulti1 createAuth id=\\(authId) testing=\\(testingEnvironment)"
            )
        }).start()
    }
"""
    shared = replace_once(shared, old, new, "beginNewAuth")
    SHARED.write_text(shared, encoding="utf-8")

for proof in (
    helper_marker,
    "GhostBase.BotMulti1 sendCode start",
    "GhostBase.BotMulti1 sendCode migrate",
    "GhostBase.BotMulti1 sendCode rpc",
    "GhostBase.BotMulti1 sendCode timeout",
    "GhostBase.BotMulti1 switch authorized completed",
):
    if proof not in auth:
        raise SystemExit(f"[V10ZG BOTMULTI1] missing auth proof: {proof}")
if shared_marker not in shared or "transaction.createAuth" not in shared:
    raise SystemExit("[V10ZG BOTMULTI1] missing auth-record proof")

print("[V10ZG] BOTMULTI1 diagnostics applied")
print("[V10ZG] logs: createAuth, sendCode start/RPC/migrate/timeout, switch authorized")
