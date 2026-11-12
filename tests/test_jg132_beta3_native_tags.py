"""Focused native Saved tags integration gates; native module build is separate."""
import os, shutil, subprocess, tempfile
from pathlib import Path
import unittest
BUILDER=Path(__file__).resolve().parents[1]
SOURCE=Path(os.environ.get('JG_BETA3_SOURCE', BUILDER/'work/swiftgram-src'))
BEFORE=Path(os.environ.get('JG_BETA3_BEFORE', SOURCE.parent/'before'))
OWNERS=[
 'ChatPresentationInterfaceState/Sources/ChatPresentationInterfaceState.swift',
 'TelegramUI/Sources/Chat/ChatControllerLoadDisplayNode.swift',
 'TelegramUI/Sources/Chat/ChatControllerNavigationButtonAction.swift',
 'TelegramUI/Sources/Chat/UpdateChatPresentationInterfaceState.swift',
 'TelegramUI/Sources/ChatController.swift',
 'TelegramUI/Sources/ChatControllerNode.swift',
 'TelegramUI/Sources/ChatControllerUpdateSearch.swift',
 'TelegramUI/Sources/ChatHistoryListNode.swift',
 'TelegramUI/Sources/ChatInterfaceStateContextMenus.swift',
 'TelegramUI/Sources/ChatInterfaceStateInputPanels.swift',
 'TelegramUI/Sources/ChatInterfaceTitlePanelNodes.swift',
 'TelegramUI/Sources/ChatSearchTitleAccessoryPanelNode.swift',
 'TelegramUI/Sources/ChatTagSearchInputPanelNode.swift',
 'TelegramUI/Sources/JerkgramSavedTagsController.swift']
class NativeTags(unittest.TestCase):
    def read(self, file): return (SOURCE/'submodules'/file).read_text()
    def test_accepted_index_provider_preserved(self):
        for owner in ['Postbox/Sources/LocalSavedTagsTable.swift', 'TelegramCore/Sources/TelegramEngine/Messages/LocalSavedTagsService.swift', 'TelegramCore/Sources/TelegramEngine/Messages/LocalSavedTagsOperations.swift']:
            self.assertEqual((SOURCE/'submodules'/owner).read_bytes(), (BEFORE/'submodules'/owner).read_bytes(),owner)
    def test_typed_filter(self):
        s=self.read('ChatPresentationInterfaceState/Sources/ChatPresentationInterfaceState.swift')
        self.assertTrue('case localSavedTag(String)' in s)
        self.assertTrue('case cloudReaction(MemoryBuffer)' in s)
    def test_same_history_bubbles(self):
        s=self.read('TelegramUI/Sources/ChatHistoryListNode.swift')
        self.assertIn('updateLocalSavedTag(',s)
        self.assertIn('localSavedTagsHistory',s)
        self.assertIn('loadBoundary(earlier:',s)
    def test_native_strip(self):
        s=self.read('TelegramUI/Sources/ChatSearchTitleAccessoryPanelNode.swift')
        self.assertIn('updateLocalSavedTags(',s)
        self.assertIn('localSavedTagId:',s)
    def test_no_search_chooser_or_pushed_assignment(self):
        s=self.read('TelegramUI/Sources/Chat/ChatControllerNavigationButtonAction.swift')
        self.assertNotIn('pushViewController(jerkgramSavedTagsController',s)
        for p in ['ChatInterfaceStateInputPanels.swift','ChatInterfaceStateContextMenus.swift']:
            self.assertNotIn('pushViewController(jerkgramSavedTagsController', self.read('TelegramUI/Sources/'+p))
    def test_catalogue_sheet_has_no_message_results_or_navigation(self):
        s=self.read('TelegramUI/Sources/JerkgramSavedTagsController.swift').split('// Owned by the existing Saved history node.')[0]
        for token in ('ChatListItem(', 'Show messages', 'navigateToChatController', 'case message', 'makePageProvider'):
            self.assertTrue(token not in s, token)
        self.assertIn('summary.assignedCounts',s)
        self.assertIn('service.set(tagId: id, messageIds: self.selectedIds, assigned:',s)
    def test_cloud_calls_unwrap_only_genuine_buffers(self):
        import re
        for owner in OWNERS:
            s=self.read(owner)
            self.assertFalse(re.search(r'reactionFromMessageTag\(tag: (?:historyFilter|updatedFilter|filter)\.customTag',s),owner)
        s=self.read('TelegramUI/Sources/ChatControllerUpdateSearch.swift')
        self.assertTrue(s.index('localSavedTagId != nil') < s.index('let limit: Int32'))
        self.assertIn('updatedHistoryFilter(nil)',s)
        apply=self.read('TelegramUI/Sources/Chat/ChatControllerLoadDisplayNode.swift')
        self.assertIn('self.jerkgramHistoryFilterRequestGeneration == filterGeneration',apply)
    def test_lifecycle_restore_and_indexed_boundaries(self):
        s=self.read('TelegramUI/Sources/ChatHistoryListNode.swift')
        for token in ('savedUnfilteredAnchor', 'localSavedTagsHistory?.dispose()', 'self.localSavedTagsHistory === local', 'loadBoundary(earlier: true)', 'loadBoundary(earlier: false)'):
            self.assertTrue(token in s,token)
        s=self.read('TelegramUI/Sources/JerkgramSavedTagsController.swift').split('// Owned by the existing Saved history node.')[1]
        for token in ('self.generation == generation', 'self.provider.reset()', 'content.earlier : content.later', 'holeEarlier: false, holeLater: false', 'self.content = content'):
            self.assertTrue(token in s,token)
        self.assertNotIn('searchMessages(',s)
        self.assertNotIn('getHistory(',s)
    def test_native_strip_render_cache_and_localization(self):
        s=self.read('TelegramUI/Sources/ChatSearchTitleAccessoryPanelNode.swift')
        local=s.split('private func updateLocalSavedTags(params: Params) {')[1].split('private func update(params:')[0]
        self.assertLess(local.index('guard self.localRenderGate.update(key)'),local.index('for button in self.localButtons'))
        self.assertIn('self.localRenderGate.invalidate()',s)
        self.assertIn('self.localRevision = catalogue.revision',s)
        history=self.read('TelegramUI/Sources/ChatHistoryListNode.swift')
        self.assertIn('strings.text("Older tagged messages",',history)
        self.assertIn('strings.text("Newer tagged messages",',history)
    def test_fenced_clears_and_synchronous_jump_replay(self):
        state=self.read('TelegramUI/Sources/Chat/UpdateChatPresentationInterfaceState.swift')
        self.assertIn('expectedGeneration: expectedLocalFilterGeneration',state)
        self.assertIn('jerkgramClearingLocalSavedTagsFilter(filter, expectedId: expectedLocalFilterId',state)
        history=self.read('TelegramUI/Sources/ChatHistoryListNode.swift')
        self.assertIn('self.updateLocalSavedTag(nil, cleared: cleared)',history)
        self.assertIn('self.localSavedTagsHistory === local',history)
        self.assertIn('jerkgramResolveLocalSavedTagsNavigation(clearHistory:',history)
    def test_retained_content_observation_and_exact_retry(self):
        owner=self.read('TelegramUI/Sources/JerkgramSavedTagsController.swift')
        history=owner.split('final class JerkgramLocalSavedTagsHistory {')[1]
        self.assertIn('self.context.engine.data.subscribe(TelegramEngine.EngineData.Item.Messages.Messages(ids: ids))',history)
        self.assertNotIn('.postbox',history)
        self.assertIn('self.messageGeneration == messageGeneration',history)
        self.assertIn('self.observedIds == ids',history)
        self.assertIn('self.failedRequest ?? self.unavailableRequest ?? self.lastRequest',history)
        retry=history.split('    func retry() {')[1].split('    func contains(',1)[0]
        self.assertNotIn('provider.reset()',retry)
        self.assertNotIn('cursor: nil',retry)
    def coordinator_fixture_source(self):
        from saved_tags_native import declaration
        service=self.read('TelegramCore/Sources/TelegramEngine/Messages/LocalSavedTagsService.swift')
        engine=self.read('TelegramCore/Sources/TelegramEngine/Data/MessagesData.swift')
        history=self.read('TelegramUI/Sources/JerkgramSavedTagsController.swift')
        fixture=(BUILDER/'tests/fixtures/beta3_native_tags/coordinator-native.swift').read_text()
        content='\n'.join(declaration(service,a) for a in ['public struct LocalSavedTagsContentRow {','public struct LocalSavedTagsContentPage {','public enum LocalSavedTagsPageEvent {'])
        for token,body in [
            ('/* EXACT_ENGINE_MESSAGES_ITEM */',declaration(engine,'public struct Messages: TelegramEngineDataItem, PostboxViewDataItem {')),
            ('/* EXACT_CONTENT_TYPES */',content),
            ('/* EXACT_DELIVERY */',declaration(service,'final class LocalSavedTagsDelivery {')),
            ('/* EXACT_PAGE_PROVIDER */',declaration(service,'public final class LocalSavedTagsPageProvider {')),
            ('/* EXACT_COORDINATOR */',declaration(history,'final class JerkgramLocalSavedTagsHistory {'))]:
            fixture=fixture.replace(token,body)
        return fixture
    def test_full_coordinator_fixture_assembly(self):
        source=self.coordinator_fixture_source()
        self.assertNotIn('/* EXACT_',source)
        from saved_tags_native import declaration
        self.assertIn(declaration(self.read('TelegramUI/Sources/JerkgramSavedTagsController.swift'),'final class JerkgramLocalSavedTagsHistory {'),source)
        self.assertIn('self.observedMessages = messages.filter { ids.contains($0.key) }.mapValues { $0._asMessage() }',source)
        self.assertIn('ordinary unchanged-metadata caption edit stayed stale',source)
        self.assertIn('unavailable older page retry jumped to newest/nil cursor',source)
    def test_actual_full_coordinator_native(self):
        if not shutil.which('xcrun'):
            if os.environ.get('JG_BETA3_REQUIRE_NATIVE') == '1': self.fail('Required full native coordinator gate needs macOS Swift/xcrun')
            self.skipTest('full actual production coordinator execution pending macOS')
        with tempfile.TemporaryDirectory(prefix='beta3-coordinator-native-') as tmp:
            source=Path(tmp)/'main.swift';exe=Path(tmp)/'coordinator'
            source.write_text(self.coordinator_fixture_source())
            for opt in ('-Onone','-O'):
                result=subprocess.run(['xcrun','swiftc','-swift-version','5',opt,str(source),'-o',str(exe)],capture_output=True,text=True,timeout=90)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                result=subprocess.run([str(exe)],capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                self.assertIn('PASS exact full native coordinator',result.stdout)
            # Execute both reported failures as mutations of the full extracted
            # production coordinator; the same fixture must reject each one.
            original=self.coordinator_fixture_source()
            mutations=[
                ('stale-edit', 'self.observedMessages = messages.filter { ids.contains($0.key) }.mapValues { $0._asMessage() }', '// regression: retained message snapshots never refresh', 'ordinary unchanged-metadata caption edit stayed stale'),
                ('newest-retry', 'let request = self.failedRequest ?? self.unavailableRequest ?? self.lastRequest', 'let request = PageRequest(cursor: nil, direction: .earlier)', 'unavailable older page retry jumped to newest/nil cursor')]
            for name,before,after,expected in mutations:
                self.assertIn(before,original)
                source.write_text(original.replace(before,after,1))
                result=subprocess.run(['xcrun','swiftc','-swift-version','5','-Onone',str(source),'-o',str(exe)],capture_output=True,text=True,timeout=90)
                self.assertEqual(result.returncode,0,name+'\n'+result.stderr)
                result=subprocess.run([str(exe)],capture_output=True,text=True,timeout=30)
                self.assertNotEqual(result.returncode,0,name+' mutation survived fixture')
                self.assertIn(expected,result.stdout+result.stderr)

    def test_exact_provider_fixture_assembly(self):
        from saved_tags_core_native import assemble_core
        with tempfile.TemporaryDirectory(prefix='beta3-native-tags-assemble-') as tmp:
            paths=assemble_core(BUILDER,SOURCE,Path(tmp))
            self.assertTrue(all(p.is_file() for p in paths))
            core=(Path(tmp)/'Core.swift').read_text()
            from saved_tags_native import declaration
            service=self.read('TelegramCore/Sources/TelegramEngine/Messages/LocalSavedTagsService.swift')
            self.assertIn(declaration(service,'public final class LocalSavedTagsPageProvider {'),core)
            fixture=(BUILDER/'tests/fixtures/beta3_native_tags/provider-native.swift').read_text()
            self.assertIn('nativeTagsSeen.count == 925',fixture)
    def test_exact_provider_native(self):
        if not shutil.which('xcrun'):
            if os.environ.get('JG_BETA3_REQUIRE_NATIVE') == '1':
                self.fail('Required native beta3 provider gate needs macOS xcrun/Swift')
            self.skipTest('exact production SQLite/provider execution pending macOS')
        from saved_tags_core_native import assemble_core
        from saved_tags_native import run_native
        def assemble_beta3(root, source, folder):
            paths=assemble_core(root,source,folder)
            main=folder/'main.swift'
            main.write_text(main.read_text()+'\n'+(BUILDER/'tests/fixtures/beta3_native_tags/provider-native.swift').read_text())
            return paths
        run_native(BUILDER,SOURCE,assembler=assemble_beta3,expected='PASS beta3 native tags 925 memberships both directions')
    def test_native_filter_and_parser(self):
        if not shutil.which('xcrun'):
            if os.environ.get('JG_BETA3_REQUIRE_NATIVE') == '1':
                self.fail('Required native beta3 tags gate needs macOS xcrun/Swift; portable checks are not native compilation')
            self.skipTest('macOS native filter compilation and Swift parse pending')
        from saved_tags_native import declaration
        actual=declaration(self.read(OWNERS[0]),'    public struct HistoryFilter: Equatable {')
        fixture=(BUILDER/'tests/fixtures/beta3_native_tags/filter-native.swift').read_text()
        with tempfile.TemporaryDirectory(prefix='beta3-native-tags-') as tmp:
            main=Path(tmp)/'main.swift'; exe=Path(tmp)/'filter'
            strip=self.read('TelegramUI/Sources/ChatSearchTitleAccessoryPanelNode.swift')
            gate=declaration(strip,'struct JerkgramLocalSavedTagsRenderKey: Equatable {')+'\n'+declaration(strip,'struct JerkgramLocalSavedTagsRenderGate {')
            history=self.read('TelegramUI/Sources/JerkgramSavedTagsController.swift')
            helpers=declaration(history,'func jerkgramClearingLocalSavedTagsFilter(')+'\n'+declaration(history,'func jerkgramResolveLocalSavedTagsNavigation(')
            main.write_text(fixture.replace('/* EXACT_HISTORY_FILTER */',actual).replace('/* EXACT_RENDER_GATE */',gate).replace('/* EXACT_TRANSITION_HELPERS */',helpers))
            for opt in ('-Onone','-O'):
                result=subprocess.run(['xcrun','swiftc','-swift-version','5',opt,str(main),'-o',str(exe)],capture_output=True,text=True,timeout=90)
                self.assertEqual(result.returncode,0,result.stderr)
                result=subprocess.run([str(exe)],capture_output=True,text=True,timeout=20)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                self.assertIn('PASS actual HistoryFilter',result.stdout)
            for owner in OWNERS:
                result=subprocess.run(['xcrun','swiftc','-frontend','-parse',str(SOURCE/'submodules'/owner)],capture_output=True,text=True,timeout=90)
                self.assertEqual(result.returncode,0,owner+'\n'+result.stderr)
if __name__=='__main__': unittest.main()
