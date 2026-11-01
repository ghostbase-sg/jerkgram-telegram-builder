import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(os.environ.get('JERKGRAM_SETTINGS_GLASS_SOURCE', pathlib.Path(__file__).resolve().parents[1] / 'work/swiftgram-src'))
G = ROOT / 'submodules/Display/Source/GhostBaseGlass.swift'
S = ROOT / 'submodules/SettingsUI/Sources/Privacy and Security/RecentSessionScreen.swift'
C = ROOT / 'submodules/SettingsUI/Sources/Privacy and Security/Recent Sessions/RecentSessionsController.swift'
T = ROOT / 'submodules/TelegramPresentationData/Sources/PresentationTheme.swift'

class SettingsGlass(unittest.TestCase):
    def test_production_policy_mapping(self):
        policy = G.read_text().split('// JGC material policy begin')[1].split('// JGC material policy end')[0]
        self.assertIn('optIn && master && enabled && !reduceTransparency', policy)
        self.assertIn('isDark ? 0.34 : 0.26', policy)
        self.assertIn('isDark ? 0.60 : 0.70', policy)
        self.assertNotIn('lowPower', policy)
        self.assertIn('JerkgramSettingsMaterialPolicy.itemAlpha', T.read_text())
    def test_scoped_live_components(self):
        s = S.read_text()
        self.assertIn('settingsGlass: Bool = false', s)
        self.assertIn('jerkgramAcceptsSettingsSurface: Bool { return false }', s)
        self.assertEqual(s.count('if lhs.materialState != rhs.materialState'), 2)
        self.assertIn('self.jerkgramTracksVisualSettings = settingsGlass', s)
        self.assertIn('override func jerkgramSettingsVisualStateUpdated()', s)
        self.assertIn('self.updateComponent(component:', s)
        self.assertEqual(C.read_text().count('settingsGlass: true'), 3)
        self.assertNotIn('NotificationCenter', s)
        self.assertNotIn('UserDefaults', s)
    def test_native_sheet_and_state_preserved(self):
        fixture = json.loads((pathlib.Path(__file__).parent / 'fixtures/settings-glass-expansion/native-contract.json').read_text())
        new = S.read_text()
        for start, end, digest in fixture['sections']:
            self.assertEqual(hashlib.sha256(new.split(start)[1].split(end)[0].encode()).hexdigest(), digest)
        for line in fixture['geometry']:
            self.assertIn(line, new)
    def test_native_policy_fixture(self):
        swift = shutil.which('swift')
        if not swift:
            self.skipTest('Swift unavailable; extracted production fixture requires macOS gate')
        policy = G.read_text().split('// JGC material policy begin')[1].split('// JGC material policy end')[0]
        cases = (pathlib.Path(__file__).parent / 'fixtures/settings-glass-expansion/cases.swift').read_text()
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / 'main.swift'
            p.write_text(policy + cases)
            subprocess.run([swift, str(p)], check=True, capture_output=True, text=True)
