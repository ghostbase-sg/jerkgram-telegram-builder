"""Beta3 reset repair: exact production extraction and mandatory macOS gate.

JG_BETA3_REQUIRE_NATIVE=1 fails closed when native Swift/Clang is unavailable.
No historical fixture or compiler input is modified.
"""
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CORE = Path(os.environ.get('JG_BETA3_BOT_CORE', str(ROOT / 'work/swiftgram-src/submodules/TelegramCore/Sources')))
FIX = ROOT / 'tests/fixtures/beta3_bot_reset'
spec = importlib.util.spec_from_file_location('beta2_codec_reuse', ROOT / 'tests/test_jg131_beta2_bot_codec.py')
codec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(codec)
declaration = codec.declaration


def native_main():
    source = (CORE / 'State/JerkgramBotBridgeHistory.swift').read_text()
    storage = '\n'.join(declaration(source, anchor) for anchor in [
        'private func botBridgeValidatedAccount(', 'private func botBridgeReadProgress(',
        'func jerkgramPrepareBotBridgeHistory(', 'private func botBridgeWriteProgress('])
    return (FIX / 'codec.swift').read_text().replace('/* REAL_STORAGE_BOUNDARY */', storage)


def manager_main132():
    source = (CORE / 'State/AccountStateManager.swift').read_text()
    queue = (CORE / 'State/Sync/StateOperationQueue.swift').read_text()
    custom = (CORE / 'State/AccountStateManager+Custom.swift').read_text()
    reset = declaration(source, 'public func reset()')
    segment = reset[reset.index('self.replaceOperations(with: .fetchDifference'):reset.index('let network = self.network')].strip()
    start = declaration(source, 'func startFirstOperation()')
    guards = start[start.index('guard let operation'):start.index('switch operation.content')]
    return ((FIX / 'manager132.swift').read_text()
        .replace('/* REAL_OPERATION_TYPES */', declaration(queue, 'enum StateOperation {') + '\n' + declaration(queue, 'struct StateOperationQueue {'))
        .replace('/* REAL_REPLACEMENT */', declaration(source, 'func replaceOperations('))
        .replace('/* REAL_RESET_SCHEDULING */', segment)
        .replace('/* REAL_START_GUARDS */', guards)
        .replace('/* REAL_RUN_CUSTOM */', declaration(custom, 'func runCustom(')))


def manager_main():
    if (CORE / 'State/Sync/StateOperationQueue.swift').is_file():
        return manager_main132()
    source = (CORE / 'State/AccountStateManager.swift').read_text()
    reset = declaration(source, 'public func reset()')
    segment = reset[reset.index('self.operationDisposable.set(nil)'):reset.index('let appliedValues:')].strip()
    start = declaration(source, 'private func startFirstOperation()')
    guards = start[start.index('guard let operation'):start.index('switch operation.content')]
    custom = start[start.index('case let .custom(operationId, signal):'):start.index('case let .processEvents(operationId, events):')]
    return ((FIX / 'manager.swift').read_text()
        .replace('/* REAL_OPERATION_TYPES */', declaration(source, 'private enum AccountStateManagerOperationContent') + '\n' + declaration(source, 'private final class AccountStateManagerOperation'))
        .replace('/* REAL_REPLACEMENT */', declaration(source, 'private func replaceOperations('))
        .replace('/* REAL_RESET_SCHEDULING */', segment)
        .replace('/* REAL_START_GUARDS */', guards)
        .replace('/* REAL_CUSTOM_ACTIVATION */', custom))


def diagnostics_main():
    source = (CORE / 'State/JerkgramBotBridgeDiagnostics.swift').read_text()
    policy = source.split('// BEGIN BOTBRIDGE DIAGNOSTICS\n')[1].split('// END BOTBRIDGE DIAGNOSTICS')[0]
    return 'import Foundation\n' + policy + (FIX / 'diagnostics.swift').read_text()


def controller_main():
    # Reuse established boundary facades and tests, extracting current owners.
    source = (CORE / 'State/JerkgramBotBridgeHistory.swift').read_text()
    account_state = (CORE / 'SyncCore/SyncCore_AuthorizedAccountState.swift').read_text()
    if 'public let state: State?' not in account_state:
        raise AssertionError('Current authorized account state no longer exposes the live cursor')
    old = ROOT / 'tests/fixtures/botbridge1'
    shared = (old / 'storage.swift').read_text().split('/* REAL_STORAGE */')[0].replace('/* REAL_POLICY */', codec.policy(source))
    # The older storage fixture predates live-state observation. Extend only the
    # assembled Beta3 boundary with the same four cursor fields as 13.2.
    prior = 'struct AuthorizedAccountState { let peerId: PeerId; let isTestingEnvironment: Bool }'
    current = '''struct AuthorizedAccountState {
    struct State { let pts: Int32; let qts: Int32; let date: Int32; let seq: Int32 }
    let peerId: PeerId
    let isTestingEnvironment: Bool
    let state: State?
    init(peerId: PeerId, isTestingEnvironment: Bool, state: State? = nil) {
        self.peerId = peerId; self.isTestingEnvironment = isTestingEnvironment; self.state = state
    }
}'''
    if shared.count(prior) != 1:
        raise AssertionError('Historical storage boundary changed')
    shared = shared.replace(prior, current, 1)
    anchors = ['struct BotBridgeHistoryEvent', 'private func botBridgeValidatedAccount(',
        'private func botBridgeReadProgress(', 'func jerkgramPrepareBotBridgeHistory(',
        'private func botBridgeWriteProgress(', 'func botBridgeObservedLive(', 'private func botBridgeCursor(',
        'private struct BotBridgeHistoryPage', 'private func botBridgePage(',
        'private func botBridgeReplyPeerIds(', 'private func importBotBridgeHistoryPage(',
        'private final class BotBridgePageLease', 'final class BotBridgeHistoryController']
    return (old / 'controller.swift').read_text().replace('/* SHARED_STORAGE_FACADES */', shared).replace('/* REAL_CONTROLLER_AND_DEPENDENCIES */', '\n'.join(declaration(source, a) for a in anchors)) + (FIX / 'controller_recovery.swift').read_text()


class ResetRepair(unittest.TestCase):
    def test_routine_account_reset_only_observes(self):
        source = (CORE / 'Account/Account.swift').read_text()
        reset = declaration(source, 'public func resetStateManagement()')
        self.assertIn('.lifecycle(.stateManagementReset, terminal: false)', reset)
        self.assertNotIn('jerkgramCancelBotBridgeHistory', reset)
        self.assertIn('self.stateManager.reset()', reset)
        self.assertIn('jerkgramCancelBotBridgeHistory(reason: .softReset)', source)

    def test_observation_cannot_freeze_or_cancel(self):
        source = (CORE / 'State/JerkgramBotBridgeDiagnostics.swift').read_text()
        lifecycle = declaration(source, 'func lifecycle(_ kind: BotBridgeDiagnosticLifecycle, terminal: Bool = true)')
        self.assertIn('precondition(kind != .stateManagementReset || !terminal)', lifecycle)
        self.assertIn('kind != .stateManagementReset', lifecycle)
        self.assertLess(lifecycle.index('cancelHistory(kind)'), lifecycle.index('lock.lock()'))
        owner = declaration(source, 'final class BotBridgeDiagnosticOwner')
        self.assertIn('precondition(kind != .stateManagementReset || !terminal)', owner)

    def test_codec_and_atomic_recovery_wiring(self):
        source = (CORE / 'State/JerkgramBotBridgeHistory.swift').read_text()
        self.assertIn('softResetRecoveryVersion = try container.decodeIfPresent(Int32.self, forKey: .softResetRecoveryVersion) ?? 0', source)
        self.assertIn('try container.encode(softResetRecoveryVersion, forKey: .softResetRecoveryVersion)', source)
        prepare = declaration(source, 'func jerkgramPrepareBotBridgeHistory(')
        self.assertLess(prepare.index('botBridgeValidatedAccount('), prepare.index('botBridgeRecoverInitialSoftReset('))
        self.assertLess(prepare.index('botBridgeRecoverInitialSoftReset('), prepare.index('botBridgeWriteProgress('))
        recover = declaration(source, 'func botBridgeRecoverInitialSoftReset(')
        for field in ['examined','inserted','insertedPeers','insertedUsers','insertedChats','deleteIdsObserved','skipped','unsupported','deletions','missingReferences','reservedPages','committedPages']:
            self.assertIn('progress.' + field + ' == 0', recover)
        self.assertIn('fallback.softResetRecoveryVersion = 1', source)
        self.assertIn('invalid.softResetRecoveryVersion = 1', declaration(source, 'private func botBridgeReadProgress('))

    def test_native_assembly_uses_real_codec_and_production_storage(self):
        main = native_main()
        self.assertNotIn('/* REAL_STORAGE_BOUNDARY */', main)
        self.assertIn('func jerkgramPrepareBotBridgeHistory(', main)
        self.assertIn('encodeInt32(0, forKey: "reservedPages")', main)
        self.assertTrue(codec.codec_sources())

    def test_manager_and_lifecycle_native_assembly(self):
        manager = manager_main()
        self.assertNotIn('/* REAL_', manager)
        source = (CORE / 'State/AccountStateManager.swift').read_text()
        if (CORE / 'State/Sync/StateOperationQueue.swift').is_file():
            self.assertIn(declaration(source, 'func replaceOperations('), manager)
            self.assertIn(declaration((CORE / 'State/Sync/StateOperationQueue.swift').read_text(), 'struct StateOperationQueue {'), manager)
            self.assertIn(declaration((CORE / 'State/AccountStateManager+Custom.swift').read_text(), 'func runCustom('), manager)
            self.assertIn('self.replaceOperations(with: .fetchDifference', manager)
        else:
            self.assertIn(declaration(source, 'private func replaceOperations('), manager)
            self.assertIn('self.operationDisposable.set(nil)', manager)
        self.assertIn('let _ = (signal |> deliverOn(self.queue)).start(completed:', manager)
        self.assertNotIn('/* REAL_', diagnostics_main())
        controller = controller_main()
        self.assertNotIn('/* REAL_', controller)
        self.assertIn(declaration((CORE / 'State/JerkgramBotBridgeHistory.swift').read_text(), 'func botBridgeObservedLive('), controller)

    def test_current_target_codec_inputs_are_exact(self):
        evidence = json.loads((FIX / 'PROVENANCE.json').read_text())
        self.assertEqual(evidence['ref'], '24638bc69bd083981b178dd1e7f921eebbf7fc46')
        for row in evidence['files']:
            data = (ROOT / row['fixture']).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), row['sha256'], row['path'])
            self.assertEqual(hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest(), row['sha'], row['path'])

    def test_native_manager_diagnostics_and_controller(self):
        if not shutil.which('swiftc'):
            if os.environ.get('JG_BETA3_REQUIRE_NATIVE') == '1':
                self.fail('Mandatory Beta3 manager/lifecycle/controller native execution requires Swift')
            self.skipTest('Swift unavailable; manager/lifecycle/controller execution pending')
        for name, text in [('manager', manager_main()), ('diagnostics', diagnostics_main()), ('controller', controller_main())]:
            for optimization in ['-O', '-Onone']:
                with self.subTest(name=name, optimization=optimization), tempfile.TemporaryDirectory(prefix='beta3-native-') as tmp:
                    main = Path(tmp) / 'main.swift'; main.write_text(text)
                    executable = Path(tmp) / 'native'
                    compiled = subprocess.run([shutil.which('swiftc'), '-swift-version', '5', optimization, str(main), '-o', str(executable)], capture_output=True, text=True, timeout=120)
                    self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
                    result = subprocess.run([str(executable)], capture_output=True, text=True, timeout=30)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertIn('PASS', result.stdout)

    def test_native_codec_both_optimizations(self):
        if not shutil.which('swiftc') or not shutil.which('xcrun'):
            if os.environ.get('JG_BETA3_REQUIRE_NATIVE') == '1':
                self.fail('Mandatory Beta3 native gate requires macOS Swift/Clang; execution remains pending')
            self.skipTest('macOS Swift/Clang unavailable; native execution pending')
        with tempfile.TemporaryDirectory(prefix='beta3-reset-') as tmp:
            fixture = Path(tmp) / 'fixture'; fixture.mkdir()
            for name in ['official', 'support']:
                (fixture / name).symlink_to(codec.FIXTURE / name, target_is_directory=True)
            (fixture / 'native.swift').write_text(native_main())
            old_fixture, old_owner = codec.FIXTURE, codec.OWNER
            try:
                codec.FIXTURE = fixture
                codec.OWNER = CORE / 'State/JerkgramBotBridgeHistory.swift'
                for optimization in ['-O', '-Onone']:
                    folder = Path(tmp) / optimization; folder.mkdir()
                    executable = codec.compile_fixture(folder, optimization)
                    result = subprocess.run([str(executable)], capture_output=True, text=True, timeout=30)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertIn('PASS Beta3 actual Postbox reset recovery', result.stdout)
            finally:
                codec.FIXTURE, codec.OWNER = old_fixture, old_owner


if __name__ == '__main__':
    unittest.main(verbosity=2)
