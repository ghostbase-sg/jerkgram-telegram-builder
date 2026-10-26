"""Bounded source regressions for retained chat browsing; native/UI runtime still required."""
import json
import os
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PREPARED = Path(os.environ.get('JG_EXCLUDED_PREPARED', ROOT.parent / 'excluded-history'))
SOURCE = Path(os.environ.get('JG_EXCLUDED_SOURCE', ROOT / 'work/swiftgram-src'))
if not SOURCE.exists():
    SOURCE = Path('/home/pixi/Projects/Jerkgram/iOS/jerkgram-telegram-builder/work/swiftgram-src')

def source(owner):
    target = PREPARED / 'after' / owner
    return (target if target.exists() else SOURCE / owner).read_text()

class RetainedChatInteractionTests(unittest.TestCase):
    def test_removal_banner_does_not_replace_selection_toolbar(self):
        text = source('submodules/TelegramUI/Sources/ChatInterfaceStateInputPanels.swift')
        self.assertIn('if jerkgramIsRetainedExcludedChat(chatPresentationInterfaceState.renderedPeer?.peer) && chatPresentationInterfaceState.interfaceState.selectionState == nil {', text)
        self.assertIn('panel = ChatMessageSelectionInputPanelNode(', text)
        # Existing copy and forward rules remain owned by stock context menus.
        self.assertNotIn('canForward = false', text)

    def test_visible_read_advances_locally_before_server_membership_guard(self):
        text = source('submodules/TelegramCore/Sources/TelegramEngine/Messages/ApplyMaxReadIndexInteractively.swift')
        body = text.split('func _internal_applyMaxReadIndexInteractively(transaction:', 1)[1].split('func applyOutgoingReadMaxIndex', 1)[0]
        local = re.search(r'if jerkgramIsRetainedExcludedChat\(transaction.getPeer\(index.id.peerId\)\) \{(.*?)\n    \}', body, re.S)
        self.assertIsNotNone(local, 'retained visible reads need a local-only branch before nonmember rejection')
        self.assertLess(local.start(), body.index('guard peerKeepsReadState'))
        branch = local.group(1)
        self.assertIn('transaction.applyIncomingReadMaxId(index.id)', branch)
        self.assertIn('transaction.applyMarkUnread(peerId: index.id.peerId, namespace: index.id.namespace, value: false, interactive: false)', branch)
        self.assertIn('transaction.confirmSynchronizedIncomingReadState(index.id.peerId)', branch)
        self.assertIn('return', branch)
        self.assertNotIn('applyInteractiveReadMaxIndex', branch)
        self.assertNotIn('notifyAppliedIncomingReadMessages', branch)
        self.assertNotIn('network', branch)

    def test_retained_groups_and_channels_never_synchronize_server_read_state(self):
        text = source('submodules/TelegramCore/Sources/State/NonMemberChannelReadState.swift')
        body = text.split('func peerKeepsReadState(_ peer: Peer?) -> Bool {', 1)[1]
        self.assertTrue(body.lstrip().startswith('if jerkgramIsRetainedExcludedChat(peer) { return false }'), 'local retention must not grant server read membership, including groups')
        self.assertIn('return !peerKeepsReadState(getPeer(peerId))', text)
        synchronize = (SOURCE / 'submodules/TelegramCore/Sources/State/SynchronizePeerReadState.swift').read_text()
        self.assertIn('return peerKeepsReadState(transaction.getPeer(peerId))', synchronize)

    def test_opening_retained_history_does_not_reset_local_read_position(self):
        text = source('submodules/TelegramCore/Sources/State/AccountViewTracker.swift')
        self.assertIn('if transaction.getPeerChatListIndex(peerId) == nil && !jerkgramIsRetainedExcludedChat(transaction.getPeer(peerId)) {', text)

    def test_retained_forwards_use_portable_cached_copy_out(self):
        text = source('submodules/TelegramCore/Sources/PendingMessages/EnqueueMessage.swift')
        resolver = text.split('private func ghostBaseResolveProtectedForwards(', 1)[1].split('public func enqueueMessages(', 1)[0]
        self.assertIn('guard protected || retainedCopy else', resolver)
        self.assertIn('&& !hasCopyRestriction', resolver)
        self.assertNotIn('guard enabled && chatForward,', resolver)
        self.assertIn('localOnly: jerkgramIsRetainedExcludedChat(sourcePeer)', resolver)
        media = text.split('private func ghostBaseProtectedLocalMedia(', 1)[1].split('private func ghostBaseResolveProtectedForwards(', 1)[0]
        self.assertIn('localOnly: Bool = false', media)
        self.assertLess(media.index('if localOnly { return .single(nil) }'), media.index('disposables.add(fetchedMediaResource('))
        self.assertIn('if cached.complete { return .single(localCopy(cached)) }', media)
        self.assertIn('return .message(text: text.text', text)

    def test_retained_target_is_rejected_before_enqueue_side_effects(self):
        text = source('submodules/TelegramCore/Sources/PendingMessages/EnqueueMessage.swift')
        body = text.split('func enqueueMessages(transaction: Transaction,', 1)[1]
        self.assertLess(body.index('if jerkgramIsRetainedExcludedChat(transaction.getPeer(peerId))'), body.index('if account.isSupportUser'))
        self.assertIn('return Array<MessageId?>(repeating: nil, count: messages.count)', body)
        text = source('submodules/TelegramCore/Sources/Utils/CanSendMessagesToPeer.swift')
        self.assertEqual(text.count('if jerkgramIsRetainedExcludedChat(peer._asPeer()) { return false }'), 2)

    def test_topic_read_updates_local_badge_before_receipt_guard(self):
        text = source('submodules/TelegramCore/Sources/TelegramEngine/Messages/ReplyThreadHistory.swift')
        body = text.split('    func applyMaxReadIndex(messageIndex: MessageIndex) {', 1)[1].split('    deinit', 1)[0]
        self.assertIn('let inputPeer = jerkgramIsRetainedExcludedChat(peer) ? nil : apiInputPeer(peer)', body)
        badge = body.index('strongSelf.unreadCountValue = unreadCountValue')
        receipt_guard = body.index('guard let inputPeer else {')
        request = body.index('strongSelf.account.network.request(')
        self.assertLess(badge, receipt_guard)
        self.assertLess(receipt_guard, request)

    @unittest.skipUnless((PREPARED / 'owners.json').exists(), 'prepared-only parent evidence; stage tests cover integrated hashes')
    def test_new_owners_preserve_exact_readonly_parent(self):
        owners = json.loads((PREPARED / 'owners.json').read_text())
        for owner in [
            'submodules/TelegramCore/Sources/TelegramEngine/Messages/ApplyMaxReadIndexInteractively.swift',
            'submodules/TelegramCore/Sources/State/NonMemberChannelReadState.swift',
            'submodules/TelegramCore/Sources/State/AccountViewTracker.swift',
            'submodules/TelegramCore/Sources/PendingMessages/EnqueueMessage.swift',
            'submodules/TelegramCore/Sources/TelegramEngine/Messages/ReplyThreadHistory.swift',
        ]:
            self.assertIn(owner, owners)
            self.assertEqual((PREPARED / 'before' / owner).read_bytes(), (SOURCE / owner).read_bytes())

if __name__ == '__main__': unittest.main()
