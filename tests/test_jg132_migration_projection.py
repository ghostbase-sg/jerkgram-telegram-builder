"""Fresh hermetic32stage migration proof over genuine pinned Git objects."""
from pathlib import Path
import json,re,shutil,tempfile,unittest
from jg132_migration_fixtures import baseline,GenuinePristineFactory,two_fresh_replays,hashes

SYNC='submodules/TelegramCore/Sources/State/Sync/'
def method(text,name):
    found=re.search(r'^    func '+name+r'\([^\n]*\) \{\n(.*?)^    \}',text,re.M|re.S)
    if not found:raise AssertionError('Missing actual132method '+name)
    return found.group(1)

class Genuine132Migration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='jg132-hermetic-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.first,cls.second=two_fresh_replays(GenuinePristineFactory(),cls.temp.name)
        cls.source=cls.first['source']

    def test_two_fresh32_replays_reverse_and_refuse_corruption(self):
        self.assertEqual(self.first['hashes'],self.second['hashes'])
        self.assertEqual(len(self.first['records']),32)
        self.assertTrue(all(r['exact_reverse_and_corrupt_prewrite'] and r['raw_repeat_refused'] for r in self.first['records']))
        self.assertEqual(baseline.boundary(self.source),32)
        self.assertFalse((self.source/'.git').exists())

    def test_selected_release_metadata_and_removed_owners(self):
        self.assertEqual(json.loads((self.source/'versions.json').read_text())['app'],'13.2')
        for name in ('submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift','submodules/TelegramUI/Sources/CoreListChatHistoryBackend.swift'):
            self.assertFalse((self.source/name).exists())
        declared={n for row in baseline.chain() for n in row['owners']}
        self.assertTrue(self.first['changed']<=declared)

    def test_actual_replay_methods_keep_tag_retention_and_edit_order(self):
        text=(self.source/SYNC/'StateReplay+Messages.swift').read_text()
        for name,hook in [('applyDeleteMessagesWithGlobalIds','_internal_removeLocalSavedTagsGlobalIds'),('applyDeleteMessages','_internal_removeLocalSavedTagsMessages'),('applyUpdateMinAvailableMessage','_internal_removeLocalSavedTagsRange')]:
            body=method(text,name);self.assertIn(hook,body)
            if 'JerkgramRetentionRuntime.shouldCapture' in body:self.assertLess(body.index(hook),body.index('JerkgramRetentionRuntime.shouldCapture'))
        edit=method(text,'applyEditMessage')
        for token in ('updateLocalSavedTagsMetadata','transaction.recordMessageEdit(message)','GhostBaseMessageAttribute'):self.assertIn(token,edit)
        add=method(text,'applyAddMessages')
        self.assertLess(add.index('transaction.addMessages'),add.index('jerkgramIncludeBotMessagePeers'))

    def test_actual_agent_and_retained_keys_remain_disjoint(self):
        agent=(self.source/'submodules/TelegramCore/Sources/TelegramEngine/Agent/TelegramEngineAgent.swift').read_text()
        self.assertEqual(agent.count('ValueBoxKey(length: 1)'),2);self.assertNotIn('removeItemCache',agent)
        retained=(self.source/'submodules/TelegramCore/Sources/State/JerkgramRetainedChat.swift').read_text()
        self.assertIn('ValueBoxKey(length: 8)',retained)
        namespaces=(self.source/'submodules/TelegramCore/Sources/SyncCore/SyncCore_Namespaces.swift').read_text()
        self.assertIn('cachedAgent: Int8 = 63',namespaces);self.assertIn('jerkgramRetainedChatMembers: Int8 = 63',namespaces)

    def test_actual_bot_manager_keeps_native_custom_queue(self):
        manager=(self.source/'submodules/TelegramCore/Sources/State/AccountStateManager.swift').read_text()
        self.assertIn('private var operations_ = StateOperationQueue()',manager)
        self.assertIn('self.addOperation(.custom(self.getNextId(), signal), position: .last)',manager)
        self.assertNotIn('ghostBaseBotShadow',manager)
        self.assertEqual(manager.count('let controller = BotBridgeHistoryController('),1)

    def test_actual_backend_uses_public_factory(self):
        caller=(self.source/'submodules/TelegramUI/Sources/ChatHistoryListNode.swift').read_text()
        self.assertIn('makeCoreListChatHistoryBackend(rotated: rotated, scrollTrace: scrollTrace)',caller)
        self.assertNotIn('return CoreListChatHistoryBackend(',caller);self.assertIn('var useCoreListBackend = false',caller)
        factory=(self.source/'submodules/TelegramUI/Components/Chat/ChatHistoryListViewBackend/Sources/CoreListChatHistoryBackend.swift').read_text()
        self.assertIn('public func makeCoreListChatHistoryBackend',factory)

    def test_independent_guard_corruption_is_refused_without_writes(self):
        row=baseline.chain()[30]
        guards=[g for g in json.loads(baseline.GUARDS.read_text()) if g['stage']==row['stage'] and 'before' in g['timing'] and g['target_path'] not in row['owners']]
        self.assertTrue(guards)
        with baseline.source_boundary_view(self.source,30) as parent,tempfile.TemporaryDirectory() as td:
            root=Path(td)/'source';shutil.copytree(parent,root)
            p=root/guards[0]['target_path'];p.write_bytes(p.read_bytes()+b'\n// corrupt guard\n');before=hashes(root)
            with self.assertRaises(RuntimeError):baseline.apply_stage(root,row['stage'],require_head=False)
            self.assertEqual(hashes(root),before)

if __name__=='__main__':unittest.main()
