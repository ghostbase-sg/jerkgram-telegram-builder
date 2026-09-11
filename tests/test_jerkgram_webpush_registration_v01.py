from pathlib import Path
import subprocess
import sys


STOCK_REGISTER_NOTIFICATION_TOKEN = """import Foundation
import SwiftSignalKit
import Postbox
import TelegramApi


public enum NotificationTokenType {
    case aps(encrypt: Bool)
    case voip
}

func _internal_unregisterNotificationToken(account: Account, token: Data, type: NotificationTokenType, otherAccountUserIds: [PeerId.Id]) -> Signal<Never, NoError> {
    let mappedType: Int32
    switch type {
        case .aps:
            mappedType = 1
        case .voip:
            mappedType = 9
    }
    return account.network.request(Api.functions.account.unregisterDevice(tokenType: mappedType, token: hexString(token), otherUids: otherAccountUserIds.map({ $0._internalGetInt64Value() })))
    |> retryRequest
    |> ignoreValues
}

func _internal_registerNotificationToken(account: Account, token: Data, type: NotificationTokenType, sandbox: Bool, otherAccountUserIds: [PeerId.Id], excludeMutedChats: Bool) -> Signal<Bool, NoError> {
    return masterNotificationsKey(account: account, ignoreDisabled: false)
    |> mapToSignal { masterKey -> Signal<Bool, NoError> in
        let mappedType: Int32
        var keyData = Data()
        switch type {
            case let .aps(encrypt):
                mappedType = 1
                if encrypt {
                    keyData = masterKey.data
                }
            case .voip:
                mappedType = 9
                keyData = masterKey.data
        }
        var flags: Int32 = 0
        if excludeMutedChats {
            flags |= 1 << 0
        }
        return account.network.request(Api.functions.account.registerDevice(flags: flags, tokenType: mappedType, token: hexString(token), appSandbox: sandbox ? .boolTrue : .boolFalse, secret: Buffer(data: keyData), otherUids: otherAccountUserIds.map({ $0._internalGetInt64Value() })))
        |> map { _ -> Bool in
            return true
        }
        |> `catch` { error -> Signal<Bool, NoError> in
            if error.errorDescription == \"TOKEN_WAS_INVALIDATED\" {
                return .single(false)
            } else {
                return .single(true)
            }
        }
    }
}
"""


def make_fixture(root: Path) -> Path:
    target = root / "submodules/TelegramCore/Sources/TelegramEngine/AccountData/RegisterNotificationToken.swift"
    target.parent.mkdir(parents=True)
    target.write_text(STOCK_REGISTER_NOTIFICATION_TOKEN)
    return target


def test_webpush_type10_registration_is_separate_bounded_and_idempotent(tmp_path: Path):
    root = tmp_path / "telegram"
    target = make_fixture(root)
    original = target.read_text()

    patcher = Path(__file__).parents[1] / "scripts/apply_jerkgram_webpush_registration_v01.py"
    first = subprocess.run([sys.executable, str(patcher), str(root)], capture_output=True, text=True)
    assert first.returncode == 0, first.stderr + first.stdout

    patched = target.read_text()

    # Stock APNs/VoIP owner is regression-locked: Jerkgram Web Push is a separate
    # helper and must not masquerade as a new NotificationTokenType case.
    assert "case aps(encrypt: Bool)" in patched
    assert "case voip" in patched
    assert "mappedType = 1" in patched
    assert "mappedType = 9" in patched
    assert "case webPush" not in patched
    assert "case .webPush" not in patched
    assert patched.startswith(original)

    register_signature = "public func _internal_registerJerkgramWebPushToken("
    unregister_signature = "public func _internal_unregisterJerkgramWebPushToken("
    assert patched.count(register_signature) == 1
    assert patched.count(unregister_signature) == 1

    helper = patched[len(original):]
    assert "account: Account" in helper
    assert "token: String" in helper
    assert "excludeMutedChats: Bool" in helper
    assert "flags |= 1 << 0" in helper
    assert "Api.functions.account.registerDevice(" in helper
    assert "tokenType: 10" in helper
    assert "token: token" in helper
    assert "appSandbox: .boolFalse" in helper
    assert "secret: Buffer(data: Data())" in helper
    assert "otherUids: []" in helper
    assert "Api.functions.account.unregisterDevice(tokenType: 10, token: token, otherUids: [])" in helper

    # Both helpers report the real request outcome instead of retrying forever or
    # converting a failure into a success state.
    assert helper.count("|> map { _ -> Bool in") == 2
    assert helper.count("return true") == 2
    assert helper.count("|> `catch` { _ -> Signal<Bool, NoError> in") == 2
    assert helper.count("return .single(false)") == 2
    assert "retryRequest" not in helper
    assert "masterNotificationsKey" not in helper
    assert "hexString(token)" not in helper

    # Sensitive Web Push capability material must never be persisted or printed.
    for forbidden in (
        "UserDefaults",
        "print(token)",
        "debugPrint(token)",
        "NSLog",
        "endpoint",
        "p256dh",
        "auth\"",
    ):
        assert forbidden not in helper

    verifier = Path(__file__).parents[1] / "scripts/verify_jerkgram_webpush_registration_v01.py"
    verified = subprocess.run([sys.executable, str(verifier), str(root)], capture_output=True, text=True)
    assert verified.returncode == 0, verified.stderr + verified.stdout
    assert "PASS" in verified.stdout

    second = subprocess.run([sys.executable, str(patcher), str(root)], capture_output=True, text=True)
    assert second.returncode == 0, second.stderr + second.stdout
    assert target.read_text() == patched
