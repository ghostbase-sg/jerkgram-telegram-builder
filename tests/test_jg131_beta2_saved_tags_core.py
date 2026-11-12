"""Core integration contracts; native fixture executes exact semantic helpers.

Portable checks do not claim Swift compilation, Signal queue/network delivery,
UIKit behavior, or SQLite persistence. Those remain the explicit native gate.
"""
from pathlib import Path
import hashlib, os, shutil, sys, tempfile, unittest
from saved_tags_native import declaration
from test_jg131_botbridge1_history import is_migrated_132, assert_migrated_owner, migrated_parent_text
ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('JG_SAVED_TAGS_SOURCE', ROOT.parent/'jerkgram-next/beta2/saved-tags/source' if (ROOT.parent/'jerkgram-next/beta2/saved-tags/source').is_dir() else ROOT/'work/swiftgram-src'))
CORE = SOURCE/'submodules/TelegramCore/Sources'
class CoreContracts(unittest.TestCase):
    def test_store_is_frozen(self):
        for name, digest in [('LocalSavedTagsTable.swift','4281a7927d2cc8d345e9eb34ecbbce89f0cb1a8afc05922568ccbaadf4b66f91'),('Postbox.swift','47cfba511a142f076bb207bddc02475551b7f773ea980b3aee00708cfbc38cd8')]:
            if name == 'Postbox.swift' and is_migrated_132(SOURCE): assert_migrated_owner(self,SOURCE,'submodules/Postbox/Sources/Postbox.swift')
            else: self.assertEqual(hashlib.sha256((SOURCE/'submodules/Postbox/Sources'/name).read_bytes()).hexdigest(),digest)
    def test_semantic_hooks_precede_retention_and_use_raw_global_ids(self):
        if is_migrated_132(SOURCE):
            body=(CORE/'State/Sync/StateReplay+Messages.swift').read_text()
            for anchor,call in [('func applyDeleteMessagesWithGlobalIds(', '_internal_removeLocalSavedTagsGlobalIds(transaction: transaction, ids: ids)'),('func applyDeleteMessages(', '_internal_removeLocalSavedTagsMessages(transaction: transaction, ids: ids)')]:
                section=declaration(body,anchor)
                self.assertIn(call,section)
                self.assertLess(section.index(call),section.index('let ghostBase'))
            section=declaration(body,'func applyUpdateMinAvailableMessage(')
            self.assertIn('_internal_removeLocalSavedTagsRange',section)
            self.assertLess(section.index('_internal_removeLocalSavedTagsRange'),section.index('transaction.deleteMessagesInRange'))
            return
        body=(CORE/'State/AccountStateManagementUtils.swift').read_text()
        for case, call in [('DeleteMessagesWithGlobalIds(ids)', '_internal_removeLocalSavedTagsGlobalIds(transaction: transaction, ids: ids)'), ('DeleteMessages(ids)', '_internal_removeLocalSavedTagsMessages(transaction: transaction, ids: ids)')]:
            section=body.split('case let .'+case+':')[-1].split('case let .')[0]
            self.assertIn(call,section)
            self.assertLess(section.index(call),section.index('let ghostBase'))
        section=body.split('case let .UpdateMinAvailableMessage(id):')[-1].split('case let .')[0]
        self.assertIn('_internal_removeLocalSavedTagsRange',section)
    def test_shared_clear_covers_nil_thread_and_inclusive_ranges(self):
        body=(CORE/'TelegramEngine/Messages/DeleteMessages.swift').read_text()
        self.assertIn('_internal_removeLocalSavedTagsMessages(transaction: transaction, ids: ids)',declaration(body,'public func _internal_deleteMessages('))
        for name in ['_internal_clearHistory(', '_internal_clearHistoryInRange(']:
            self.assertIn('_internal_removeLocalSavedTagsRange',declaration(body,'func '+name))
    def test_facade_has_bounded_loader_and_real_metadata(self):
        path=CORE/'TelegramEngine/Messages/LocalSavedTagsService.swift'
        self.assertTrue(path.is_file(),'Core facade missing')
        body=path.read_text()
        self.assertIn('guard !missing.isEmpty',body)
        operations=(CORE/'TelegramEngine/Messages/LocalSavedTagsOperations.swift').read_text()
        self.assertIn('messageIds.count <= 1000',operations)
        self.assertIn('timestamp: message.timestamp, threadId: message.threadId',operations)
        self.assertIn('limit: 45',operations)
        self.assertIn('cursor?.revision == page.revision',operations)
        self.assertIn('while self.windows.count > 3',body)
        self.assertIn('account.testingEnvironment',body)
        self.assertIn('account.id',body)
        self.assertIn('localSavedTagsRevisionKey()',body)
        for forbidden in ['updateMessageReactions','setMessageReactions','searchMessages','getMessagesHistoryViewState','Timer(']:
            self.assertNotIn(forbidden,body)
    def test_delivery_and_invalidation_share_serial_domain(self):
        service=(CORE/'TelegramEngine/Messages/LocalSavedTagsService.swift').read_text()
        self.assertIn('final class LocalSavedTagsDelivery',service)
        self.assertIn('DispatchSpecificKey',service)
        self.assertIn('self.delivery.async',declaration(service,'fileprivate func bind<T>'))
        self.assertIn('self.delivery.sync',declaration(service,'public func dispose()'))
        provider=declaration(service,'public final class LocalSavedTagsPageProvider {')
        self.assertNotIn('NSRecursiveLock',provider)
        for anchor in ['public func reset()', 'public func dispose()', 'public func request(']:
            self.assertIn('self.service.delivery.sync',declaration(provider,anchor))
    def test_exact_core_native_assembly(self):
        from saved_tags_core_native import assemble_core
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            paths=assemble_core(ROOT,SOURCE,folder)
            self.assertTrue(all(p.is_file() for p in paths))
            core=(folder/'Core.swift').read_text()
            service=(CORE/'TelegramEngine/Messages/LocalSavedTagsService.swift').read_text()
            for anchor in ['final class LocalSavedTagsDelivery {', 'fileprivate func bind<T>', 'public func dispose()', 'public final class LocalSavedTagsPageProvider {']:
                self.assertIn(declaration(service,anchor),core)
            self.assertNotIn('/* EXACT_',core)
            self.assertIn('SQLiteFixtureValueBox', (folder/'main.swift').read_text())
    def test_retention_and_history_bodies_preserved(self):
        if is_migrated_132(SOURCE):
            name='submodules/TelegramCore/Sources/State/Sync/StateReplay+Messages.swift'
            current=(SOURCE/name).read_text(); before=migrated_parent_text(SOURCE,name,32)
            for anchor in ['func applyDeleteMessagesWithGlobalIds(', 'func applyDeleteMessages(']:
                old=declaration(before,anchor); new=declaration(current,anchor)
                new='\n'.join(line for line in new.split('\n') if '_internal_removeLocalSavedTags' not in line and 'localSavedTagsAlreadyRemoved:' not in line)
                self.assertEqual(old,new)
            return
        current=(CORE/'State/AccountStateManagementUtils.swift').read_text()
        before_path=Path(os.environ.get('JG_SAVED_TAGS_BEFORE',SOURCE.parent/'before'))/'submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift'
        if not before_path.is_file(): self.skipTest('Historical parent comparison needs JG_SAVED_TAGS_BEFORE; local staged proof recorded separately')
        before=before_path.read_text()
        for name in ['DeleteMessagesWithGlobalIds(ids)', 'DeleteMessages(ids)']:
            old=before.split('case let .'+name+':')[-1].split('case let .')[0]
            new=current.split('case let .'+name+':')[-1].split('case let .')[0]
            new='\n'.join(line for line in new.split('\n') if '_internal_removeLocalSavedTags' not in line and 'localSavedTagsAlreadyRemoved:' not in line)
            self.assertEqual(old,new)
    def test_author_purge_shipped_scope(self):
        interaction=(CORE/'TelegramEngine/Messages/DeleteMessagesInteractively.swift').read_text()
        self.assertIn('let inputChannel = apiInputChannel(peer)',interaction)
        menu=(SOURCE/'submodules/TelegramUI/Sources/Chat/ChatControllerContextMenu.swift')
        # Exact current menu owner is retained in source; no guessed self purge.
        candidates=list((SOURCE/'submodules/TelegramUI/Sources').rglob('*ContextMenus.swift'))
        self.assertTrue(candidates)
        body=''.join(p.read_text() for p in candidates)
        self.assertIn('message.id.peerId.isReplies',body)
        self.assertIn('blockMessageAuthor',body)
class CoreNative(unittest.TestCase):
    def test_exact_core_sqlite_and_provider(self):
        if not shutil.which('swiftc') or not shutil.which('xcrun'):
            if '--require-native' in sys.argv or os.environ.get('JG_SAVED_TAGS_REQUIRE_NATIVE') == '1':
                self.fail('Required native Core gate needs macOS Swift/Clang/xcrun')
            self.skipTest('Native Core SQLite/provider fixture pending: no macOS Swift/Clang/xcrun')
        from saved_tags_native import run_native
        from saved_tags_core_native import assemble_core
        run_native(ROOT,SOURCE,assembler=assemble_core,expected='PASS exact Core provider cancellation/reentrancy/window bounds with Signal boundary')
if __name__=='__main__': unittest.main(argv=[a for a in sys.argv if a != '--require-native'],verbosity=2)
