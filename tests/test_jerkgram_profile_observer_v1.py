"""Exercise real current-product installation and refusal/rollback, not a Python model of Swift."""
from pathlib import Path
import importlib.util
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import apply_jerkgram_profile_observer_v1 as installer
import verify_jerkgram_profile_observer_v1 as verifier

SOURCE = Path(os.environ.get('JERKGRAM_OBSERVER_PRODUCT_SOURCE', ROOT.parent/'release-1.2.0/source'))


class InstallationTests(unittest.TestCase):
    def copy_source(self, destination):
        for name in installer.PATCHES:
            path = SOURCE/name
            if not path.exists():
                self.skipTest('Materialized13.2 product owners unavailable; run source integration gate')
            target = destination/name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())

    def tree(self, root):
        return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}

    def test_actual_current_product_install_and_repeat(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.copy_source(root)
            installer.install(root)
            verifier.verify(root)
            before = self.tree(root)
            installer.install(root)
            verifier.verify(root)
            self.assertEqual(before, self.tree(root))
            peers = (root/(installer.PREFIX+'UpdatePeers.swift')).read_text()
            self.assertIn('previous.isHidden == event.isHidden {', peers)
            self.assertNotIn('event.observedAt - previous.observedAt <= 2', peers)
            full = (root/(installer.PREFIX+'TelegramEngine/Peers/UpdateCachedPeerData.swift')).read_text()
            self.assertEqual(full.count('jerkgramProfileObserverFullUser('), 1)
            self.assertIn('jerkgramObserverExcludingPeerId: peerId', full)
            self.assertIn('jerkgramProfileObserverUpdatedPeers(transaction: transaction, accountPeerId: accountPeerId, peers: peers,', peers)
            observer = (root/(installer.PREFIX+'JerkgramProfileObserver.swift')).read_text()
            self.assertIn('case .userEmpty: continue', observer)
            self.assertIn('transaction.getPeer(peerId) as? TelegramUser', observer)
            self.assertLess(observer.index('store.migrateLegacyObserver('), observer.index('self.admission.loaded(generation: generation)'))
            self.assertIn('guard migrated && observerMigrated && store.status == "ready"', observer)
            self.assertIn('self.storageStatus.set(.failed(operation: operation, sqliteCode: code))', observer)
            ui = (root/'submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoScreen.swift').read_text()
            self.assertIn('ghostBaseRecordObservedProfileV11G(', ui)
            self.assertIn('jerkgramProfileObserverBegin(account: self.context.account, peerId: peer.id)', ui)
            self.assertTrue('jerkgramProfileObserverStartedPeerId: EnginePeer.Id?' in ui,
                            'Screen enrollment must use the TelegramCore-visible EnginePeer.Id')
            self.assertTrue('jerkgramProfileObserverStartedPeerId: PeerId?' not in ui,
                            'PeerInfoScreen does not import the Postbox PeerId type')
            old_ui = ui.replace('jerkgramProfileObserverStartedPeerId: EnginePeer.Id?',
                                'jerkgramProfileObserverStartedPeerId: PeerId?')
            self.assertEqual(installer.patch_profile_ui(old_ui), ui)

    def test_bad_last_anchor_does_not_modify_any_owner(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.copy_source(root)
            last = root/'submodules/TelegramUI/Sources/AccountContext.swift'
            last.write_text(last.read_text().replace('    private var isFrozenDisposable: Disposable?\n', ''))
            before = self.tree(root)
            with self.assertRaises(RuntimeError):
                installer.install(root)
            self.assertEqual(before, self.tree(root))

    def test_write_failure_rolls_back_and_retry_succeeds(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.copy_source(root)
            before = self.tree(root)
            replace = os.replace
            calls = []
            def fail_third(source, destination):
                calls.append(destination)
                if len(calls) == 3:
                    raise OSError('injected installation write failure')
                return replace(source, destination)
            with patch.object(installer.os, 'replace', side_effect=fail_third):
                with self.assertRaises(OSError):
                    installer.install(root)
            for name, data in before.items():
                self.assertEqual((root/name).read_bytes(), data)
            self.assertFalse((root/(installer.MANIFEST+'.pending')).exists())
            installer.install(root)
            verifier.verify(root)

    def test_tampering_is_rejected_without_repairing_over_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.copy_source(root)
            installer.install(root)
            path = root/(installer.PREFIX+'UpdatePeers.swift')
            path.write_text(path.read_text()+'\n// unexpected mutation\n')
            before = self.tree(root)
            with self.assertRaises(RuntimeError):
                installer.install(root)
            self.assertEqual(before, self.tree(root))
            with self.assertRaises(RuntimeError):
                verifier.verify(root)


if __name__ == '__main__':
    unittest.main()
