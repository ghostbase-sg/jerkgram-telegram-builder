"""Run actual production snapshot helper on macOS; source wiring checks run everywhere."""
from pathlib import Path
import os, shutil, subprocess, tempfile, unittest
ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('JG_PERFORMANCE_SOURCE', ROOT / 'work/swiftgram-src'))
POLICY = 'submodules/TelegramCore/Sources/TelegramEngine/Privacy/BlockedPeersContext.swift'
HISTORY = 'submodules/TelegramUI/Sources/ChatHistoryEntriesForView.swift'
class BlockedSnapshotTests(unittest.TestCase):
    def test_one_snapshot_per_mapping_preserves_live_updates(self):
        history = (SOURCE/HISTORY).read_text()
        self.assertEqual(history.count('JerkgramBlockedReactionPolicy.messageFilterSnapshot('), 1)
        self.assertLess(history.index('JerkgramBlockedReactionPolicy.messageFilterSnapshot('), history.index('    loop: for entry in view.entries {'))
        self.assertIn('blockedMessageFilter?.isHidden(authorId: message.author?.id) ?? false', history)
        self.assertNotIn('JerkgramBlockedReactionPolicy.isMessageHidden(', history)
        policy = (SOURCE/POLICY).read_text()
        self.assertIn('public struct MessageFilterSnapshot {', policy)
        self.assertIn('guard self.isGroupChat(chatPeer), self.hideBlockedMessages(accountPeerId: accountPeerId) else', policy)
        self.assertIn('public static func notifySettingsChanged()', policy)
        self.assertIn('self.notifyPresentationChanged()', policy)
    @unittest.skipUnless(shutil.which('swiftc'), 'native production helper requires macOS Swift')
    def test_actual_snapshot_is_account_scoped_immutable_and_handles_self_and_missing_author(self):
        policy = (SOURCE/POLICY).read_text()
        helper = policy.split('    public struct MessageFilterSnapshot {', 1)[1].split('    // Build175 snapshot end', 1)[0]
        fixture = '''import Foundation
typealias PeerId = Int64
struct MessageFilterSnapshot {''' + helper + '''
let accountA: PeerId = 1
let accountB: PeerId = 2
var blocked: Set<PeerId> = [2, 3]
let a = MessageFilterSnapshot(accountPeerId: accountA, blockedPeerIds: blocked)
precondition(!a.isHidden(authorId: nil))
precondition(!a.isHidden(authorId: accountA))
precondition(a.isHidden(authorId: accountB))
precondition(a.isHidden(authorId: 3))
precondition(!a.isHidden(authorId: 4))
// A mapping owns its value snapshot; a later mapping sees the changed blocked set.
blocked.remove(3)
let next = MessageFilterSnapshot(accountPeerId: accountA, blockedPeerIds: blocked)
precondition(a.isHidden(authorId: 3))
precondition(!next.isHidden(authorId: 3))
let b = MessageFilterSnapshot(accountPeerId: accountB, blockedPeerIds: [1, 2])
precondition(!b.isHidden(authorId: accountB))
precondition(b.isHidden(authorId: accountA))
let empty = MessageFilterSnapshot(accountPeerId: accountA, blockedPeerIds: [])
precondition(!empty.isHidden(authorId: 3))
print("actual snapshot helper PASS")
'''
        # Public production members need public fixture types, as in TelegramCore.
        fixture = fixture.replace('typealias PeerId', 'public typealias PeerId')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'main.swift'; p.write_text(fixture)
            subprocess.run(['swiftc', '-warnings-as-errors', str(p), '-o', d+'/check'], check=True)
            subprocess.run([d+'/check'], check=True)
if __name__ == '__main__': unittest.main()
