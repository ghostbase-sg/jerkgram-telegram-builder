#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
TARGET = ROOT / "submodules/TelegramCore/Sources/TelegramEngine/AccountData/RegisterNotificationToken.swift"

errors = []
if not TARGET.exists():
    errors.append(f"missing RegisterNotificationToken.swift: {TARGET}")
else:
    text = TARGET.read_text()
    register_marker = "public func _internal_registerJerkgramWebPushToken("
    unregister_marker = "public func _internal_unregisterJerkgramWebPushToken("

    for required in (
        "public enum NotificationTokenType",
        "case aps(encrypt: Bool)",
        "case voip",
        "mappedType = 1",
        "mappedType = 9",
        "func _internal_unregisterNotificationToken(",
        "func _internal_registerNotificationToken(",
        register_marker,
        unregister_marker,
        "account: Account",
        "token: String",
        "excludeMutedChats: Bool",
        "flags |= 1 << 0",
        "Api.functions.account.registerDevice(",
        "tokenType: 10",
        "token: token",
        "appSandbox: .boolFalse",
        "secret: Buffer(data: Data())",
        "otherUids: []",
        "Api.functions.account.unregisterDevice(tokenType: 10, token: token, otherUids: [])",
    ):
        if required not in text:
            errors.append(f"missing invariant: {required}")

    if text.count(register_marker) != 1:
        errors.append(f"register helper count={text.count(register_marker)}, expected 1")
    if text.count(unregister_marker) != 1:
        errors.append(f"unregister helper count={text.count(unregister_marker)}, expected 1")

    if register_marker in text:
        helper = text[text.index(register_marker):]
        if helper.count("|> map { _ -> Bool in") != 2:
            errors.append("Web Push helpers must map exactly two request successes")
        if helper.count("return true") != 2:
            errors.append("Web Push helpers must return true exactly twice on success")
        if helper.count("|> `catch` { _ -> Signal<Bool, NoError> in") != 2:
            errors.append("Web Push helpers must catch exactly two request failures")
        if helper.count("return .single(false)") != 2:
            errors.append("Web Push helpers must return false exactly twice on failure")
        for forbidden in (
            "retryRequest",
            "masterNotificationsKey",
            "hexString(token)",
            "UserDefaults",
            "print(token)",
            "debugPrint(token)",
            "NSLog",
            "endpoint",
            "p256dh",
        ):
            if forbidden in helper:
                errors.append(f"Web Push helper contains forbidden dependency/logging: {forbidden}")

    if "case .webPush" in text or "case webPush" in text:
        errors.append("NotificationTokenType must remain APNs/VoIP-only")

if errors:
    print("[jerkgram-webpush-registration-verify] FAIL")
    for error in errors:
        print(" -", error)
    raise SystemExit(1)

print("[jerkgram-webpush-registration-verify] PASS")
