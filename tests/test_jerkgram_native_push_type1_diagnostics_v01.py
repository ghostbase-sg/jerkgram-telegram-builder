from pathlib import Path
import importlib.util
import unittest


ROOT = Path(__file__).parents[1]
APPLY = ROOT / "scripts/apply_jerkgram_native_push_type1_diagnostics_v01.py"
INSTALLER = ROOT / "scripts/install_jerkgram_v12w_build133_probe_hook.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


REGISTER_FIXTURE = r'''import Foundation

// GHOSTBASE_V10E1_SPLIT_PUSH_TYPE1
func _internal_registerNotificationToken(account: Account, token: Data, type: NotificationTokenType, sandbox: Bool, otherAccountUserIds: [PeerId.Id], excludeMutedChats: Bool) -> Signal<Bool, NoError> {
    let ghostBaseRegisterDeviceKind: String
    switch type {
        case .aps:
            ghostBaseRegisterDeviceKind = "Type1"
        case .voip:
            ghostBaseRegisterDeviceKind = "Type9"
    }

    GhostBaseV10EPushProbeCore.record("registerDeviceEntry")
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
        GhostBaseV10EPushProbeCore.record("registerDeviceRequest")
        GhostBaseV10EPushProbeCore.record("registerDevice" + ghostBaseRegisterDeviceKind + "Request")
        GhostBaseV10EPushProbeCore.set("LastRegisterDeviceType", "\(mappedType)")
        return account.network.request(Api.functions.account.registerDevice(flags: flags, tokenType: mappedType, token: hexString(token), appSandbox: sandbox ? .boolTrue : .boolFalse, secret: Buffer(data: keyData), otherUids: otherAccountUserIds.map({ $0._internalGetInt64Value() })))
        |> map { _ -> Bool in
            GhostBaseV10EPushProbeCore.record("registerDeviceSuccess")
            GhostBaseV10EPushProbeCore.record("registerDevice" + ghostBaseRegisterDeviceKind + "Success")
            GhostBaseV10EPushProbeCore.set("LastRegisterDevice" + ghostBaseRegisterDeviceKind + "Error", "none")
            return true
        }
        |> `catch` { error -> Signal<Bool, NoError> in
            GhostBaseV10EPushProbeCore.set("LastRegisterDeviceError", error.errorDescription)
            GhostBaseV10EPushProbeCore.set("LastRegisterDevice" + ghostBaseRegisterDeviceKind + "Error", error.errorDescription)
            if error.errorDescription == "TOKEN_WAS_INVALIDATED" {
                GhostBaseV10EPushProbeCore.record("registerDeviceInvalidated")
                GhostBaseV10EPushProbeCore.record("registerDevice" + ghostBaseRegisterDeviceKind + "Invalidated")
                return .single(false)
            } else {
                GhostBaseV10EPushProbeCore.record("registerDeviceError")
                GhostBaseV10EPushProbeCore.record("registerDevice" + ghostBaseRegisterDeviceKind + "Error")
                return .single(true)
            }
        }
    }
}

public enum JerkgramWebPushRegistrationResult {
    case success
    case failure(code: Int32, description: String)
}
public func _internal_registerJerkgramWebPushToken(account: Account) {
    let request = Api.functions.account.registerDevice(tokenType: 10)
}
public func _internal_unregisterJerkgramWebPushToken(account: Account) {}
'''

BUILD_CONFIG_FIXTURE = r'''@implementation BuildConfig (JerkgramExtensionDiagnostics)

+ (NSString *)jerkgramExtensionDiagnosticsReport {
    NSString *group = JerkgramResolvedDiagnosticsGroup();
    NSURL *container = [NSFileManager.defaultManager containerURLForSecurityApplicationGroupIdentifier:group];
    if (container == nil) {
        return @"{\"schemaVersion\":1,\"error\":\"shared-container-unavailable\"}";
    }
    NSDictionary *report = @{};
    NSData *json = [NSJSONSerialization dataWithJSONObject:report options:0 error:nil];
    return [[NSString alloc] initWithData:json encoding:NSUTF8StringEncoding] ?: @"{}";
}

@end
'''


class NativePushType1DiagnosticsTests(unittest.TestCase):
    def test_register_patch_extends_existing_type1_probe_without_changing_stock_semantics(self):
        patch = load_module("native_type1_apply", APPLY)
        actual = patch.patch_register(REGISTER_FIXTURE)

        for token in (
            patch.SWIFT_MARKER,
            'LastRegisterDeviceType1Sandbox',
            'LastRegisterDeviceType1Encrypt',
            'LastRegisterDeviceType1SecretLength',
            'LastRegisterDeviceType1OtherUidsCount',
            'LastRegisterDeviceType1ErrorCode',
            'error.errorCode',
        ):
            self.assertIn(token, actual)

        self.assertIn('tokenType: 10', actual)
        self.assertIn('public func _internal_registerJerkgramWebPushToken(', actual)
        self.assertIn('return .single(false)', actual)
        self.assertIn('return .single(true)', actual)
        self.assertEqual(actual, patch.patch_register(actual))

    def test_copy_extension_report_contains_required_native_type1_block_without_raw_material(self):
        patch = load_module("native_type1_apply_report", APPLY)
        actual = patch.patch_build_config(BUILD_CONFIG_FIXTURE)

        for marker in (
            "=== Native Push Type1 ===",
            "APNsRegistered: %@",
            "Type1RequestCount: %ld",
            "Type1SuccessCount: %ld",
            "Type1FailureCount: %ld",
            "Sandbox: %@",
            "Encrypt: %@",
            "SecretLength: %@",
            "OtherUidsCount: %@",
            "RPCCode: %@",
            "RPCDescription: %@",
            "Timestamp: %@",
        ):
            self.assertIn(marker, actual)

        self.assertEqual(actual.count("stringByAppendingString:JerkgramNativePushType1Diagnostics()"), 2)
        helper = actual[actual.index(patch.OBJC_MARKER):actual.index("@implementation BuildConfig (JerkgramExtensionDiagnostics)")]
        for forbidden in ("hexString(token)", "p256dh", "canonicalToken", "rawBinding"):
            self.assertNotIn(forbidden, helper)
        self.assertEqual(actual, patch.patch_build_config(actual))

    def test_installer_keeps_webpush_and_makes_type1_verifier_the_final_pre_bazel_gate(self):
        installer = load_module("native_type1_installer", INSTALLER)
        order = installer.SOURCE_ORDERED

        self.assertLess(order.index("verify_jerkgram_webpush_registration_v01.py"), order.index("apply_jerkgram_native_push_type1_diagnostics_v01.py"))
        self.assertLess(order.index("verify_jerkgram_push_binding_bridge_v01.py"), order.index("apply_jerkgram_native_push_type1_diagnostics_v01.py"))
        self.assertEqual(order[-2], "apply_jerkgram_native_push_type1_diagnostics_v01.py")
        self.assertEqual(order[-1], "verify_jerkgram_native_push_type1_diagnostics_v01.py")


if __name__ == "__main__":
    unittest.main()
