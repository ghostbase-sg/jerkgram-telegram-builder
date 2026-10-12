"""Central normalization source contracts, complemented by the native link fixture."""
import os
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('JG13_SOURCE', ROOT / 'work/swiftgram-src'))

class ProtectedCopyTests(unittest.TestCase):
    def setUp(self):
        self.source = (SOURCE / 'submodules/TelegramCore/Sources/PendingMessages/EnqueueMessage.swift').read_text()
    def test_public_boundary_normalizes_before_deleted_reply(self):
        body = self.source.split('public func enqueueMessages(', 1)[1]
        self.assertLess(body.index('ghostBaseResolveProtectedForwards('), body.index('ghostBaseResolveDeletedReplies('))
        self.assertIn('Array<MessageId?>(repeating: nil, count: messages.count)', body)
    def test_actual_source_chat_and_cached_dm_protection(self):
        self.assertIn('private func ghostBaseResolveProtectedForwards(', self.source)
        self.assertIn('cached.flags.contains(.copyProtectionEnabled) || cached.flags.contains(.myCopyProtectionEnabled)', self.source)
        self.assertIn('source.peers[source.id.peerId]', self.source)
        self.assertIn('jerkgram.ProtectedContent.Enabled', self.source)
        self.assertIn('jerkgram.ProtectedContent.ChatForward', self.source)
        self.assertIn('let sourceChannel = actualPeer as? TelegramChannel', self.source)
        self.assertIn('$0.flags.contains(.isScam) || $0.flags.contains(.isFake)', self.source)
    def test_finite_binary_copy_and_batch_abort(self):
        body = self.source.split('private func ghostBaseProtectedLocalMedia(', 1)[1].split('private func ghostBaseResolveProtectedForwards(', 1)[0]
        for token in ('resourceData(', 'fetchedMediaResource(', 'timeout(', 'copyItem(', 'LocalFileReferenceMediaResource(', 'previewRepresentations: []', 'alternativeRepresentations: []', 'reference: nil'):
            self.assertIn(token, body)
        self.assertIn('jerkgramDisplayPortableCopyFailure(text: ghostBaseProtectedCopyFailureText(languageCode: languageCode))', self.source)
        self.assertIn('ghostBaseProtectedForwardAllowsTextFallback(source.media.first)', self.source)
        self.assertNotIn('compactDisplayTitle', self.source)
        self.assertIn('Не удалось скопировать защищённое сообщение', self.source)
        self.assertIn('fittedQuote(', self.source.split('private func ghostBaseProtectedForwardText(', 1)[1])
        self.assertIn('return disposables', body)
    def test_destination_options_grouping_and_quote_budget(self):
        body = self.source.split('private func ghostBaseBuildProtectedForward(', 1)[1].split('private func ghostBaseProtectedLocalMedia(', 1)[0]
        for token in ('forwardCopyRequestedAttributes(', 'ghostBaseProtectedForwardText(', 'maxCaptionLength', 'maxMessageLength', 'hideCaptions', 'hideNames', 'correlationId: correlationId', 'localGroupingKey: groupingKey', 'EmbeddedMediaStickersMessageAttribute'):
            self.assertIn(token, body)
    def test_quote_appearance_and_rich_media(self):
        helper = self.source.split('private func ghostBaseProtectedForwardText(', 1)[1].split('private func ghostBaseBuildProtectedForward(', 1)[0]
        self.assertIn('.BlockQuote(isCollapsed:', helper)
        builder = self.source.split('private func ghostBaseBuildProtectedForward(', 1)[1].split('private func ghostBaseProtectedLocalMedia(', 1)[0]
        self.assertIn('ghostBaseOriginalPortableEntities(source: source)', builder)
        self.assertIn('source.associatedMedia', builder)
        self.assertIn('sourcePeer ?? source.peers[source.id.peerId]', builder)
if __name__ == '__main__': unittest.main()
