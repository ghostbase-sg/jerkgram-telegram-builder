import importlib.util
from pathlib import Path
import unittest

REPO = Path(__file__).resolve().parents[1]
PATCH_PATH = REPO / "scripts/apply_jerkgram_build140_download_boost1.py"
INSTALLER = REPO / "scripts/install_jerkgram_v12w_build133_probe_hook.py"


class DownloadBoostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patch = None
        if PATCH_PATH.exists():
            spec = importlib.util.spec_from_file_location("download_boost", PATCH_PATH)
            cls.patch = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cls.patch)

    def test_fetch_patch_preserves_stock_off_and_adds_medium_maximum(self):
        self.assertIsNotNone(self.patch, "download boost patcher is missing")
        source = '''import Foundation\n\nprivate let possiblePartLengths: [Int64] = [1]\n\nif isStory {\n    self.defaultPartSize = 512 * 1024\n} else {\n    self.defaultPartSize = 128 * 1024\n}\nself.cdnPartSize = 128 * 1024\nlet state = FetchingState(\n    maxPendingParts: 6,\n    decryptionState: nil\n)\n'''
        actual = self.patch.patch_fetch_v2(source)
        self.assertIn('jerkgramDownloadPartSize(512 * 1024, fileSize: self.size)', actual)
        self.assertIn('jerkgramDownloadPartSize(128 * 1024, fileSize: self.size)', actual)
        self.assertIn('maxPendingParts: jerkgramDownloadMaxPendingParts(6)', actual)
        self.assertIn('self.cdnPartSize = 128 * 1024', actual)
        self.assertIn('case "medium":\n        return 512 * 1024', actual)
        self.assertIn('case "maximum":\n        return 1024 * 1024', actual)
        self.assertEqual(actual, self.patch.patch_fetch_v2(actual))

    def test_small_files_and_off_mode_keep_stock_contract(self):
        self.assertIsNotNone(self.patch, "download boost patcher is missing")
        helper = self.patch.FETCH_HELPER
        self.assertIn('guard let fileSize, fileSize > 1 * 1024 * 1024 else', helper)
        self.assertIn('return defaultPartSize', helper)
        self.assertIn('default:\n        return defaultValue', helper)

    def test_global_setting_is_not_account_scoped(self):
        self.assertIsNotNone(self.patch, "download boost patcher is missing")
        self.assertEqual(self.patch.KEY, 'jerkgram.global.DownloadBoost')
        self.assertIn('UserDefaults.standard.string(forKey: jerkgramDownloadBoostKey)', self.patch.SETTINGS_HELPER)
        self.assertIn('UserDefaults.standard.set(mode, forKey: jerkgramDownloadBoostKey)', self.patch.DOWNLOAD_MENU_WIRING)
        self.assertNotIn('jerkgramScopedSettingsKey', self.patch.SETTINGS_HELPER)
        self.assertNotIn('jerkgramScopedSettingsKey', self.patch.DOWNLOAD_MENU_WIRING)

    def test_wiring_runs_after_premium_icons_and_before_identity(self):
        installer = INSTALLER.read_text()
        order = (
            'verify_jerkgram_build140_premium_icons1.py',
            'apply_jerkgram_build140_download_boost1.py',
            'verify_jerkgram_build140_download_boost1.py',
            'apply_jerkgram_build140_identity.py',
        )
        for name in order:
            self.assertEqual(installer.count(name), 1, name)
        positions = [installer.index(name) for name in order]
        self.assertEqual(positions, sorted(positions))


if __name__ == "__main__":
    unittest.main()
