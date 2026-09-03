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

    def test_patch_disables_both_siri_bindings_without_private_security_apis(self):
        module = self.load(PATCH, "build130_siri_patch")
        result = module.patch_app_delegate(self.app_delegate_fixture())
        self.assertEqual(result.count(module.MARKER), 1)
        self.assertNotIn("import Security", result)
        self.assertNotIn("SecTaskCreateFromSelf", result)
        self.assertNotIn("SecTaskCopyValueForEntitlement", result)
        self.assertNotIn("INPreferences.requestSiriAuthorization", result)
        self.assertNotIn("INPreferences.siriAuthorizationStatus", result)

        request_start = result.index("requestSiriAuthorization: { completion in")
        siri_start = result.index("siriAuthorization: {")
        request = result[request_start:siri_start]
        self.assertIn("completion(false)", request)
        self.assertTrue(request.rstrip().endswith("},"))
        status = result[siri_start:result.index("})", siri_start)]
        self.assertIn("return .denied", status)

    def test_patch_is_idempotent_and_leaves_final_about_owner_untouched(self):
        module = self.load(PATCH, "build130_siri_patch")
        app = module.patch_app_delegate(self.app_delegate_fixture())
        self.assertEqual(app, module.patch_app_delegate(app))
        strings = 'var jerkgramVersion: String { return "Jerkgram" }'
        settings = 'if page == .about { return Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") }'
        self.assertEqual(strings, module.patch_strings(strings))
        self.assertEqual(settings, module.patch_settings(settings))

    def test_source_verifier_rejects_missing_runtime_gate(self):
        verifier = self.load(VERIFY, "build130_siri_verify")
        with self.assertRaises(RuntimeError):
            verifier.verify_app_delegate(self.app_delegate_fixture())

    def test_probe_installer_follows_build129_and_runs_before_bazel(self):
        installer = self.load(INSTALLER, "build130_siri_installer")
        probe = '''python3 ../../scripts/apply_jerkgram_v12r_build129_protected_chat_forward1.py
"$BAZEL_BIN" build //Telegram:Telegram
python3 ../../scripts/verify_jerkgram_v12s_build128_final_ipa.py ghostbase-final/GhostBase.ipa
'''
        patched = installer.patch_probe(probe)
        self.assertEqual(patched, installer.patch_probe(patched))
        self.assertEqual(patched.count(installer.SOURCE_MARKER), 1)
        self.assertEqual(patched.count(installer.FINAL_MARKER), 1)
        self.assertLess(patched.index("build129_protected_chat_forward1.py"), patched.index("build130_siri_failclosed1.py"))
        self.assertLess(patched.index("verify_jerkgram_v12s_build130_siri_failclosed1.py"), patched.index("verify_jerkgram_v12s_build130_app_delegate_parse1.py"))
        self.assertLess(patched.index("verify_jerkgram_v12s_build130_app_delegate_parse1.py"), patched.index('"$BAZEL_BIN" build'))
        self.assertLess(patched.index("verify_jerkgram_v12s_build128_final_ipa.py"), patched.index("jerkgram_finalize_build130_identity.py"))

        legacy = patched.replace("\n" + installer.line("verify_jerkgram_v12s_build130_app_delegate_parse1.py"), "", 1)
        upgraded = installer.patch_probe(legacy)
        self.assertEqual(upgraded.count("verify_jerkgram_v12s_build130_app_delegate_parse1.py"), 1)
        self.assertEqual(upgraded, installer.patch_probe(upgraded))


if __name__ == "__main__":
    unittest.main()
