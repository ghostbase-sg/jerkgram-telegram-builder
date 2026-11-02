"""Task 1 source checks and real extracted Swift execution (requires Swift).
Boundary fakes replace storage I/O only; policy/callback algorithms are extracted unchanged.
This does not execute a real Postbox DB, whole worker, or device.
"""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('JERKGRAM_BOTBRIDGE_SOURCE', ROOT/'work/swiftgram-src'))
BEFORE = Path(os.environ.get('JERKGRAM_BOTBRIDGE_C_SOURCE', SOURCE.parent/'before'))
PROVENANCE = ROOT/'tests/fixtures/botbridge1/provenance'
CORE = SOURCE / 'submodules/TelegramCore/Sources'
FIXTURES = Path(__file__).parent / 'fixtures/botbridge1'

def method(text, anchor):
    start = text.index(anchor)
    opening = text.index('{', start)
    depth = 1
    i = opening + 1
    while depth:
        depth += (text[i] == '{') - (text[i] == '}')
        i += 1
    return text[start:i]

class HistoryTests(unittest.TestCase):
    def test_required_production_boundary(self):
        p = CORE / 'State/JerkgramBotBridgeHistory.swift'
        self.assertTrue(p.exists(), 'missing bounded history production implementation')
        text = p.read_text()
        for item in ['// BEGIN BOTBRIDGE POLICY', '// END BOTBRIDGE POLICY', 'final class BotBridgeHistoryController', 'func cancel(reason:', 'automaticFloodWait: false', 'addHistoricalMessagesWithoutInteractiveActions', 'jerkgramIncludeBotMessagePeers', 'synchronouslyIsMessageDeletedRemotely', 'synchronouslyIsMessageDeletedInteractively']:
            self.assertIn(item, text)
        for item in ['setState(', 'finalStateWithDifference(', 'replayFinalState(', 'getDialogs(', 'getHistory(', 'Logger.', 'errorDescription', 'UserDefaults']:
            self.assertNotIn(item, text)
        import re
        self.assertEqual(set(re.findall(r'Api.functions.([\w.]+)\(', text)), {'updates.getState', 'updates.getDifference'})

    def test_nested_delete_vectors_bounded_before_working_sets(self):
        text = (CORE/'State/JerkgramBotBridgeHistory.swift').read_text()
        self.assertTrue('static let maxDeleteIdsPerPage = 20000' in text, 'missing nested delete-ID bound')
        storage = method(text, 'private func importBotBridgeHistoryPage(')
        self.assertLess(storage.index('deleteIdCount <= BotBridgeHistoryProgress.maxDeleteIdsPerPage'), storage.index('var candidates:'))
        self.assertNotIn('data.messages.contains(id.id)', storage)

    def test_active_watchdog_precedes_reservation_subscription(self):
        text = (CORE/'State/JerkgramBotBridgeHistory.swift').read_text()
        schedule = method(text, 'private func schedulePage(')
        self.assertIn('self.armWatchdog(lease)', schedule)
        self.assertLess(schedule.index('self.armWatchdog(lease)'), schedule.index('self.reserveAndDispatch(lease)'))
        reserve = method(text, 'private func reserveAndDispatch(')
        self.assertNotIn('lease.timer =', reserve, 'reservation callback must not renew the active lease watchdog')

    def test_postbox_only_callback_blocks_change(self):
        before = (BEFORE / 'submodules/Postbox/Sources/Postbox.swift').read_text()
        after = (SOURCE / 'submodules/Postbox/Sources/Postbox.swift').read_text()
        original = method(before, 'fileprivate func addMessages(transaction:')
        changed = method(after, 'fileprivate func addMessages(transaction:')
        expected = original.replace('location: AddMessagesLocation)', 'location: AddMessagesLocation, runInstalledActions: Bool = true)')
        expected = expected.replace('if let bag = self.installedMessageActionsByPeerId[peerId]', 'if runInstalledActions, let bag = self.installedMessageActionsByPeerId[peerId]')
        expected = expected.replace('if let bag = self.installedStoreOrUpdateMessageActionsByPeerId[peerId]', 'if runInstalledActions, let bag = self.installedStoreOrUpdateMessageActionsByPeerId[peerId]')
        self.assertEqual(changed, expected)
        self.assertEqual(method(before, 'public func addMessages('), method(after, 'public func addMessages('))
        historical = method(after, 'public func addHistoricalMessagesWithoutInteractiveActions(')
        self.assertIn('location: .Random, runInstalledActions: false', historical)

    def test_existing_inclusion_algorithm_preserved(self):
        path = 'submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift'
        before = (BEFORE / path).read_text()
        after = (SOURCE / path).read_text()
        self.assertEqual(method(before, 'func jerkgramIncludeBotMessagePeers('), method(after, 'func jerkgramIncludeBotMessagePeers('))

    def test_old_pager_and_suppression_removed(self):
        for p in [CORE/'State/AccountStateManager.swift', CORE/'Account/Account.swift']:
            text = p.read_text()
            self.assertFalse('GhostBaseBotHistoryGate' in text, 'old gate remains')
            self.assertFalse('ghostBaseStartBotShadowHistory' in text, 'old startup remains')
            self.assertFalse('ghostBaseBotShadow' in text, 'old pager remains')
        account = (CORE/'Account/Account.swift').read_text()
        self.assertIn('jerkgramStartBotBridgeHistory(recordId: id.int64)', account)
        self.assertIn('strongSelf._loggedOut.set(true)', account)

    def test_baseline_and_modern_owners_unchanged(self):
        import hashlib, json
        frozen = json.loads((PROVENANCE/'MODERN-WRITE-BASELINE.json').read_text())
        for row in frozen['files']:
            self.assertEqual(hashlib.sha256((BEFORE/row['path']).read_bytes()).hexdigest(), row['sha256'], row['path'])
        allowed = {'submodules/TelegramCore/Sources/Account/Account.swift', 'submodules/TelegramCore/Sources/Authorization.swift', 'submodules/TelegramCore/Sources/State/AccountStateManager.swift', 'submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift'}
        for row in frozen['files']:
            if row['path'] not in allowed:
                self.assertEqual(hashlib.sha256((SOURCE/row['path']).read_bytes()).hexdigest(), row['sha256'], row['path'])
        manager = (CORE/'State/AccountStateManager.swift').read_text()
        self.assertIn((PROVENANCE/'MODERN-POLL-DIFFERENCE-BASELINE.swift.txt').read_text(), manager)
        baseline_manager = (BEFORE/'submodules/TelegramCore/Sources/State/AccountStateManager.swift').read_text()
        self.assertEqual(method(baseline_manager, 'func addCustomOperation<T, E>'), method(manager, 'func addCustomOperation<T, E>'))

    def test_preference_key_scoped_collision_and_generation_site(self):
        import sys
        sys.path.insert(0, str(ROOT/'scripts'))
        from verify_jg131_botbridge1 import verify_preference_key_available
        self.assertGreater(verify_preference_key_available(BEFORE), 0)
        authorization = (CORE/'Authorization.swift').read_text()
        self.assertEqual(authorization.count('jerkgramRenewBotBridgeGeneration('), 1)
        history = (CORE/'State/JerkgramBotBridgeHistory.swift').read_text()
        self.assertIn('guard user.botInfo != nil else { return }', method(history, 'func jerkgramRenewBotBridgeGeneration('))

    def run_swift(self, text):
        compiler = shutil.which('swiftc')
        if compiler is None:
            self.skipTest('Swift compiler unavailable; native behavioral harness pending macOS')
        with tempfile.TemporaryDirectory() as d:
            src = Path(d)/'main.swift'; src.write_text(text)
            exe = Path(d)/'fixture'
            compiled = subprocess.run([compiler, str(src), '-o', str(exe)], capture_output=True, text=True, timeout=60)
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            result = subprocess.run([str(exe)], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('PASS', result.stdout)

    def test_native_production_policy_and_lifetime(self):
        text = (CORE/'State/JerkgramBotBridgeHistory.swift').read_text()
        policy = text.split('// BEGIN BOTBRIDGE POLICY\n')[1].split('// END BOTBRIDGE POLICY')[0]
        self.run_swift('import Foundation\n' + policy + (FIXTURES/'policy.swift').read_text())

    def test_native_real_page_lease(self):
        text = (CORE/'State/JerkgramBotBridgeHistory.swift').read_text()
        policy = text.split('// BEGIN BOTBRIDGE POLICY\n')[1].split('// END BOTBRIDGE POLICY')[0]
        lease = method(text, 'private final class BotBridgePageLease')
        fixture = (FIXTURES/'lease.swift').read_text().replace('/* REAL_POLICY */', policy).replace('/* REAL_LEASE */', lease)
        self.run_swift(fixture)

    def test_native_real_storage_helper(self):
        text = (CORE/'State/JerkgramBotBridgeHistory.swift').read_text()
        policy = text.split('// BEGIN BOTBRIDGE POLICY\n')[1].split('// END BOTBRIDGE POLICY')[0]
        pieces = [method(text, name) for name in [
            'private func botBridgeValidatedAccount(',
            'private func botBridgeWriteProgress(',
            'private struct BotBridgeHistoryPage',
            'private func botBridgeReplyPeerIds(',
            'private func importBotBridgeHistoryPage('
        ]]
        fixture = (FIXTURES/'storage.swift').read_text().replace('/* REAL_POLICY */', policy).replace('/* REAL_STORAGE */', '\n'.join(pieces))
        self.run_swift(fixture)

    def controller_fixture_source(self):
        text = (CORE/'State/JerkgramBotBridgeHistory.swift').read_text()
        policy = text.split('// BEGIN BOTBRIDGE POLICY\n')[1].split('// END BOTBRIDGE POLICY')[0]
        shared = (FIXTURES/'storage.swift').read_text().split('/* REAL_STORAGE */')[0].replace('/* REAL_POLICY */', policy)
        pieces = [method(text, name) for name in [
            'struct BotBridgeHistoryEvent',
            'private func botBridgeValidatedAccount(',
            'private func botBridgeReadProgress(',
            'func jerkgramPrepareBotBridgeHistory(',
            'private func botBridgeWriteProgress(',
            'private func botBridgeCursor(',
            'private struct BotBridgeHistoryPage',
            'private func botBridgePage(',
            'private func botBridgeReplyPeerIds(',
            'private func importBotBridgeHistoryPage(',
            'private final class BotBridgePageLease',
            'final class BotBridgeHistoryController'
        ]]
        fixture = (FIXTURES/'controller.swift').read_text().replace('/* SHARED_STORAGE_FACADES */', shared).replace('/* REAL_CONTROLLER_AND_DEPENDENCIES */', '\n'.join(pieces))
        return fixture

    def test_native_real_controller_and_response_adapter(self):
        self.run_swift(self.controller_fixture_source())

    def test_controller_fixture_uses_complete_production_types(self):
        text = (CORE/'State/JerkgramBotBridgeHistory.swift').read_text()
        fixture = self.controller_fixture_source()
        self.assertIn(method(text, 'final class BotBridgeHistoryController'), fixture)
        self.assertIn(method(text, 'private func botBridgePage('), fixture)
        self.assertIn(method(text, 'private func importBotBridgeHistoryPage('), fixture)
        self.assertNotIn('/* REAL_', fixture)
        self.assertNotIn('/* SHARED_', fixture)

    def test_native_real_postbox_method_mixed_transaction(self):
        text = (SOURCE/'submodules/Postbox/Sources/Postbox.swift').read_text()
        impl = method(text, 'fileprivate func addMessages(transaction:')
        entries = method(text, 'public func addMessages(') + '\n' + method(text, 'public func addHistoricalMessagesWithoutInteractiveActions(')
        fixture = (FIXTURES/'postbox.swift').read_text().replace('/* REAL_IMPL */', impl).replace('/* REAL_ENTRIES */', entries)
        self.run_swift(fixture)

if __name__ == '__main__':
    unittest.main()
