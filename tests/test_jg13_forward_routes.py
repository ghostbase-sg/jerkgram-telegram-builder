"""UI route contracts; Core owns per-message protected normalization."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('JG13_SOURCE', ROOT / 'work/swiftgram-src'))


class ForwardRouteTests(unittest.TestCase):
    def setUp(self):
        self.source = (SOURCE / 'submodules/TelegramUI/Sources/ChatControllerForwardMessages.swift').read_text()
        # Reconstruct the exact parent in an isolated Git root. CI only has
        # the materialized final tree, not a developer's scratch fixtures.
        owner = 'submodules/TelegramUI/Sources/ChatControllerForwardMessages.swift'
        manifest = json.loads((ROOT / 'patches/jg13-portable-copy.sha256.json').read_text())['owners'][owner]
        self.assertEqual(hashlib.sha256(self.source.encode()).hexdigest(), manifest['after_sha256'])
        with tempfile.TemporaryDirectory() as directory:
            baseline_root = Path(directory)
            target = baseline_root / owner
            target.parent.mkdir(parents=True)
            target.write_text(self.source)
            subprocess.run(['git', 'init', '-q', directory], check=True)
            subprocess.run(['git', 'apply', '--reverse', '--include=' + owner, str(ROOT / 'patches/jg13-portable-copy.patch')], cwd=baseline_root, check=True)
            self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), manifest['before_sha256'])
            self.baseline = target.read_text()

    def test_generic_selection_reaches_core_as_forward(self):
        self.assertNotIn('jerkgramPortableMessagesSignal', self.source)
        self.assertNotIn('canUsePortableCopy', self.source)
        self.assertIn('return .forward(source: message.id, threadId: nil, grouping: .auto, attributes: attributes, correlationId: nil)', self.source)
        self.assertLess(self.source.index('result.append(.message(text: text.string'), self.source.index('result.append(contentsOf: messages.map'))

    def test_obsolete_helpers_removed_and_other_private_functions_retained(self):
        import re
        removed = {'jerkgramRequiresPortableForward', 'jerkgramPortableForwardBaseMessage', 'jerkgramProtectedResourceData', 'jerkgramPortableForwardMessage'}
        original = set(re.findall(r'private func (\w+)\(', self.baseline))
        current = set(re.findall(r'private func (\w+)\(', self.source))
        self.assertEqual(original - current, removed)
        for helper in removed:
            self.assertNotIn(helper, self.source)

    def test_every_branch_retains_hide_caption_and_name_options(self):
        self.assertIn('forwardOptions?.hideNames == true\n                                    || options?.hideNames == true', self.source)
        self.assertIn('forwardOptions?.hideCaptions == true\n                                    || options?.hideCaptions == true', self.source)
        self.assertIn('hideCaptions: options?.hideCaptions ?? false', self.source)
        saved = self.source.split('let mappedMessages = messages.map', 1)[1].split('let _ = (reactionItems', 1)[0]
        self.assertIn('hideNames: options?.hideNames == true', saved)
        self.assertIn('hideCaptions: options?.hideCaptions == true', saved)
        self.assertIn('correlationId: correlationId', saved)

    def test_destination_paid_schedule_and_commit_contracts_unchanged(self):
        # Preserve the full destination/payment commit closure, not isolated tokens.
        before = self.baseline.split('let commit: ([EnqueueMessage]) -> Void', 1)[1].split('let commitResolved:', 1)[0]
        after = self.source.split('let commit: ([EnqueueMessage]) -> Void', 1)[1].split('switch mode {', 1)[0]
        self.assertEqual(before.rstrip(), after.rstrip())
        for fragment in ('case .generic:', 'case .silent:', 'case .schedule:', 'case .whenOnline:', 'scheduleWhenOnlineTimestamp', 'repeatPeriod: timeResult.repeatPeriod', 'enqueueMessages(account: strongSelf.context.account, peerId: peer.id, messages: peerMessages)', 'enqueueMessages(account: strongSelf.context.account, peerId: peerId, messages: mappedMessages)'):
            self.assertIn(fragment, self.source)
        self.assertIn('func forwardMessages(messageIds: [EngineMessage.Id], options: ChatInterfaceForwardOptionsState? = nil, resetCurrent: Bool = false)', self.source)


if __name__ == '__main__':
    unittest.main()
