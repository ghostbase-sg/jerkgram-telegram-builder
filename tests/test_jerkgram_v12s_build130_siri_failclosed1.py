import importlib.util
from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts" / "apply_jerkgram_v12s_build130_siri_failclosed1.py"
VERIFY = REPO / "scripts" / "verify_jerkgram_v12s_build130_siri_failclosed1.py"
INSTALLER = REPO / "scripts" / "install_jerkgram_v12s_build130_probe_hook.py"


class Build130SiriFailClosedTests(unittest.TestCase):
    def load(self, path, name):
        self.assertTrue(path.is_file(), f"missing Build130 stage: {path.name}")
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module

    @staticmethod
    def app_delegate_fixture():
        return '''import Foundation
import Intents

let bindings = TelegramApplicationBindings(requestSiriAuthorization: { completion in
    if #available(iOS 10, *) {
        INPreferences.requestSiriAuthorization { status in
            if case .authorized = status {
                completion(true)
            } else {
                completion(false)
            }
        }
    } else {
        completion(false)
    }
}, siriAuthorization: {
    if buildConfig.isSiriEnabled {
        if #available(iOS 10, *) {
            switch INPreferences.siriAuthorizationStatus() {
            case .authorized:
                return .allowed
            case .denied, .restricted:
                return .denied
            case .notDetermined:
                return .notDetermined
            @unknown default:
                return .notDetermined
            }
        } else {
            return .denied
        }
    } else {
        return .denied
    }
})
'''

    def test_patch_adds_boolean_entitlement_gate_before_both_siri_apis(self):
        module = self.load(PATCH, "build130_siri_patch")
        result = module.patch_app_delegate(self.app_delegate_fixture())
        self.assertIn("import JerkgramSiriEntitlement", result)
        self.assertEqual(result.count(module.MARKER), 1)
        self.assertIn("return JerkgramHasRuntimeSiriEntitlement()", result)
        self.assertIn("buildConfig.isSiriEnabled && jerkgramHasRuntimeSiriEntitlement()", result)
        self.assertLess(
            result.index("buildConfig.isSiriEnabled && jerkgramHasRuntimeSiriEntitlement()"),
            result.index("INPreferences.requestSiriAuthorization"),
        )
        self.assertLess(
            result.rindex("buildConfig.isSiriEnabled && jerkgramHasRuntimeSiriEntitlement()"),
            result.index("INPreferences.siriAuthorizationStatus()"),
        )
        self.assertIn("completion(false)", result)
        self.assertIn("return .denied", result)
        self.assertIn("            }\n        }, siriAuthorization:", result)
        self.assertTrue(result.rstrip().endswith("            }\n        })"))
        self.assertNotIn("TeamIdentifier", result)
        self.assertNotIn("application-identifier", result)

    def test_bridge_is_security_owned_by_objc_target_and_telegram_ui_dep(self):
        module = self.load(PATCH, "build130_siri_patch")
        self.assertIn("#import <Security/SecTask.h>", module.BRIDGE_IMPLEMENTATION_CONTENT)
        self.assertIn('CFSTR("com.apple.developer.siri")', module.BRIDGE_IMPLEMENTATION_CONTENT)
        self.assertIn("CFGetTypeID(value) == CFBooleanGetTypeID()", module.BRIDGE_IMPLEMENTATION_CONTENT)
        self.assertIn("CFRelease(task)", module.BRIDGE_IMPLEMENTATION_CONTENT)
        self.assertIn('"Security"', module.BRIDGE_BUILD_CONTENT)
        self.assertIn("JerkgramSiriEntitlementSwiftProbe", module.BRIDGE_BUILD_CONTENT)
        self.assertIn("import JerkgramSiriEntitlement", module.BRIDGE_SWIFT_PROBE_CONTENT)
        build = 'swift_library(\n    deps = [\n        "//submodules/BuildConfig:BuildConfig",\n    ],\n)\n'
        patched = module.patch_telegram_ui_build(build)
        self.assertIn('"//submodules/JerkgramSiriEntitlement:JerkgramSiriEntitlement",', patched)
        self.assertEqual(patched, module.patch_telegram_ui_build(patched))

    def test_patch_is_idempotent_and_updates_visible_settings_build(self):
        module = self.load(PATCH, "build130_siri_patch")
        app = module.patch_app_delegate(self.app_delegate_fixture())
        self.assertEqual(app, module.patch_app_delegate(app))
        self.assertFalse(hasattr(module, "patch_settings"))
        self.assertFalse(hasattr(module, "patch_strings"))

    def test_source_verifier_rejects_missing_runtime_gate(self):
        verifier = self.load(VERIFY, "build130_siri_verify")
        with self.assertRaises(RuntimeError):
            verifier.verify_app_delegate(self.app_delegate_fixture())

    def test_probe_installer_follows_build129_and_runs_before_bazel(self):
        installer = self.load(INSTALLER, "build130_siri_installer")
        probe = '''python3 ../../scripts/apply_jerkgram_v12r_build129_protected_chat_forward1.py
"$BAZEL_BIN" build ${BAZEL_EXTRA_ARGS:-} //Telegram:Telegram
python3 ../../scripts/verify_jerkgram_v12s_build128_final_ipa.py ghostbase-final/GhostBase.ipa
'''
        patched = installer.patch_probe(probe)
        self.assertEqual(patched, installer.patch_probe(patched))
        self.assertEqual(patched.count(installer.SOURCE_MARKER), 1)
        self.assertEqual(patched.count(installer.FINAL_MARKER), 1)
        self.assertLess(patched.index("build129_protected_chat_forward1.py"), patched.index("build130_siri_failclosed1.py"))
        self.assertLess(patched.index("verify_jerkgram_v12s_build130_siri_failclosed1.py"), patched.index('"$BAZEL_BIN" build'))
        self.assertLess(patched.index("JerkgramSiriEntitlementSwiftProbe"), patched.index(installer.BAZEL_ANCHOR))
        self.assertLess(patched.index("verify_jerkgram_v12s_build128_final_ipa.py"), patched.index("jerkgram_finalize_build130_identity.py"))


if __name__ == "__main__":
    unittest.main()
