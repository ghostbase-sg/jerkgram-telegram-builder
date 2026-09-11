from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


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


def assert_diagnostic_contract(helper: str) -> None:
    assert "public enum JerkgramWebPushRegistrationResult" in helper
    assert "case success" in helper
    assert "case failure(code: Int32, description: String)" in helper
    assert helper.count("Signal<JerkgramWebPushRegistrationResult, NoError>") == 2
    assert helper.count("return .success") == 2
    assert helper.count("error.errorCode") == 2
    assert helper.count("error.errorDescription") == 2
    assert helper.count(".failure(code: error.errorCode, description: error.errorDescription)") == 2
    assert "Signal<Bool, NoError>" not in helper
    assert "return .single(false)" not in helper


def test_webpush_type10_registration_is_separate_bounded_diagnostic_and_idempotent(tmp_path: Path):
    root = tmp_path / "telegram"
    target = make_fixture(root)
    original = target.read_text()

    patcher = Path(__file__).parents[1] / "scripts/apply_jerkgram_webpush_registration_v01.py"
    first = subprocess.run([sys.executable, str(patcher), str(root)], capture_output=True, text=True)
    assert first.returncode == 0, first.stderr + first.stdout

    patched = target.read_text()

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

    assert_diagnostic_contract(helper)
    assert "retryRequest" not in helper
    assert "masterNotificationsKey" not in helper
    assert "hexString(token)" not in helper

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


class WebPushRpcDiagnosticsPreflightTest(unittest.TestCase):
    def test_runtime_helper_preserves_rpc_code_and_description(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "telegram"
            target = make_fixture(root)
            original = target.read_text()
            patcher = Path(__file__).parents[1] / "scripts/apply_jerkgram_webpush_registration_v01.py"
            result = subprocess.run([sys.executable, str(patcher), str(root)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            helper = target.read_text()[len(original):]
            assert_diagnostic_contract(helper)

    def test_binding_alert_surfaces_only_rpc_code_and_description(self):
        bridge = (Path(__file__).parents[1] / "scripts/apply_jerkgram_push_binding_bridge_v01.py").read_text()
        self.assertGreaterEqual(bridge.count("case let .failure(code, description):"), 2)
        self.assertIn('"RPC \\(code): \\(description)"', bridge)
        self.assertNotIn('RPC \\(code): \\(description) \\(canonicalToken)', bridge)
        self.assertNotIn('RPC \\(code): \\(description) \\(rawBinding)', bridge)
        self.assertNotIn("print(error.errorDescription)", bridge)
        self.assertNotIn("NSLog", bridge)


if __name__ == "__main__":
    unittest.main()
