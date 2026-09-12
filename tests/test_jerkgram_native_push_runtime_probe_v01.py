from pathlib import Path
import importlib.util
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts/apply_jerkgram_native_push_runtime_probe_v01.py"


REGISTER_FIXTURE = r'''
import Foundation
import SwiftSignalKit
import Postbox
import TelegramApi

public enum NotificationTokenType {
    case aps(encrypt: Bool)
    case voip
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
            if error.errorDescription == "TOKEN_WAS_INVALIDATED" {
                return .single(false)
            } else {
                return .single(true)
            }
        }
    }
}
'''


APP_FIXTURE = r'''
import UIKit

@objc(AppDelegate) class AppDelegate: UIResponder, UIApplicationDelegate {
    @objc var window: UIWindow?

    private func handleJerkgramPushBindingUrl(_ url: URL) -> Bool {
        return false
    }

    private func handleJerkgramPushUrl(_ url: URL) -> Bool {
        return false
    }

    private func handleJerkgramExternalUrl(_ url: URL) -> Bool {
        if self.handleJerkgramPushBindingUrl(url) {
            return true
        }
        if self.handleJerkgramPushUrl(url) {
            return true
        }
        return false
    }
}
'''


class NativePushRuntimeProbeTests(unittest.TestCase):
    def load_patch(self):
        spec = importlib.util.spec_from_file_location("native_push_probe", PATCH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_type1_probe_records_attempt_success_and_exact_rpc_failure_without_changing_stock_return_semantics(self):
        module = self.load_patch()
        updated = module.patch_register_text(REGISTER_FIXTURE)

        for token in (
            "JERKGRAM_NATIVE_PUSH_TYPE1_RUNTIME_PROBE_V01",
            "jerkgram.nativePush.type1.",
            "tokenBytes: token.count",
            "secretBytes: keyData.count",
            "otherUidsCount: otherAccountUserIds.count",
            "mappedType == 1",
            "recordAttempt(",
            "recordSuccess(",
            "recordFailure(",
            "error.errorCode",
            "error.errorDescription",
        ):
            self.assertIn(token, updated)

        # Stock behavior must stay byte-for-byte equivalent in meaning: only
        # TOKEN_WAS_INVALIDATED returns false; every other RPC error returns true.
        self.assertIn('if error.errorDescription == "TOKEN_WAS_INVALIDATED"', updated)
        self.assertIn("return .single(false)", updated)
        self.assertGreaterEqual(updated.count("return .single(true)"), 1)

        # Diagnostics may store token/key lengths, never token/key material.
        recorder = updated[updated.index("private enum JerkgramNativePushRuntimeProbe"):updated.index("public enum NotificationTokenType")]
        self.assertNotIn("hexString(token)", recorder)
        self.assertNotIn("masterKey.data", recorder)
        self.assertNotIn("keyData.base64", recorder)

    def test_debug_deeplink_surfaces_last_type1_result_without_touching_existing_push_routes(self):
        module = self.load_patch()
        updated = module.patch_app_delegate_text(APP_FIXTURE)

        for token in (
            "handleJerkgramNativePushDiagnosticUrl",
            'url.path == "/native-debug"',
            'title: "Jerkgram Native Push"',
            'jerkgram.nativePush.type1.',
            'RPC: \\(errorCode) \\(errorDescription)',
            "if self.handleJerkgramNativePushDiagnosticUrl(url)",
            "if self.handleJerkgramPushBindingUrl(url)",
            "if self.handleJerkgramPushUrl(url)",
        ):
            self.assertIn(token, updated)

        dispatcher = updated[updated.index("private func handleJerkgramExternalUrl"):]
        self.assertLess(dispatcher.index("handleJerkgramNativePushDiagnosticUrl"), dispatcher.index("handleJerkgramPushBindingUrl"))
        self.assertLess(dispatcher.index("handleJerkgramPushBindingUrl"), dispatcher.index("handleJerkgramPushUrl"))

    def test_patch_is_idempotent(self):
        module = self.load_patch()
        once_register = module.patch_register_text(REGISTER_FIXTURE)
        twice_register = module.patch_register_text(once_register)
        self.assertEqual(once_register, twice_register)

        once_app = module.patch_app_delegate_text(APP_FIXTURE)
        twice_app = module.patch_app_delegate_text(once_app)
        self.assertEqual(once_app, twice_app)


if __name__ == "__main__":
    unittest.main()
