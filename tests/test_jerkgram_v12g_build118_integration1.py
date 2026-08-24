import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
OVERLAY = REPO / "scripts/apply_jerkgram_v12g_build118_integration1.py"


SETTINGS_FIXTURE = '''import Foundation
private func ghostBaseBool(_ key: String, defaultValue: Bool) -> Bool { return defaultValue }
struct GhostBaseSettingsState {
    static func load() -> GhostBaseSettingsState { return GhostBaseSettingsState() }
    func save() {}
}
func controller(context: AccountContext) {
    let initialState = GhostBaseSettingsState.load()
    let next = initialState
    next.save()
}
'''

CORE_FIXTURE = '''import Foundation
case let .DeleteMessages(ids):
    let ghostBaseSaveDeleted = (
        UserDefaults.standard.object(
            forKey: "jerkgram.Messages.SaveDeleted"
        ) as? Bool
    ) ?? true
case let .EditMessage(id, message):
    let ghostBaseSaveEditHistory = (
        UserDefaults.standard.object(
            forKey: "jerkgram.Messages.SaveEditHistory"
        ) as? Bool
    ) ?? true
'''


class Build118IntegrationTests(unittest.TestCase):
    def test_account_scope_reaches_settings_and_capture_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            settings = root / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
            core = root / "submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift"
            settings.parent.mkdir(parents=True)
            core.parent.mkdir(parents=True)
            settings.write_text(SETTINGS_FIXTURE)
            core.write_text(CORE_FIXTURE)
            (root / "submodules/SettingsUI/BUILD").write_text('deps = [\n]')
            (root / "submodules/TelegramCore/BUILD").write_text('deps = [\n]')
            env = os.environ.copy()
            env["JERKGRAM_SOURCE_ROOT"] = str(root)
            result = subprocess.run([sys.executable, str(OVERLAY)], cwd=REPO, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            self.assertEqual(result.returncode, 0, result.stdout)
            rendered_settings = settings.read_text()
            rendered_core = core.read_text()
            self.assertIn("load(accountPeerId:", rendered_settings)
            self.assertIn("save(accountPeerId:", rendered_settings)
            self.assertIn("context.account.peerId.toInt64()", rendered_settings)
            self.assertIn("JerkgramRetentionRuntime.shouldCapture", rendered_core)
            self.assertIn("accountPeerId.toInt64()", rendered_core)
            self.assertIn("id.peerId.toInt64()", rendered_core)
            self.assertIn("Namespaces.Peer.SecretChat", rendered_core)
            self.assertIn("JerkgramCaptureRecorder.record", rendered_core)
            self.assertIn("kind: .deletedMessage", rendered_core)
            self.assertIn("kind: .editedMessage", rendered_core)
            self.assertNotIn("let ghostBaseSaveEditHistory = (\n                        UserDefaults.standard", rendered_core)


if __name__ == "__main__":
    unittest.main()
