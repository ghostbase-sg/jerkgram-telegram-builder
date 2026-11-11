"""Hub source contracts plus extracted production Foundation/lifecycle fixture.

The fixture runs only on macOS. Source checks are useful on Linux but do not
establish UIKit navigation, rendered glyph shape, or device behavior.
"""
import hashlib
import json
import os
import platform
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TREE = Path(os.environ.get('JG_LOCAL_PREMIUM_SOURCE', ROOT.parent / 'jerkgram-next/beta2/local-premium/source'))
FIXTURES = ROOT / 'tests/fixtures/local_premium'
BASELINE = json.loads((FIXTURES / 'baseline.json').read_text())
SETTINGS = 'submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift'
STRINGS = 'submodules/TelegramPresentationData/Sources/JerkgramStrings.swift'


def body(source, declaration):
    start = source.index(declaration)
    opening = source.index('{', start)
    depth, cursor = 1, opening + 1
    while depth:
        depth += (source[cursor] == '{') - (source[cursor] == '}')
        cursor += 1
    return source[start:cursor]


class LocalPremiumContracts(unittest.TestCase):
    def setUp(self):
        self.source = (TREE / SETTINGS).read_text()

    def test_reachable_home_sibling_and_native_push(self):
        home = body(self.source, 'if page == .home')
        self.assertIn('.disclosure(2, 2, strings.localPremium, "Item List/Icons/Premium", .localPremium)', home)
        self.assertLess(home.index('strings.dataAndBackup'), home.index('strings.localPremium'))
        pages = body(self.source, 'private enum GhostBaseSettingsPage:')
        self.assertIn('case localPremium', pages)
        self.assertIn('return strings.localPremium', pages)
        dispatch = self.source.split('}, openPage: { selectedPage in', 1)[1].split('}, openDownloadBoost:', 1)[0]
        self.assertIn('pushController?(', dispatch)
        self.assertIn('page: selectedPage', dispatch)
        self.assertNotIn('present(', dispatch)

    def test_exact_native_premium_resource_and_no_new_renderer(self):
        icon = body(self.source, 'private func jerkgramSettingsMenuIcon(')
        self.assertIn('case "Item List/Icons/Premium":\n        return PresentationResourcesSettings.premium', icon)
        self.assertEqual(icon.count('renderSettingsIcon('), 1)
        self.assertNotIn('systemName:', icon)

    def test_groups_controls_ids_and_truthful_footer(self):
        self.assertIn('if page == .localPremium', self.source, 'Local Premium page missing')
        hub = body(self.source, 'if page == .localPremium')
        for row in ('.header(0, strings.appearance)', '.header(1, strings.localPremiumMedia)',
                    '.header(2, strings.messages)', '.downloadBoost(1, 1, state.downloadBoost)',
                    '.info(1, strings.downloadBoostHint)', 'JerkgramAppIconAccess.unlockEnabled',
                    'JerkgramSponsoredContentPolicy.preferenceKey', 'JerkgramTranslationSettings.preferenceKey',
                    'strings.translationNeedsWork', '.info(2, strings.localPremiumScopeHint)'):
            self.assertIn(row, hub)
        self.assertNotIn('DefaultFolder', hub)
        self.assertNotIn('isPremium', hub)
        infos = re.findall(r'\.info\((\d+),', hub)
        self.assertEqual(len(infos), len(set(infos)))
        ids = []
        for kind, section, index in re.findall(r'\.(header|toggle|downloadBoost|info)\(\s*(\d+)(?:,\s*(\d+))?', hub):
            ids.append(int(section) * 1000 + (int(index) if index else 999 if kind == 'info' else 0))
        self.assertEqual(len(ids), len(set(ids)), ids)

    def test_aliases_refresh_on_appearance_without_writes_or_global_subscription(self):
        owner = body(self.source, 'private final class JerkgramDiagnosticSettingsController:')
        self.assertIn('var refreshSettingsOnAppearance: (() -> Void)?', owner)
        self.assertIn('self.refreshSettingsOnAppearance?()', body(owner, 'override func viewWillAppear'))
        page = body(self.source, 'private func ghostBaseSettingsPageController(')
        self.assertIn('controller.refreshSettingsOnAppearance = reloadSettings', page)
        reload = body(page, 'let reloadSettings: () -> Void =')
        self.assertIn('GhostBaseSettingsState.load(accountPeerId: accountPeerId)', reload)
        self.assertIn('stateValue.modify { _ in refreshed }', reload)
        self.assertIn('statePromise.set(refreshed)', reload)
        for forbidden in ('UserDefaults.standard.set', 'jerkgramPersistChangedSettings', 'NotificationCenter', 'Timer', 'save('):
            self.assertNotIn(forbidden, reload)
        for page_name, value in (('home', 'state.removeSponsored'), ('appearance', 'JerkgramAppIconAccess.unlockEnabled'),
                                 ('mediaStories', 'state.downloadBoost'), ('messages', 'state.enhancedTranslation')):
            self.assertIn(value, body(self.source, 'if page == .' + page_name))

    def test_persistence_and_consumers_unchanged(self):
        digest = lambda text: hashlib.sha256(text.encode()).hexdigest()
        for declaration, expected in BASELINE['blocks'].items():
            self.assertEqual(digest(body(self.source, declaration)), expected, declaration)
        setters = self.source.split('updateBool: { key, value in', 1)[1].split('}, openPage:', 1)[0]
        self.assertEqual(digest(setters), BASELINE['setters'])
        for owner, expected in BASELINE['unchanged_owners'].items():
            self.assertEqual(hashlib.sha256((TREE / owner).read_bytes()).hexdigest(), expected, owner)

    def test_ru_en_and_translation_status_in_both_entry_points(self):
        strings = (TREE / STRINGS).read_text()
        for text in ('Локальный Premium', 'Local Premium', 'Требует доработки', 'Needs work',
                     'Медиа', 'Media', 'не предоставляют Telegram Premium', 'do not grant Telegram Premium'):
            self.assertIn(text, strings)
        self.assertIn('strings.translationNeedsWork', body(self.source, 'if page == .messages'))

    def test_native_back_navigation_state_and_scope(self):
        from local_premium_fixture import native_source
        extracted = native_source(TREE)
        self.assertIn('self.refreshSettingsOnAppearance?()', extracted)
        if platform.system() != 'Darwin' or not shutil.which('swiftc'):
            if os.environ.get('JG_LOCAL_PREMIUM_REQUIRE_NATIVE') == '1':
                self.fail('Local Premium native fixture requires macOS / Apple Foundation and Swift')
            self.skipTest('macOS / Apple Foundation and Swift unavailable; extraction succeeds, native execution pending')
        with tempfile.TemporaryDirectory(prefix='jg-local-premium-native-') as directory:
            main = Path(directory) / 'main.swift'
            main.write_text(extracted)
            for mode in ('-Onone', '-O'):
                binary = Path(directory) / ('fixture' + mode)
                subprocess.run(['swiftc', mode, str(main), '-o', str(binary)], check=True)
                subprocess.run([str(binary)], check=True, env=dict(os.environ, CFFIXED_USER_HOME=directory))


if __name__ == '__main__':
    unittest.main()
