"""Focused recovery gates; historical Default Folder gates require their parent view."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
TREE = Path(os.environ.get('JG_BETA2_UI_SOURCE', ROOT.parent / 'jerkgram-next/beta2/recovery/source'))
FIXTURES = ROOT / 'tests/fixtures/beta2_recovery_ui'
BASELINE = json.loads((FIXTURES / 'baseline.json').read_text())
CORE = 'submodules/TelegramCore/Sources/TelegramEngine/Peers/ChatListFiltering.swift'
SETTINGS = 'submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift'
SCREEN = 'submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoScreen.swift'
CONTAINER = 'submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoScreenItemSectionContainerNode.swift'


def body(source, declaration):
    start = source.index(declaration)
    opening = source.index('{', start)
    depth = 1
    cursor = opening + 1
    while depth:
        depth += (source[cursor] == '{') - (source[cursor] == '}')
        cursor += 1
    return source[start:cursor]


def native_source():
    source = (TREE / CORE).read_text()
    foundation = source.split('// BEGIN JERKGRAM DEFAULT FOLDER FOUNDATION\n', 1)[1].split('// END JERKGRAM DEFAULT FOLDER FOUNDATION', 1)[0]
    declarations = ['public struct JerkgramChatListFilterProposal', 'public struct JerkgramChatListFilterSnapshot',
                    'func _internal_updatedJerkgramChatListFilters', 'func _internal_updateJerkgramChatListFilterOrder',
                    'private func jerkgramPruneDefaultFolderOrder']
    return ('import Foundation\n' + (FIXTURES / 'shell.swift').read_text() + '\n' + foundation + '\n'
            + '\n'.join(body(source, item) for item in declarations) + '\n' + (FIXTURES / 'main.swift').read_text())


class Beta2RecoveryUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from jg132_baseline import enabled, source_boundary_view
        cls.current_parent = None
        if enabled():
            context=source_boundary_view(TREE,29)
            cls.current_parent=context.__enter__()
            cls.addClassCleanup(context.__exit__,None,None,None)

    def expected_unchanged(self,owner):
        if self.current_parent is not None:
            return hashlib.sha256((self.current_parent/owner).read_bytes()).hexdigest()
        return BASELINE['unchanged_owners'][owner]

    def test_disabled_policy_covers_all_runtime_boundaries(self):
        source = (TREE / CORE).read_text()
        self.assertTrue('public static let runtimeEnabled = false' in source, 'runtime capability must be disabled')
        self.assertIn('runtimeEnabled && current.0', body(source, 'public static func snapshot'))
        self.assertIn('JerkgramDefaultFolderSettings.runtimeEnabled', body(source, 'public static func effective'))
        self.assertIn('JerkgramDefaultFolderSettings.runtimeEnabled', body(source, 'public static func startupReady'))
        self.assertIn('JerkgramDefaultFolderSettings.runtimeEnabled', body(source, 'public static func proposalIsCurrent'))
        transaction = body(source, 'func _internal_updateJerkgramChatListFilterOrder')
        self.assertLess(transaction.index('guard JerkgramDefaultFolderSettings.runtimeEnabled'), transaction.index('transaction.updatePreferencesEntry'))
        prune = body(source, 'private func jerkgramPruneDefaultFolderOrder')
        self.assertLess(prune.index('guard JerkgramDefaultFolderSettings.runtimeEnabled'), prune.index('transaction.getPreferencesEntry'))

    def test_appearance_control_removed_with_preferences_and_other_pages_retained(self):
        source = (TREE / SETTINGS).read_text()
        appearance = body(source, 'if page == .appearance')
        self.assertNotIn('JerkgramDefaultFolderSettings.preferenceKey', appearance)
        self.assertNotIn('Unlock Default Chat Folder', appearance)
        self.assertNotIn('normal folder reorder', appearance)
        self.assertIn('.info(1, strings.hidePhoneHint)', appearance)
        # Other pages and state persistence stay byte identical, including translations.
        def without_changed_pages(text):
            for page in ('mediaStories', 'appearance'):
                text = text.replace(body(text, 'if page == .' + page), '')
            return text
        self.assertEqual(hashlib.sha256(without_changed_pages(source).encode()).hexdigest(), BASELINE['settings_other_pages_sha256'])

    def test_download_hint_shares_control_section_with_unique_footer_identity(self):
        media = body((TREE / SETTINGS).read_text(), 'if page == .mediaStories')
        self.assertIn('.downloadBoost(0, 5, state.downloadBoost)', media)
        self.assertIn('.info(0, strings.downloadBoostHint)', media)
        infos = re.findall(r'\.info\((\d+),', media)
        self.assertEqual(infos, ['0'])
        self.assertEqual(len(infos), len(set(infos)), 'info stable IDs collide within a section')

    def test_dark_override_is_scoped_and_reconciled(self):
        source = (TREE / SCREEN).read_text()
        self.assertTrue('self.isSettings && sectionId == AnyHashable(SettingsSection.ghostbase) ? 0.44 : nil' in source, 'only main Settings ghostbase receives dark override')
        reconcile = body(source, 'func reconcileJerkgramVisualState')
        self.assertIn('for (sectionId, sectionNode) in self.regularSections', reconcile)
        self.assertIn('darkBackgroundAlpha:', reconcile)
        regular = source.split('for (sectionId, sectionItems) in items {', 1)[1].split('settings.sectionsRegularRemoval', 1)[0]
        self.assertIn('sectionNode.updateJerkgramVisualState(', regular)
        self.assertIn('darkBackgroundAlpha:', regular)
        container = (TREE / CONTAINER).read_text()
        self.assertIn('alpha: isDark ? (self.ghostBaseDarkBackgroundAlpha ?? 0.26) : 0.18', container)
        update = body(container, 'func updateJerkgramVisualState')
        self.assertIn('self.ghostBaseDarkBackgroundAlpha = darkBackgroundAlpha', update)
        self.assertIn('if self.ghostBaseGlassEnabled {', container)
        # Existing material admission and rendering stay intact outside the scoped wiring.
        for owner in ('submodules/Display/Source/GhostBaseGlass.swift',
                      'submodules/Display/Source/ViewController.swift',
                      'submodules/TelegramPresentationData/Sources/PresentationTheme.swift'):
            self.assertEqual(hashlib.sha256((TREE / owner).read_bytes()).hexdigest(), self.expected_unchanged(owner), owner)

    def test_native_folder_consumers_and_storage_stay_exact(self):
        for owner in ('submodules/ChatListUI/Sources/ChatListController.swift',
                      'submodules/ChatListUI/Sources/ChatListFilterPresetListController.swift',
                      'submodules/ChatListUI/Sources/TabBarChatListFilterController.swift',
                      'submodules/TelegramCore/Sources/TelegramEngine/Peers/TelegramEnginePeers.swift',
                      'submodules/TelegramCore/Sources/SyncCore/SyncCore_Namespaces.swift'):
            self.assertEqual(hashlib.sha256((TREE / owner).read_bytes()).hexdigest(), self.expected_unchanged(owner), owner)
        source = (TREE / CORE).read_text()
        for text, key in ((body(source, 'private struct JerkgramDefaultFolderOrder'), 'storage_type_sha256'),
                          (body(source, 'public static func update(accountPeerId:'), 'cache_update_sha256'),
                          (source.split('func _internal_generateNewChatListFilterId', 1)[1], 'native_core_remainder_sha256')):
            expected=BASELINE[key]
            if self.current_parent is not None:
                parent=(self.current_parent/CORE).read_text()
                parts={'storage_type_sha256':lambda:body(parent,'private struct JerkgramDefaultFolderOrder'),
                       'cache_update_sha256':lambda:body(parent,'public static func update(accountPeerId:'),
                       'native_core_remainder_sha256':lambda:parent.split('func _internal_generateNewChatListFilterId',1)[1]}
                expected=hashlib.sha256(parts[key]().encode()).hexdigest()
            self.assertEqual(hashlib.sha256(text.encode()).hexdigest(), expected, key)

    def test_accepted_history_owner_unchanged(self):
        owner = TREE / 'submodules/TelegramCore/Sources/State/JerkgramBotBridgeHistory.swift'
        self.assertEqual(hashlib.sha256(owner.read_bytes()).hexdigest(), '4e50ada693a5f7cae35703d162f65f71b7fd9d5c95c42fc4c918b07b0b1bee16')

    def test_native_policy_snapshot_transaction_and_prune(self):
        swift = shutil.which('swiftc')
        if not swift:
            if os.environ.get('JG_BETA2_UI_REQUIRE_NATIVE') == '1':
                self.fail('Required native recovery UI fixture unavailable: swiftc missing')
            self.skipTest('swiftc missing; native policy fixture remains pending')
        with tempfile.TemporaryDirectory(prefix='beta2-recovery-ui-') as tmp:
            main = Path(tmp) / 'main.swift'
            main.write_text(native_source())
            for mode in ('-Onone', '-O'):
                executable = Path(tmp) / ('fixture' + mode)
                subprocess.run([swift, mode, str(main), '-o', str(executable)], check=True)
                subprocess.run([str(executable)], check=True)


if __name__ == '__main__':
    unittest.main()
