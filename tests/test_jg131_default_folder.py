import hashlib, json, os, pathlib, shutil, subprocess, tempfile, unittest
ROOT = pathlib.Path(__file__).resolve().parents[2]
TREE = pathlib.Path(os.environ.get('JERKGRAM_DEFAULT_FOLDER_SOURCE', ROOT / 'jerkgram-telegram-builder/work/swiftgram-src'))
SOURCE = TREE / 'submodules/TelegramCore/Sources/TelegramEngine/Peers/ChatListFiltering.swift'
class DefaultFolderPolicy(unittest.TestCase):
    def policy(self):
        source = SOURCE.read_text()
        self.assertTrue('// BEGIN JERKGRAM DEFAULT FOLDER FOUNDATION' in source, 'production policy is missing')
        return source.split('// BEGIN JERKGRAM DEFAULT FOLDER FOUNDATION\n')[1].split('// END JERKGRAM DEFAULT FOLDER FOUNDATION')[0]
    def test_production_policy_exists(self):
        self.policy()
    def test_proposal_lifetime_policy_exists(self):
        self.assertIn("struct JerkgramFolderProposalToken", self.policy())
    def test_interface_footer_has_unique_native_stable_id(self):
        settings = self.read('SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift')
        appearance = settings.split('if page == .appearance {', 1)[1].split('if page == .about {', 1)[0]
        self.assertEqual(appearance.count('.info(1,'), 1)
    def test_startup_policy_exists(self):
        self.assertIn('public static func startupReady', self.policy())
    def read(self, owner):
        return (TREE / 'submodules' / owner).read_text()
    def test_native_stock_sections_remain_exact(self):
        fixtures = pathlib.Path(__file__).parent / 'fixtures/default-folder'
        for item in json.loads((fixtures / 'stock-sections.json').read_text()):
            self.assertIn(item['text'], self.read(item['file']), item['file'])
        helper = self.read('ChatListUI/Sources/TabBarChatListFilterController.swift')
        body = helper.split('    |> distinctUntilChanged', 1)[1].split('// Metadata and unread tuples', 1)[0].rstrip()
        self.assertEqual(hashlib.sha256(body.encode()).hexdigest(), (fixtures / 'unread.sha256').read_text().strip())
    def test_authoritative_cleanup_and_obsolete_transaction_guard(self):
        source = SOURCE.read_text()
        self.assertEqual(source.count('jerkgramPruneDefaultFolderOrder(transaction: transaction, old:'), 3)
        commit = source.split('func _internal_updateJerkgramChatListFilterOrder', 1)[1].split('private func jerkgramPruneDefaultFolderOrder', 1)[0]
        self.assertIn('account.postbox.transaction', commit)
        self.assertIn('proposal.token.matches(lifetime: account.postbox, generation: policy.generation)', commit)
        self.assertIn('proposedGeneration: proposal.token.generation', commit)
        self.assertIn('proposal.allowedIds == allowed', commit)
        self.assertIn('accepted.filter { $0 == 0 || allowed.contains($0) }', commit)
        self.assertNotIn('updateDialogFiltersOrder', commit)
    def test_shared_snapshot_startup_and_both_native_reorders(self):
        root = self.read('ChatListUI/Sources/ChatListController.swift')
        editor = self.read('ChatListUI/Sources/ChatListFilterPresetListController.swift')
        self.assertIn('!strongSelf.initializedFilters && snapshot.startupReady', root)
        self.assertIn('jerkgramReorderProposal = self.jerkgramFilterSnapshot?.proposal', root)
        self.assertIn('reorderProposal = latestSnapshot?.proposal', editor)
        self.assertIn('updatedFilterOrderValue.map(snapshot.normalizedOrder)', editor)
        self.assertIn('reorderProposal == nil, let order = order, order.first != 0', editor)
        for source in (root, editor):
            self.assertIn('updateJerkgramChatListFilterOrder(ids:', source)
            self.assertIn('updateChatListFiltersInteractively {', source)
        fallback = root.split('if !resolvedItems.contains(where:', 1)[1]
        self.assertLess(fallback.index('if snapshot.localActive'), fallback.index('(0 ..< index - 1).reversed()'))
        self.assertIn('combinedView(keys: [preferencesKey, peerKey])', SOURCE.read_text())
    def test_native_production_fixtures(self):
        policy = self.policy()
        swift = shutil.which('swift')
        if not swift:
            self.skipTest('Swift absent on Linux; actual production Foundation fixtures require macOS Swift')
        fixture = (pathlib.Path(__file__).parent / 'fixtures/default-folder/main.swift').read_text()
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / 'main.swift'
            path.write_text('import Foundation\n' + policy + '\n' + fixture)
            subprocess.run([swift, str(path)], check=True)
if __name__ == '__main__': unittest.main()
