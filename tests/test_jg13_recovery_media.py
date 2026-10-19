"""Bounded recovery source contracts; runtime behavior is checked by native runner."""
import os
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('JG13_SOURCE', ROOT / 'work/swiftgram-src'))
class RecoveryMediaTests(unittest.TestCase):
    def assertIn(self, member, container, msg=None):
        self.assertTrue(member in container, msg or f"Missing source contract: {member}")
    def setUp(self):
        self.source = (SOURCE / 'submodules/TelegramCore/Sources/PendingMessages/EnqueueMessage.swift').read_text()
    def test_static_media_precedes_binary_cache(self):
        body = self.source.split('private func ghostBaseReconstructedMedia(', 1)[1]
        self.assertIn('ghostBaseStaticDeletedMedia(media: media)', body)
        self.assertLess(body.index('ghostBaseStaticDeletedMedia(media: media)'), body.index('GhostBaseDeletedMediaCache.resolvePath'))
    def test_static_map_is_not_a_live_location(self):
        self.assertIn('liveBroadcastingTimeout: nil', self.source)
        self.assertIn('liveProximityNotificationRadius: nil', self.source)
        self.assertIn('vCardData: contact.vCardData', self.source)
    def test_service_actions_have_specific_bodies(self):
        for action in ('todoCompletions', 'todoAppendTasks', 'pollOptionAppended', 'pollOptionDeleted'):
            self.assertIn('case let .' + action, self.source)
    def test_fresh_interactive_media_is_gated_and_clean(self):
        for fragment in ('canSendPolls', 'canSendTodos', 'Namespaces.Media.LocalPoll', 'totalVoters: nil', 'completions: []', 'poll.attachedMedia == nil', 'case .quiz', 'peer.botInfo', '.banSendPolls'):
            self.assertIn(fragment, self.source)
    def test_interactive_recovery_is_text_only(self):
        for name, end in [('ghostBaseReconstructedMedia', 'ghostBaseResolveDeletedReplies'), ('ghostBaseProtectedLocalMedia', 'ghostBaseResolveProtectedForwards')]:
            body = self.source.split('private func ' + name + '(', 1)[1].split('private func ' + end + '(', 1)[0]
            self.assertNotIn('return ghostBaseFreshDeletedInteractiveMedia(', body)
            self.assertNotIn('return .single(ghostBaseFreshDeletedInteractiveMedia(', body)
    def test_service_context_and_contact_deduplication(self):
        body = self.source.split('private func ghostBaseQuoteBody(', 1)[1].split('private func ghostBaseShiftEntities(', 1)[0]
        self.assertIn('let originalInteractive', body)
        self.assertIn('append(originalPoll.text, originalPoll.textEntities)', body)
        self.assertIn('append(originalTodo.text, originalTodo.textEntities)', body)
        self.assertIn('if recoveredMedia && !interactiveSnapshot', body)
        self.assertIn('prefix: "+ "', body)
        self.assertNotIn('☐', body)
    def test_recovered_attachment_has_no_duplicate_label_and_sticker_uses_alt(self):
        body = self.source.split('private func ghostBaseQuoteBody(', 1)[1].split('private func ghostBaseShiftEntities(', 1)[0]
        self.assertIn('file.attributes', body)
        self.assertIn('case let .Sticker(displayText, _, _)', body)
        self.assertNotIn('file.stickerDisplayText', body)
        self.assertIn('JerkgramDeletedReplyLabel.sticker.text(languageCode: languageCode) +', body)
        self.assertIn('if recoveredMedia && !interactiveSnapshot || source.media.isEmpty', body)
if __name__ == '__main__': unittest.main()
