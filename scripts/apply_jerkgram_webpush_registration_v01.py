#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
TARGET = ROOT / "submodules/TelegramCore/Sources/TelegramEngine/AccountData/RegisterNotificationToken.swift"

if not TARGET.exists():
    raise SystemExit(f"[jerkgram-webpush-registration] missing {TARGET}")

text = TARGET.read_text()
REGISTER_MARKER = "public func _internal_registerJerkgramWebPushToken("
UNREGISTER_MARKER = "public func _internal_unregisterJerkgramWebPushToken("
RESULT_MARKER = "public enum JerkgramWebPushRegistrationResult"

if (REGISTER_MARKER in text) != (UNREGISTER_MARKER in text):
    raise SystemExit("[jerkgram-webpush-registration] partial Web Push helper patch detected")

if REGISTER_MARKER not in text:
    for stock_marker in (
        "public enum NotificationTokenType",
        "case aps(encrypt: Bool)",
        "case voip",
        "mappedType = 1",
        "mappedType = 9",
        "func _internal_unregisterNotificationToken(",
        "func _internal_registerNotificationToken(",
    ):
        if stock_marker not in text:
            raise SystemExit(f"[jerkgram-webpush-registration] stock anchor missing: {stock_marker}")

    helper = r'''

// MARK: Jerkgram Web Push type-10 registration
// Keep Telegram's RPC code/description for the first real-device integration pass.
// Capability material (endpoint/keys/token) is never included in this result.
public enum JerkgramWebPushRegistrationResult {
    case success
    case failure(code: Int32, description: String)
}

// This is deliberately separate from NotificationTokenType. The stock enum owns
// APNs/VoIP tokens, while this helper receives an already validated canonical Web
// Push subscription JSON string from the Jerkgram-owned URL bridge.
public func _internal_registerJerkgramWebPushToken(
    account: Account,
    token: String,
    excludeMutedChats: Bool
) -> Signal<JerkgramWebPushRegistrationResult, NoError> {
    var flags: Int32 = 0
    if excludeMutedChats {
        flags |= 1 << 0
    }

    return account.network.request(Api.functions.account.registerDevice(
        flags: flags,
        tokenType: 10,
        token: token,
        appSandbox: .boolFalse,
        secret: Buffer(data: Data()),
        otherUids: []
    ))
    |> map { _ -> JerkgramWebPushRegistrationResult in
        return .success
    }
    |> `catch` { error -> Signal<JerkgramWebPushRegistrationResult, NoError> in
        return .single(.failure(code: error.errorCode, description: error.errorDescription))
    }
}

public func _internal_unregisterJerkgramWebPushToken(
    account: Account,
    token: String
) -> Signal<JerkgramWebPushRegistrationResult, NoError> {
    return account.network.request(Api.functions.account.unregisterDevice(tokenType: 10, token: token, otherUids: []))
    |> map { _ -> JerkgramWebPushRegistrationResult in
        return .success
    }
    |> `catch` { error -> Signal<JerkgramWebPushRegistrationResult, NoError> in
        return .single(.failure(code: error.errorCode, description: error.errorDescription))
    }
}
'''
    text = text.rstrip("\n") + "\n" + helper
    TARGET.write_text(text)

patched = TARGET.read_text()
for required in (
    RESULT_MARKER,
    "case success",
    "case failure(code: Int32, description: String)",
    REGISTER_MARKER,
    UNREGISTER_MARKER,
    "Signal<JerkgramWebPushRegistrationResult, NoError>",
    "error.errorCode",
    "error.errorDescription",
    ".failure(code: error.errorCode, description: error.errorDescription)",
    "tokenType: 10",
    "appSandbox: .boolFalse",
    "secret: Buffer(data: Data())",
    "otherUids: []",
    "flags |= 1 << 0",
):
    if required not in patched:
        raise SystemExit(f"[jerkgram-webpush-registration] invariant missing after patch: {required}")

if patched.count(RESULT_MARKER) != 1:
    raise SystemExit("[jerkgram-webpush-registration] result enum count is not exactly one")
if patched.count(REGISTER_MARKER) != 1 or patched.count(UNREGISTER_MARKER) != 1:
    raise SystemExit("[jerkgram-webpush-registration] helper count is not exactly one each")
if patched.count("error.errorCode") != 2 or patched.count("error.errorDescription") < 2:
    raise SystemExit("[jerkgram-webpush-registration] RPC diagnostics must be preserved for register and unregister")

if "case .webPush" in patched or "case webPush" in patched:
    raise SystemExit("[jerkgram-webpush-registration] NotificationTokenType must not gain a Web Push case")

print("[jerkgram-webpush-registration] OK")
print("  patched:", TARGET)
