"""Focused portable Task 4 owner/wiring contracts.

Production source/hash contracts work with JG_SAVED_TAGS_SOURCE on a clean
checkout. Historical sibling-snapshot proofs explicitly skip when unavailable;
final staging independently verifies and reverses the exact parents.
These checks do not execute
UIKit, SwiftSignalKit, network loaders, gestures or native Swift compilation.
The app build and device matrix remain release gates.
"""
from pathlib import Path
import hashlib
import json
import os
import re
import unittest
from saved_tags_native import declaration

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT.parent / 'jerkgram-next/beta2/saved-tags'
SOURCE = Path(os.environ.get('JG_SAVED_TAGS_SOURCE', BASE / 'source' if (BASE / 'source').is_dir() else ROOT / 'work/swiftgram-src'))
UI = SOURCE / 'submodules/TelegramUI'
OWNER = 'Sources/JerkgramSavedTagsController.swift'
PANEL = 'Components/Chat/ChatMessageSelectionInputPanelNode/Sources/ChatMessageSelectionInputPanelNode.swift'
OWNERS = {OWNER, PANEL, 'Sources/ChatInterfaceStateContextMenus.swift',
          'Sources/ChatInterfaceStateInputPanels.swift',
          'Sources/Chat/ChatControllerNavigationButtonAction.swift'}


class SavedTagsUIContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.controller = (UI / OWNER).read_text()
        cls.panel = (UI / PANEL).read_text()
        cls.inputs = (UI / 'Sources/ChatInterfaceStateInputPanels.swift').read_text()
        cls.menu = (UI / 'Sources/ChatInterfaceStateContextMenus.swift').read_text()
        cls.nav = (UI / 'Sources/Chat/ChatControllerNavigationButtonAction.swift').read_text()

    def test_results_font_matches_native_chat_list_presentation(self):
        native = (SOURCE / 'submodules/ChatListUI/Sources/ChatListSearchListPaneNode.swift').read_text()
        native_fonts = set(re.findall(r'ChatListPresentationData\(theme: (?:self\.)?presentationData\.theme, fontSize: (?:self\.)?presentationData\.(\w+)', native))
        self.assertTrue(native_fonts, 'No native result presentation reference found')
        local_fonts = re.findall(r'ChatListPresentationData\(theme: presentation\.theme, fontSize: presentation\.(\w+)', self.controller)
        self.assertTrue(local_fonts, 'Local result presentation must use the current presentation data')
        self.assertTrue(set(local_fonts) <= native_fonts, (local_fonts, native_fonts))

    def test_only_declared_ui_owners_changed_against_task4_parent(self):
        before = BASE / 'task4-before'
        if not before.is_dir() or SOURCE.resolve() != (BASE / 'source').resolve():
            self.skipTest('Local partial-snapshot inventory proof unavailable; final staging verifies exact parents separately')
        changed = set()
        for path in SOURCE.rglob('*'):
            if path.is_file():
                old = before / path.relative_to(SOURCE)
                if not old.is_file() or old.read_bytes() != path.read_bytes():
                    changed.add(str(path.relative_to(SOURCE)))
        self.assertEqual(changed, {'submodules/TelegramUI/' + name for name in OWNERS})
        self.assertFalse(any(not (SOURCE / p.relative_to(before)).is_file()
                             for p in before.rglob('*') if p.is_file()))

    def test_accepted_production_store_core_bytes_preserved(self):
        manifest = ROOT / 'tests/fixtures/beta2_saved_tags/ui-production-hashes.json'
        proof = json.loads(manifest.read_text())
        self.assertEqual(proof['upstream'], '279f89e4d4f63f17227bf877dc3d8990f22ecd58')
        self.assertEqual(len(proof['files']), 7)
        for name, digest in proof['files'].items():
            self.assertTrue(name.startswith('submodules/'))
            self.assertEqual(hashlib.sha256((SOURCE / name).read_bytes()).hexdigest(), digest, name)
        self.assertNotIn('setMessageReactions', self.controller)
        self.assertNotIn('EngineMemoryBuffer', self.controller)
        for forbidden in ('UserDefaults', 'isPremium', 'searchMessages(', 'getMessagesHistory', 'Timer(', 'DispatchQueue.main.sync'):
            self.assertNotIn(forbidden, self.controller)

    def test_existing_native_selection_and_cloud_reaction_actions_preserved(self):
        before = BASE / 'task4-before/submodules/TelegramUI' / PANEL
        if not before.exists():
            self.skipTest('Local historical panel proof unavailable; final staging verifies exact parents separately')
        parent = before.read_text()
        for anchor in ('private func updateActions()', '@objc private func tagButtonPressed()',
                       '@objc private func shareButtonPressed()', '@objc private func forwardButtonPressed()',
                       '@objc private func deleteButtonPressed()', '@objc private func reportButtonPressed()'):
            self.assertEqual(declaration(parent, anchor), declaration(self.panel, anchor), anchor)

    def test_missing_upstream_navigation_owner_has_exact_pinned_parent(self):
        extra = BASE / 'task-4-extra-parents'
        if not (extra / 'PROVENANCE.json').is_file():
            self.skipTest('Local exact extra-parent proof unavailable; final staging verifies/reverses that pinned parent separately')
        for row in json.loads((extra / 'PROVENANCE.json').read_text()):
            data = (extra / row['path']).read_bytes()
            self.assertEqual(row['upstream'], '279f89e4d4f63f17227bf877dc3d8990f22ecd58')
            self.assertEqual(hashlib.sha256(data).hexdigest(), row['sha256'])
            self.assertEqual(hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest(), row['git_blob_sha1'])
            self.assertNotEqual(data, (SOURCE / row['path']).read_bytes())
        self.assertFalse((BASE / 'task4-before/submodules/TelegramUI'/OWNER).exists())

    def test_discovery_empty_nonpremium_and_original_search_choice(self):
        search = self.nav.split('        case .search:\n', 1)[1].split('        case .dismiss:', 1)[0]
        self.assertIn('self.chatLocation.peerId == self.context.account.peerId', search)
        self.assertIn('ActionSheetButtonItem(title: strings.title', search)
        self.assertEqual(search.count('beginMessageSearch(.everything, "")'), 2)
        for gate in ('isPremium', 'hasSearchTags', 'hasSavedChats', '.isEmpty'):
            self.assertNotIn(gate, search)
        self.assertIn('add("create"', self.controller)
        self.assertIn('else if self.tags.isEmpty', self.controller)

    def test_exact_current_ids_entire_batch_and_one_aggregate_summary(self):
        press = declaration(self.panel, '@objc private func localTagsButtonPressed()')
        self.assertIn('self.localTagsAction?(Array(self.selectedMessages))', press)
        self.assertNotIn('prefix(', press)
        self.assertEqual(self.inputs.count('configureJerkgramLocalTagsPanel('), 5) # declaration + four reuse/new paths
        self.assertIn('selectionState.selectedIds', self.inputs)
        self.assertIn('selectionState.map { Array($0.selectedIds) }', self.menu)
        self.assertIn('selectAll ? messages.map { $0.id } : [message.id]', self.menu)
        self.assertEqual(self.controller.count('service.selectionSummary(messageIds: self.selectedIds)'), 1)
        self.assertIn('self.selectedIds.count <= 1000', self.controller)
        self.assertNotIn('service.tags(messageId:', self.controller)
        self.assertNotIn('prefix(1000)', self.controller)
        self.assertIn('assigned: true', self.controller)
        self.assertIn('assigned: false', self.controller)
        self.assertIn('summary.assignedCounts[tag.id] ?? 0', self.controller)
        self.assertIn('count == summary.selectedCount ? "✓" : "−"', self.controller)

    def test_provider_uses_outer_cursors_and_replaces_bounded_windows(self):
        self.assertIn('let cursor = self.content?.earlier', self.controller)
        self.assertIn('let cursor = self.content?.later', self.controller)
        self.assertNotIn('content.page.earlier', self.controller)
        self.assertNotIn('content.page.later', self.controller)
        self.assertNotIn('LocalSavedTagsCursor(', self.controller)
        self.assertIn('self.content = content', self.controller)
        self.assertIn('self.rowRequests = self.rowRequests.filter { retainedIds.contains($0.key) }', self.controller)
        self.assertIn('for row in content.rows { self.rowRequests[row.entry.id] = request }', self.controller)
        self.assertIn('self.request(Request(cursor: nil, direction: .earlier), mayRestart: false)', self.controller)
        self.assertNotIn('self.content.append', self.controller)
        self.assertNotIn('prefetch(', self.controller)
        # Explicit actions are the only older/newer triggers; scrolling has none.
        self.assertNotIn('visibleBottomContentOffset', self.controller)
        self.assertNotIn('displayedItemRangeChanged', self.controller)

    def test_main_queue_fences_and_lifecycle_disposal(self):
        request = declaration(self.controller, 'private func request(')
        main = request.index('|> deliverOnMainQueue')
        for guard in ('self.generation == generation', 'self.filterGeneration == filterGeneration',
                      'self.requestGeneration == requestGeneration', 'self.selectedTag == tag'):
            self.assertGreater(request.index(guard), main)
        self.assertGreater(request.index('self.content = content'), request.index('self.selectedTag == tag'))
        stop = declaration(self.controller, 'func stop()')
        for owner in ('accounts', 'catalogueSubscription', 'summarySubscription', 'pageSubscription', 'mutationSubscription', 'navigationSubscription'):
            self.assertIn(f'self.{owner}.set(nil)', stop)
        for statement in ('self.provider?.dispose()', 'self.service?.dispose()', 'self.rowRequests.removeAll()'):
            self.assertIn(statement, stop)
        self.assertIn('override func viewWillDisappear', self.controller)
        self.assertIn('primary.account.id == self.context.account.id', self.controller)
        self.assertIn('primary.account.testingEnvironment == self.context.account.testingEnvironment', self.controller)
        self.assertIn('self.summaryGeneration == summaryGeneration', self.controller)
        self.assertIn('self.revision != catalogue.revision', self.controller)

    def test_unavailable_identity_exact_retry_removal_and_saved_navigation(self):
        self.assertIn('add("message:\\(id)"', self.controller)
        self.assertIn('add("unavailable:\\(id)"', self.controller)
        self.assertIn('if let request = self.rowRequests[id]', self.controller)
        self.assertIn('self?.request(request)', self.controller)
        self.assertIn('service.remove(tagId: tag, entries: [row.entry])', self.controller)
        opened = declaration(self.controller, 'func open(')
        self.assertIn('chatLocation: .peer(peer)', opened)
        self.assertIn('TelegramEngine.EngineData.Item.Peer.Peer(id: self.context.account.peerId)', opened)
        self.assertIn('peer.id == self.context.account.peerId', opened)
        self.assertGreater(opened.index('self.navigationGeneration == navigationGeneration'), opened.index('|> deliverOnMainQueue'))
        self.assertIn('subject: .message(id: .id(id)', opened)
        self.assertNotIn('forwardInfo', opened)
        self.assertIn('return ChatListItem(', self.controller)
        self.assertNotIn('Message(stableId:', self.controller)

    def test_crud_filter_delete_localization_and_entry_equality(self):
        for method in ('create', 'rename', 'delete'):
            self.assertIn(f'service.{method}(', self.controller)
        self.assertIn('if self.selectedTag == id { self.selectedTag = nil; self.replaceFilter() }', self.controller)
        self.assertIn('!catalogue.tags.contains(where: { $0.id == tag })', self.controller)
        for text in ('No cloud sync', 'NOT included in current Jerkgram backups', 'reinstalling',
                     'НЕ входят в текущие резервные копии', 'переустановке', 'Text search within a local tag is unavailable',
                     'по тексту внутри локального тега недоступен'):
            self.assertIn(text, self.controller)
        for error in ('invalidName', 'duplicateName', 'invalidTag', 'tagNotFound', 'invalidMessage', 'wrongAccount',
                      'tagLimit', 'messageTagLimit', 'membershipLimit', 'batchLimit', 'invalidPage', 'corruptStore', 'unavailable'):
            self.assertIn('.' + error, declaration(self.controller, 'func error('))
        equality = declaration(self.controller, 'static func == (lhs: Self, rhs: Self)')
        for field in ('stableId', 'index', 'section', 'kind', 'title', 'value', 'action', 'message'):
            self.assertIn('lhs.' + field, equality)
        # Shared chat state has no new fields, copies, or equality branches.
        before = BASE / 'task4-before/submodules/ChatPresentationInterfaceState/Sources/ChatPresentationInterfaceState.swift'
        if before.exists():
            self.assertEqual(before.read_bytes(), (SOURCE / before.relative_to(BASE / 'task4-before')).read_bytes())


if __name__ == '__main__':
    unittest.main(verbosity=2)
