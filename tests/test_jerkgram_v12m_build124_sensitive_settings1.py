from pathlib import Path
import importlib.util
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts/apply_jerkgram_v12m_build124_sensitive_settings1.py"
VERIFY = REPO / "scripts/verify_jerkgram_v12m_build124_sensitive_settings1.py"

FIXTURE = '''// MARK: Jerkgram v1.2L BUILD123_ACCOUNT_SETTINGS_OWNER1
private func jerkgramPersistChangedSettings(
    accountPeerId: Int64,
    previous: GhostBaseSettingsState?,
    current: GhostBaseSettingsState
) {
    let oldValues = previous.map(jerkgramStateValues) ?? [:]
    let newValues = jerkgramStateValues(current)
    let changes = newValues.filter { oldValues[$0.key] != $0.value }
    guard !changes.isEmpty else { return }

    JerkgramSettingsCommitQueue.enqueue {
        let defaults = UserDefaults.standard
        for (key, value) in changes {
            value.write(to: defaults, key: jerkgramScopedSettingsKey(accountPeerId: accountPeerId, key: key))
            // Legacy Telegram and extension consumers use this active-account projection.
            value.write(to: defaults, key: key)
            if key == GhostBaseKey.scheduledSend {
                value.write(to: UserDefaults(suiteName: "group.4a348a9b186b700c.1") ?? defaults, key: key)
            }
        }
    }
}'''


class Build124SensitiveSettingsTests(unittest.TestCase):
    def load_patch(self):
        spec = importlib.util.spec_from_file_location("build124_sensitive_settings", PATCH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_runtime_consumed_keys_project_before_deferred_queue(self):
        module = self.load_patch()
        updated = module.patch_text(FIXTURE)

        self.assertIn("BUILD124_SENSITIVE_SETTINGS_SYNC1", updated)
        self.assertIn("GhostBaseKey.scheduledSend", updated)
        self.assertIn("GhostBaseKey.protectedEnabled", updated)
        self.assertIn("GhostBaseKey.oneTimeSave", updated)

        sync_owner = updated.index("for key in jerkgramSynchronousRuntimeSettingKeys")
        queue_owner = updated.index("JerkgramSettingsCommitQueue.enqueue")
        self.assertLess(sync_owner, queue_owner)

    def test_sync_projection_updates_scoped_and_active_defaults(self):
        module = self.load_patch()
        updated = module.patch_text(FIXTURE)
        before_queue = updated[:updated.index("JerkgramSettingsCommitQueue.enqueue")]

        self.assertIn("jerkgramScopedSettingsKey(accountPeerId: accountPeerId, key: key)", before_queue)
        self.assertIn("value.write(to: defaults, key: key)", before_queue)
        self.assertIn('UserDefaults(suiteName: "group.4a348a9b186b700c.1")', before_queue)

    def test_sensitive_keys_are_removed_from_async_batch(self):
        module = self.load_patch()
        updated = module.patch_text(FIXTURE)

        self.assertIn("let deferredChanges = changes.filter", updated)
        self.assertIn("!jerkgramSynchronousRuntimeSettingKeys.contains($0.key)", updated)
        queue_block = updated[updated.index("JerkgramSettingsCommitQueue.enqueue"):]
        self.assertIn("for (key, value) in deferredChanges", queue_block)
        self.assertNotIn("for (key, value) in changes", queue_block)

    def test_no_forced_disk_synchronize_is_added(self):
        module = self.load_patch()
        updated = module.patch_text(FIXTURE)
        self.assertNotIn(".synchronize()", updated)
        self.assertNotIn("synchronize()", updated)

    def test_unrelated_settings_remain_deferred(self):
        module = self.load_patch()
        updated = module.patch_text(FIXTURE)
        self.assertIn("guard !deferredChanges.isEmpty else { return }", updated)
        self.assertIn("JerkgramSettingsCommitQueue.enqueue", updated)

    def test_patch_is_idempotent(self):
        module = self.load_patch()
        once = module.patch_text(FIXTURE)
        self.assertEqual(once, module.patch_text(once))

    def test_verifier_tracks_canonical_jerkgram_runtime_keys(self):
        source = VERIFY.read_text(encoding="utf-8")
        self.assertIn('"jerkgram.ProtectedContent.Enabled"', source)
        self.assertIn('"jerkgram.ProtectedContent.OneTimeSave"', source)
        self.assertIn('"jerkgram.GhostMode.ScheduledSend"', source)
        self.assertNotIn('"GhostBase.ProtectedContent.Enabled"', source)
        self.assertNotIn('"GhostBase.ProtectedContent.OneTimeSave"', source)
        self.assertNotIn('"GhostBase.GhostMode.ScheduledSend"', source)


if __name__ == "__main__":
    unittest.main()
