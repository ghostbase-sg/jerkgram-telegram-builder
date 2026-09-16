import importlib.util
from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[1]
COMPAT = REPO / "scripts/apply_jerkgram_v13a0_build139_appdelegate_import_compat.py"
FOUNDATION = REPO / "scripts/apply_jerkgram_v13a_build139_notifications_foundation1.py"
INSTALLER = REPO / "scripts/install_jerkgram_v12w_build133_probe_hook.py"


def load(path: Path, name: str):
    if not path.is_file():
        raise AssertionError(f"missing Build139 patcher: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


APP_FIXTURE = '''import UIKit\nimport SwiftSignalKit\n\nfinal class AppDelegate {\n    func application(_ application: UIApplication, open url: URL, sourceApplication: String?, annotation: Any) -> Bool {\n        self.openUrl(url: url)\n        return true\n    }\n}\n'''


class Build139AppDelegateImportCompatContract(unittest.TestCase):
    def test_materialized_appdelegate_without_foundation_is_normalized_before_notifications_patch(self):
        compat = load(COMPAT, "build139_import_compat")
        foundation = load(FOUNDATION, "build139_notifications_foundation")

        normalized = compat.patch_app_delegate_text(APP_FIXTURE)
        self.assertTrue(normalized.startswith("import UIKit\nimport Foundation\n"))
        self.assertEqual(normalized.count("import Foundation\n"), 1)
        self.assertEqual(compat.patch_app_delegate_text(normalized), normalized)

        patched = foundation.patch_app_delegate_text(normalized)
        self.assertIn("import JerkgramCore\n", patched)
        self.assertIn("handleJerkgramNotificationsAuthorizeUrl", patched)
        self.assertIn("handleJerkgramNotificationsReconcileUrl", patched)

    def test_compat_runs_immediately_before_foundation_patch_in_canonical_chain(self):
        installer = INSTALLER.read_text(encoding="utf-8")
        compat_name = "apply_jerkgram_v13a0_build139_appdelegate_import_compat.py"
        foundation_name = "apply_jerkgram_v13a_build139_notifications_foundation1.py"
        self.assertIn(compat_name, installer)
        self.assertLess(installer.index(compat_name), installer.index(foundation_name))


if __name__ == "__main__":
    unittest.main()
