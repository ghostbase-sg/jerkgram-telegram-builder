"""Bounded production-source contracts; optional real Swift preference-cache execution."""
from pathlib import Path
import json
import os
import sys
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('JG_PERFORMANCE_SOURCE', ROOT/'work/swiftgram-src'))
sys.path.insert(0, str(ROOT/'scripts'))
import materialize_jg131_performance_followup as stage
OWNERS = list(stage.manifest()['owners'])
ACCOUNT, HISTORY, TIMESTAMP = OWNERS[:3]

class PerformanceFollowupTests(unittest.TestCase):
    def read(self, owner): return (SOURCE / owner).read_text()

    def test_history_preferences_are_read_once_per_map_not_per_message(self):
        text = self.read(HISTORY)
        loop = text.index('    loop: for entry in view.entries {')
        for key in ('jerkgram.Messages.ShowDeleted', 'jerkgram.ProtectedContent.Enabled', 'jerkgram.ProtectedContent.OneTimeSave'):
            self.assertEqual(text.count('forKey: "' + key + '"'), 1)
            self.assertLess(text.index('forKey: "' + key + '"'), loop)
        self.assertNotIn('UserDefaults.standard', text)
        self.assertIn('if !ghostBaseShowDeleted && ghostBaseIsDeleted', text)
        self.assertIn('message.id.peerId.namespace != Namespaces.Peer.SecretChat', text)

    def test_timestamp_uses_registered_cache_key(self):
        key = 'jerkgram.Appearance.MessageSeconds'
        self.assertIn('"' + key + '"', self.read(ACCOUNT))
        text = self.read(TIMESTAMP)
        self.assertNotIn('UserDefaults.standard', text)
        self.assertIn('JerkgramHotSettings.object(', text)
        self.assertIn('withSeconds: ghostBaseMessageSeconds', text)

    def test_only_reviewed_transformations_change_original_source(self):
        before = {n: stage.parent_bytes(n, (SOURCE/n).read_bytes()).decode() for n in OWNERS}
        account = self.read(ACCOUNT).replace('        "jerkgram.Appearance.MessageSeconds",\n', '', 1)
        self.assertEqual(account, before[ACCOUNT], 'unrelated account changes')
        timestamp = self.read(TIMESTAMP).replace('JerkgramHotSettings.object(', 'UserDefaults.standard.object(', 1)
        self.assertEqual(timestamp, before[TIMESTAMP], 'unrelated timestamp changes')
        # History transformation must retain the whole original function outside the bounded block.
        start = '    var count = 0\n'
        end = '        var contentTypeHint: ChatMessageEntryContentType = .generic'
        original = before[HISTORY]
        changed = self.read(HISTORY)
        prefix = original.split(start, 1)[0]
        self.assertTrue(changed.startswith(prefix))
        self.assertEqual(changed.split(end, 1)[1], original.split(end, 1)[1], 'unrelated history body changes')

    @unittest.skipUnless(shutil.which('swiftc'), 'Swift unavailable: cache execution requires macOS CI')
    def test_actual_cache_defaults_toggle_account_projection_and_import_invalidation(self):
        source = self.read(ACCOUNT)
        cache = source.split('public enum JerkgramHotSettings {', 1)[1].split('\npublic final class AccountAuxiliaryMethods', 1)[0]
        fixture = '''import Foundation
public enum JerkgramHotSettings {''' + cache + '''
let key = "jerkgram.Appearance.MessageSeconds"
let defaults = UserDefaults.standard
let old = defaults.object(forKey: key)
defer {
    if let old { defaults.set(old, forKey: key) } else { defaults.removeObject(forKey: key) }
    JerkgramHotSettings.invalidate()
}
defaults.removeObject(forKey: key)
JerkgramHotSettings.invalidate()
precondition((JerkgramHotSettings.object(forKey: key) as? Bool ?? false) == false)
// Normal toggle: write then invalidate, exactly as the settings persistence path does.
defaults.set(true, forKey: key)
JerkgramHotSettings.invalidate()
precondition(JerkgramHotSettings.object(forKey: key) as? Bool == true)
// Account projection/import must not inherit the previous account's cached value.
defaults.set(false, forKey: key)
precondition(JerkgramHotSettings.object(forKey: key) as? Bool == true)
JerkgramHotSettings.invalidate()
precondition(JerkgramHotSettings.object(forKey: key) as? Bool == false)
defaults.set(true, forKey: key)
JerkgramHotSettings.invalidate()
precondition(JerkgramHotSettings.object(forKey: key) as? Bool == true)
print("production cache invalidation PASS; no speed measurement")
'''
        with tempfile.TemporaryDirectory() as directory:
            main = Path(directory) / 'main.swift'
            main.write_text(fixture)
            exe = Path(directory) / 'check'
            subprocess.run(['swiftc', '-warnings-as-errors', str(main), '-o', str(exe)], check=True)
            subprocess.run([str(exe)], check=True)

if __name__ == '__main__': unittest.main()
