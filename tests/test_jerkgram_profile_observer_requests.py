import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / 'scripts/jerkgram_profile_observer_v1_payload/JerkgramProfileObserverRequests.swift'
HELPER = ROOT / 'scripts/jerkgram_profile_observer_request_patch.py'


class ProfileObserverRequestsTests(unittest.TestCase):
    def helper(self):
        spec = importlib.util.spec_from_file_location('observer_request_patch', HELPER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_real_13_2_hooks_and_idempotence(self):
        configured = os.environ.get('JERKGRAM_OBSERVER_SOURCE_ROOT') or os.environ.get('JERKGRAM_PINNED_SOURCE_ROOT')
        source = Path(configured) if configured else ROOT.parent / 'release-1.2.0/source'
        if not source.exists():
            if configured:
                self.fail('configured 13.2 source directory does not exist')
            self.skipTest('13.2 source is supplied by native CI')
        helper = self.helper()
        outputs = {}
        for path, patch in helper.REQUEST_PATCHES.items():
            result = subprocess.run(['git', '-C', str(source), 'show', '24638bc69bd083981b178dd1e7f921eebbf7fc46:' + path], capture_output=True, text=True)
            original = result.stdout if result.returncode == 0 else (source / path).read_text()
            changed = patch(original)
            self.assertNotEqual(original, changed)
            self.assertEqual(patch(changed), changed)
            self.assertIn('PROFILE_OBSERVER_', changed)
            outputs[path.rsplit('/', 1)[1]] = changed
            # The current product has retention/public-name patches in addition
            # to the pristine 13.2 base. Both must retain valid hook anchors.
            product = (source / path).read_text()
            self.assertEqual(patch(patch(product)), patch(product))
        self.assertIn('case let .updateUser(updateUserData):', outputs['UpdateInterpreter.swift'])
        self.assertIn('jerkgramProfileObserverMightWatch(accountPeerId:', outputs['UpdateInterpreter.swift'])
        self.assertEqual(outputs['StateReplay+Peers.swift'].count('jerkgramProfileObserverUpdatedUser('), 1)
        self.assertIn('publicName: jerkgramObserverPublicName', outputs['StateReplay+Peers.swift'])
        self.assertIn('case let .UpdatePeer(id, f, publicName):', outputs['StateReplay.swift'])
        self.assertIn('self.applyUpdatePeer(id, f, jerkgramObserverPublicName: publicName)', outputs['StateReplay.swift'])
        self.assertIn('firstName: updateUserNameData.firstName, lastName: updateUserNameData.lastName', outputs['UpdateInterpreter+Peers.swift'])
        state = outputs['AccountIntermediateState.swift']
        self.assertIn('jerkgramObserverInvalidatedPeerIds.count < 4096', state)
        self.assertIn('case let .UpdatePeer(id, f, _):', state)
        self.assertIn('self.addOperation(.UpdatePeer(id, f, jerkgramObserverPublicName: jerkgramObserverPublicName))', state)
        self.assertIn('self.jerkgramObserverInvalidatedPeerIds = state.state.state.jerkgramObserverInvalidatedPeerIds', state)
        self.assertIn('jerkgramProfileObserverUnionInvalidations(', state)
        self.assertIn('self.jerkgramObserverInvalidatedPeerIds.isEmpty', state)
        hub = outputs['AccountStateEventHub.swift']
        self.assertIn('self.externallyUpdatedPeerIdsPipe.putNext(Array(events.externallyUpdatedPeerId))', hub)
        self.assertIn('self.jerkgramObserverInvalidatedPeerIdsPipe.putNext(Array(events.jerkgramObserverInvalidatedPeerIds))', hub)

    def test_missing_anchor_fails_closed(self):
        helper = self.helper()
        for patch in helper.REQUEST_PATCHES.values():
            with self.assertRaises(RuntimeError):
                patch('unsupported source')

    def test_ingress_ownership_avoids_set_copy_per_batch(self):
        source = PAYLOAD.read_text()
        self.assertIn('final class JerkgramProfileRequestIngress<Id: Hashable>', source)
        self.assertNotIn('struct Ingress', source)
        self.assertNotIn('var current = current', source)
        self.assertIn('self.ingress.swap(JerkgramProfileRequestIngress())', source)

    def test_request_is_narrow_and_cancellable(self):
        source = PAYLOAD.read_text()
        self.assertIn('automaticFloodWait: false', source)
        self.assertNotIn('retryRequest', source)
        self.assertNotIn('forceUpdateCachedPeerData', source)
        self.assertNotIn('updateCurrentPeerNotificationSettings', source)
        self.assertIn('weak var account: Account?', source)
        self.assertIn('jerkgramProfileObserverCheckWatched', source)
        self.assertIn('jerkgramProfileObserverReady', source)
        self.assertIn('jerkgramProfileObserverNewWatches', source)
        self.assertIn('DispatchTime.now().uptimeNanoseconds', source)

    def test_native_public_name_operation_metadata(self):
        if not shutil.which('swiftc'):
            if os.environ.get('JERKGRAM_OBSERVER_SOURCE_ROOT') or os.environ.get('JERKGRAM_PINNED_SOURCE_ROOT'):
                self.fail('native CI requires swiftc')
            self.skipTest('native Swift compiler unavailable')
        configured = os.environ.get('JERKGRAM_OBSERVER_SOURCE_ROOT') or os.environ.get('JERKGRAM_PINNED_SOURCE_ROOT')
        source_root = Path(configured) if configured else ROOT.parent / 'release-1.2.0/source'
        original = (source_root / 'submodules/TelegramCore/Sources/Account/AccountIntermediateState.swift').read_text()
        patched = self.helper().patch_request_intermediate_state(original)
        enum_case = next(line for line in patched.splitlines() if line.startswith('    case UpdatePeer('))
        start = patched.index('    mutating func updatePeer(_ id:')
        end = patched.index('\n    }\n', start) + len('\n    }\n')
        method = patched[start:end]
        fixture = (ROOT / 'tests/native/ProfileObserverPublicNameMetadataTests.swift').read_text()
        fixture = fixture.replace('/* ENUM_CASE */', enum_case).replace('/* UPDATE_METHOD */', method)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'main.swift'
            path.write_text(fixture)
            binary = Path(directory) / 'public-name-tests'
            subprocess.run(['swiftc', str(path), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True)

    def test_native_policy(self):
        if not shutil.which('swiftc'):
            if os.environ.get('JERKGRAM_OBSERVER_SOURCE_ROOT') or os.environ.get('JERKGRAM_PINNED_SOURCE_ROOT'):
                self.fail('native CI requires swiftc')
            self.skipTest('native Swift compiler unavailable')
        source = PAYLOAD.read_text()
        policy = source.split('// BEGIN NATIVE REQUEST POLICY\n', 1)[1].split('// END NATIVE REQUEST POLICY', 1)[0]
        fixture = (ROOT / 'tests/native/ProfileObserverRequestPolicyTests.swift').read_text()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'main.swift'
            path.write_text('import Foundation\n' + policy + '\n' + fixture)
            binary = Path(directory) / 'policy-tests'
            subprocess.run(['swiftc', str(path), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True)


if __name__ == '__main__':
    unittest.main()
