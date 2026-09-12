from pathlib import Path
import importlib.util
import unittest


REPO = Path(__file__).resolve().parents[1]
APPLY = REPO / "scripts/apply_jerkgram_native_push_runtime_probe_v01.py"
VERIFY = REPO / "scripts/verify_jerkgram_native_push_runtime_probe_v01.py"
INSTALLER = REPO / "scripts/install_jerkgram_v12w_build133_probe_hook.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


REGISTER_FIXTURE = r'''
import Foundation

func _internal_registerNotificationToken(account: Account, token: Data, type: NotificationTokenType, sandbox: Bool, otherAccountUserIds: [PeerId.Id], excludeMutedChats: Bool) -> Signal<Bool, NoError> {
    let ghostBaseRegisterDeviceKind: String
    switch type {
        case .aps:
            ghostBaseRegisterDeviceKind = "Type1"
        case .voip:
            ghostBaseRegisterDeviceKind = "Type9"
    }

    GhostBaseV10EPushProbeCore.record("registerDeviceEntry")
    GhostBaseV10EPushProbeCore.record("registerDevice" + ghostBaseRegisterDeviceKind + "Entry")
    GhostBaseV10EPushProbeCore.set("LastRegisterDeviceKind", ghostBaseRegisterDeviceKind)

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

        GhostBaseV10EPushProbeCore.record("registerDeviceRequest")
        GhostBaseV10EPushProbeCore.record("registerDevice" + ghostBaseRegisterDeviceKind + "Request")
        GhostBaseV10EPushProbeCore.set("LastRegisterDeviceType", "\(mappedType)")
        GhostBaseV10EPushProbeCore.set("LastRegisterDeviceTypeRaw", "\(mappedType)")
        GhostBaseV10EPushProbeCore.setRegisterDeviceTypeSummary(lastType: mappedType, kind: ghostBaseRegisterDeviceKind)
        GhostBaseV10EPushProbeCore.set("LastRegisterDeviceSecretLength", "\(keyData.count)")
        return account.network.request(Api.functions.account.registerDevice(flags: flags, tokenType: mappedType, token: hexString(token), appSandbox: sandbox ? .boolTrue : .boolFalse, secret: Buffer(data: keyData), otherUids: otherAccountUserIds.map({ $0._internalGetInt64Value() })))
        |> map { _ -> Bool in
            GhostBaseV10EPushProbeCore.record("registerDeviceSuccess")
            GhostBaseV10EPushProbeCore.record("registerDevice" + ghostBaseRegisterDeviceKind + "Success")
            GhostBaseV10EPushProbeCore.set("LastRegisterDevice" + ghostBaseRegisterDeviceKind + "Error", "none")
            GhostBaseV10EPushProbeCore.setRegisterDeviceTypeSummary(lastType: mappedType, kind: ghostBaseRegisterDeviceKind)
            return true
        }
        |> `catch` { error -> Signal<Bool, NoError> in
            GhostBaseV10EPushProbeCore.set("LastRegisterDeviceError", error.errorDescription)
            if error.errorDescription == "TOKEN_WAS_INVALIDATED" {
                GhostBaseV10EPushProbeCore.record("registerDeviceInvalidated")
                GhostBaseV10EPushProbeCore.record("registerDevice" + ghostBaseRegisterDeviceKind + "Invalidated")
                GhostBaseV10EPushProbeCore.setRegisterDeviceTypeSummary(lastType: mappedType, kind: ghostBaseRegisterDeviceKind)
                return .single(false)
            } else {
                GhostBaseV10EPushProbeCore.record("registerDeviceError")
                GhostBaseV10EPushProbeCore.record("registerDevice" + ghostBaseRegisterDeviceKind + "Error")
                GhostBaseV10EPushProbeCore.setRegisterDeviceTypeSummary(lastType: mappedType, kind: ghostBaseRegisterDeviceKind)
                return .single(true)
            }
        }
    }
}

public enum JerkgramWebPushRegistrationResult {
    case success
    case failure(code: Int32, description: String)
}
public func _internal_registerJerkgramWebPushToken(account: Account, token: String, excludeMutedChats: Bool) -> Signal<JerkgramWebPushRegistrationResult, NoError> {
    return account.network.request(Api.functions.account.registerDevice(flags: 0, tokenType: 10, token: token, appSandbox: .boolFalse, secret: Buffer(data: Data()), otherUids: []))
    |> map { _ in .success }
    |> `catch` { error in .single(.failure(code: error.errorCode, description: error.errorDescription)) }
}
public func _internal_unregisterJerkgramWebPushToken(account: Account, token: String) -> Signal<JerkgramWebPushRegistrationResult, NoError> {
    return .single(.success)
}
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

SETTINGS_FIXTURE = r'''            switch action {
            case "copyExtensionDiagnostics":
                UIPasteboard.general.string = BuildConfig.jerkgramExtensionDiagnosticsReport()
            default:
                break
            }
'''


class NativePushRuntimeProbeTests(unittest.TestCase):
    def test_official_v10e1_indentation_is_extended_without_second_interceptor_or_semantic_change(self):
        patch = load_module("native_push_apply", APPLY)

        self.assertIn('registerDevice" + ghostBaseRegisterDeviceKind + "Request"', REGISTER_FIXTURE)
        self.assertIn("\n            case let .aps(encrypt):\n", REGISTER_FIXTURE)
        self.assertNotIn("JERKGRAM_NATIVE_PUSH_TYPE1_RUNTIME_PROBE_V01", REGISTER_FIXTURE)
        self.assertNotIn(
            'LastRegisterDevice" + ghostBaseRegisterDeviceKind + "Error", error.errorDescription',
            REGISTER_FIXTURE,
        )

        updated = patch.patch_register_text(REGISTER_FIXTURE)
        for token in (
            patch.SWIFT_MARKER,
            "jerkgramType1Encrypt = encrypt",
            "LastRegisterDeviceType1Sandbox",
            "LastRegisterDeviceType1Encrypt",
            "LastRegisterDeviceType1SecretLength",
            "LastRegisterDeviceType1OtherUidsCount",
            "LastRegisterDeviceType1ErrorCode",
            'LastRegisterDeviceType1Error", error.errorDescription',
            "error.errorCode",
        ):
            self.assertIn(token, updated)

        self.assertIn("public func _internal_registerJerkgramWebPushToken(", updated)
        self.assertIn("tokenType: 10", updated)
        self.assertIn('if error.errorDescription == "TOKEN_WAS_INVALIDATED"', updated)
        self.assertIn("return .single(false)", updated)
        self.assertIn("return .single(true)", updated)
        self.assertEqual(updated, patch.patch_register_text(updated))

    def test_copy_extension_report_contains_required_type1_block_without_raw_material(self):
        patch = load_module("native_push_report", APPLY)
        updated = patch.patch_build_config_text(BUILD_CONFIG_FIXTURE)

        for marker in (
            "=== Native Push APNs Registration ===",
            "NotificationSettingsReadCount: %ld",
            "AuthorizationGrantedCount: %ld",
            "AuthorizationDeniedCount: %ld",
            "RegisterForRemoteNotificationsCount: %ld",
            "InvalidationRegisterCount: %ld",
            "DidRegisterTokenCount: %ld",
            "DidFailTokenCount: %ld",
            "DeviceTokenLength: %@",
            "AuthorizationStatus: %@",
            "LastRegisterFail: %@",
            "=== Native Push Type1 ===",
            "APNsRegistered: %@",
            "Type1EntryCount: %ld",
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
            self.assertIn(marker, updated)

        self.assertEqual(
            updated.count("stringByAppendingString:JerkgramNativePushType1Diagnostics()"),
            2,
        )
        helper = updated[
            updated.index(patch.OBJC_MARKER):
            updated.index("@implementation BuildConfig (JerkgramExtensionDiagnostics)")
        ]
        for forbidden in ("hexString(token)", "p256dh", "canonicalToken", "rawBinding", "api_hash"):
            self.assertNotIn(forbidden, helper)
        self.assertEqual(updated, patch.patch_build_config_text(updated))

    def test_final_verifier_accepts_materialized_fixture_and_real_copy_owner(self):
        patch = load_module("native_push_apply_for_verify", APPLY)
        verifier = load_module("native_push_verify", VERIFY)
        register = patch.patch_register_text(REGISTER_FIXTURE)
        build_config = patch.patch_build_config_text(BUILD_CONFIG_FIXTURE)
        verifier.verify_texts(register, build_config, SETTINGS_FIXTURE)

    def test_installer_keeps_webpush_and_places_type1_verifier_last_before_bazel(self):
        installer_text = INSTALLER.read_text(encoding="utf-8")
        self.assertIn('"verify_jerkgram_webpush_registration_v01.py"', installer_text)
        self.assertIn('"verify_jerkgram_push_binding_bridge_v01.py"', installer_text)
        self.assertIn('"apply_jerkgram_native_push_runtime_probe_v01.py"', installer_text)
        self.assertIn('"verify_jerkgram_native_push_runtime_probe_v01.py"', installer_text)

        installer = load_module("native_push_installer", INSTALLER)
        order = installer.SOURCE_ORDERED
        apply_name = "apply_jerkgram_native_push_runtime_probe_v01.py"
        verify_name = "verify_jerkgram_native_push_runtime_probe_v01.py"

        self.assertLess(order.index("verify_jerkgram_webpush_registration_v01.py"), order.index(apply_name))
        self.assertLess(order.index("verify_jerkgram_push_binding_bridge_v01.py"), order.index(apply_name))
        self.assertEqual(order[-2], apply_name)
        self.assertEqual(order[-1], verify_name)


if __name__ == "__main__":
    unittest.main()
