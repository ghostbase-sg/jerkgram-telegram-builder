import importlib.util
from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    path = REPO_ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Build116ExtensionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.overlay = load_script("apply_jerkgram_v12e_build116_extensions1.py")

    def test_buildconfig_owns_bounded_atomic_json_diagnostics(self):
        header, implementation = self.overlay.patch_buildconfig(
            "#import <Foundation/Foundation.h>\n@interface BuildConfig : NSObject\n@end\n",
            "#import <BuildConfig/BuildConfig.h>\n",
        )

        self.assertIn("jerkgramRecordExtensionDiagnostic", header)
        self.assertIn("jerkgramExtensionDiagnosticsReport", header)
        self.assertIn("BUILD116_EXTENSION_DIAGNOSTICS1", implementation)
        self.assertIn("substringToIndex:240", implementation)
        self.assertIn("NSJSONWritingSortedKeys", implementation)
        self.assertIn("writeToURL:fileURL options:NSDataWritingAtomic", implementation)
        self.assertIn("jerkgram-extension-diagnostics", implementation)
        self.assertNotIn("appendData", implementation)

    def test_each_owner_records_selected_group_container_and_root(self):
        source = '''
let appGroupName = jerkgramResolvedApplicationGroupIdentifier(
    fallback: "group.\\(baseAppBundleId)"
)
let maybeAppGroupUrl = FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: appGroupName)
guard let appGroupUrl = maybeAppGroupUrl else {
    return
}
let rootPath = rootPathForBasePath(appGroupUrl.path)
let deviceSpecificEncryptionParameters = BuildConfig.deviceSpecificEncryptionParameters(rootPath, baseAppBundleId: baseAppBundleId)
let accountManager = AccountManager<TelegramAccountManagerTypes>(basePath: rootPath + "/accounts-metadata")
'''
        patched = self.overlay.patch_owner(source, "widget")

        for stage in ("profile", "container", "root", "encryption", "account"):
            self.assertIn('stage: "' + stage + '"', patched)
        self.assertIn('process: "widget"', patched)
        self.assertEqual(patched.count("BUILD116_EXTENSION_STAGE1"), 1)

    def test_broadcast_has_coordination_stage(self):
        source = '''
let appGroupName = jerkgramResolvedApplicationGroupIdentifier(
    fallback: "group.\\(baseAppBundleId)"
)
let maybeAppGroupUrl = FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: appGroupName)
guard let appGroupUrl = maybeAppGroupUrl else { return }
let rootPath = rootPathForBasePath(appGroupUrl.path)
let embeddedBroadcastImplementationTypePath = rootPath + "/broadcast-coordination-type-v2"
'''
        patched = self.overlay.patch_owner(source, "broadcast")
        self.assertIn('stage: "broadcastCoordination"', patched)

    def test_settings_exposes_only_one_copy_action(self):
        settings = '''
import AccountContext

    // MARK: Jerkgram v1.2E BUILD116_SETTINGS_RUNTIME_CLEANUP1
    if page == .debugResearch {
        return []
    }
            switch action {
            case "hiddenGiftsSelf":
                break
            }
'''
        patched = self.overlay.patch_settings(settings)
        self.assertIn("strings.copyExtensionDiagnostics", patched)
        self.assertIn('case "copyExtensionDiagnostics":', patched)
        self.assertIn("BuildConfig.jerkgramExtensionDiagnosticsReport()", patched)
        self.assertNotIn("runtimeLines", patched)


if __name__ == "__main__":
    unittest.main()
