import importlib.util
from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts" / "apply_jerkgram_v12s_build130_siri_failclosed1.py"
VERIFY = REPO / "scripts" / "verify_jerkgram_v12s_build130_siri_failclosed1.py"
INSTALLER = REPO / "scripts" / "install_jerkgram_v12s_build130_probe_hook.py"


class Build130SiriFailClosedTests(unittest.TestCase):
    def load(self, path, name):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module

    @staticmethod
    def app_delegate_fixture():
        return '''import Intents
let bindings = TelegramApplicationBindings(requestSiriAuthorization: { completion in
    if #available(iOS 10, *) {
        INPreferences.requestSiriAuthorization { _ in completion(false) }
    } else { completion(false) }
}, siriAuthorization: {
    if buildConfig.isSiriEnabled {
        if #available(iOS 10, *) { return .notDetermined }
    }
    return .denied
})
'''

    def test_patch_removes_all_siri_api_reachability(self):
        patch = self.load(PATCH, "build130_patch")
        verify = self.load(VERIFY, "build130_verify")
        result = patch.patch_app_delegate(self.app_delegate_fixture())
        verify.verify_app_delegate(result)
        self.assertEqual(result, patch.patch_app_delegate(result))
        request = verify.balanced_region(result, "requestSiriAuthorization: { completion in")
        status = verify.balanced_region(result, "siriAuthorization: {")
        self.assertIn("completion(false)", request)
        self.assertIn("return .denied", status)
        self.assertNotIn("INPreferences", request + status)
        self.assertNotIn("buildConfig.isSiriEnabled", request + status)
        self.assertNotIn("Security", result)
        self.assertNotIn("SecTask", result)

    def test_installer_removes_obsolete_bridge_compile_probe(self):
        installer = self.load(INSTALLER, "build130_installer")
        probe = '''python3 ../../scripts/apply_jerkgram_v12r_build129_protected_chat_forward1.py
"$BAZEL_BIN" build ${BAZEL_EXTRA_ARGS:-} //Telegram:Telegram
python3 ../../scripts/verify_jerkgram_v12s_build128_final_ipa.py ghostbase-final/GhostBase.ipa
'''
        patched = installer.patch_probe(probe)
        self.assertEqual(patched, installer.patch_probe(patched))
        self.assertIn("verify_jerkgram_v12s_build130_siri_failclosed1.py", patched)
        self.assertNotIn("JerkgramSiriEntitlementSwiftProbe", patched)


if __name__ == "__main__":
    unittest.main()
