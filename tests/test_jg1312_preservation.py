"""Source contracts for upstream fixes that share Jerkgram feature owners."""
import os
from pathlib import Path
import unittest

SOURCE = Path(os.environ.get('JG13_SOURCE', Path(__file__).resolve().parents[1] / 'work/swiftgram-src'))


class Upstream1312Preservation(unittest.TestCase):
    def text(self, name):
        p = SOURCE / name
        return p.read_text() if p.is_file() else ''

    def test_create_bot_explicit_deeplink_forwarding(self):
        for name in ('submodules/AccountContext/Sources/AccountContext.swift',
                     'submodules/TelegramUI/Sources/SharedAccountContext.swift',
                     'submodules/TelegramUI/Components/CreateBotScreen/Sources/CreateBotScreen.swift',
                     'Tests/ComposerHarness/AppContext/HarnessSharedAccountContext+Generated.swift'):
            with self.subTest(owner=name):
                self.assertIn('viaDeeplink: Bool', self.text(name))
        self.assertIn('viaDeeplink: viaDeeplink', self.text('submodules/TelegramUI/Sources/SharedAccountContext.swift'))

    def test_short_sent_message_flag_is_explicit_and_propagated(self):
        account = self.text('submodules/TelegramCore/Sources/Account/Account.swift')
        manager = self.text('submodules/TelegramCore/Sources/State/AccountStateManager.swift')
        service = self.text('submodules/TelegramCore/Sources/State/UpdateMessageService.swift')
        self.assertIn('ignoresShortSentMessages: supplementary', account)
        self.assertIn('ignoresShortSentMessages: true', account)
        self.assertIn('ignoresShortSentMessages: Bool\n', manager)
        self.assertIn('ignoresShortSentMessages: self.ignoresShortSentMessages', manager)
        self.assertIn('self.ignoresShortSentMessages = ignoresShortSentMessages', service)
        self.assertIn('if self.ignoresShortSentMessages {\n                    return', service)

    def test_bot_storage_postbox_and_successful_completion(self):
        peers = self.text('submodules/TelegramCore/Sources/TelegramEngine/Peers/TelegramEnginePeers.swift')
        storage = self.text('submodules/TelegramCore/Sources/TelegramEngine/Messages/BotWebView.swift')
        self.assertIn('_internal_setBotStorageValue(postbox: self.account.postbox', peers)
        self.assertIn('_internal_clearBotStorage(postbox: self.account.postbox', peers)
        region = storage[storage.find('private func _internal_updateBotStorageState'):storage.find('public enum BotStorageError')]
        self.assertIn('postbox.transaction', region)
        self.assertIn('return .complete()', region)
        self.assertNotIn('return .never()', region)
        self.assertIn('quotaExceeded', region)

    def test_media_rotation_seek_and_tuple_survive_diagnostics(self):
        chunk = self.text('submodules/MediaPlayer/Sources/ChunkMediaPlayerV2.swift')
        self.assertIn('videoRotationAngle: Double?)', chunk)
        self.assertEqual(chunk.count('if isVideo, reader.videoRotationAngle != loadedPartsMediaData.videoRotationAngle'), 2)
        self.assertIn('guard let self, self.seekId == seekId else', chunk)
        self.assertIn('self.playerNode?.externalVideoRotationAngle = rotationAngle', chunk)
        self.assertIn('self.videoRearmNotBefore = 0.0', chunk)
        self.assertEqual(chunk.count('sampleBuffer = ChunkMediaPlayerV2.normalizeAudioSampleBuffer('), 2)
        self.assertIn('videoRotationAngle: nil)', chunk)
        node = self.text('submodules/MediaPlayer/Sources/MediaPlayerNode.swift')
        self.assertIn('size.width.isFinite, size.height.isFinite, rotationAngle.isFinite', node)
        self.assertIn('self.externalVideoRotationAngle = nil', node)
        self.assertIn('videoLayer.setAffineTransform(mediaPlayerVideoRotationTransform(', node)

    def test_external_rotation_tracks_secondary_attachment_and_own_bounds(self):
        node = self.text('submodules/MediaPlayer/Sources/MediaPlayerNode.swift')
        helper = node.split('private func updateSecondaryVideoLayerRotation(', 1)
        self.assertEqual(len(helper), 2, 'secondary outputs need the upstream external rotation path')
        body = helper[1].split('public func addSecondaryVideoLayer', 1)[0]
        self.assertIn('self.secondaryVideoLayers[ObjectIdentifier(layer)] === layer', body)
        self.assertIn('let rotationAngle = self.externalVideoRotationAngle', body)
        self.assertIn('mediaPlayerVideoRotationTransform(size: layer.bounds.size, rotationAngle: rotationAngle)', body)
        attach = node.split('public func addSecondaryVideoLayer', 1)[1].split('public func removeSecondaryVideoLayer', 1)[0]
        self.assertIn('layer.observe(\\.bounds', attach)
        self.assertIn('[weak self, weak layer]', attach)
        self.assertIn('self.updateSecondaryVideoLayerRotation(layer)', attach)
        self.assertIn('self.secondaryVideoLayerBoundsObservers[key]', attach)
        self.assertEqual(attach.count('self.secondaryVideoLayerBoundsObservers[key] ='), 1)
        remove = node.split('public func removeSecondaryVideoLayer', 1)[1].split('private static func enqueueSecondaryCopies', 1)[0]
        self.assertIn('self.secondaryVideoLayerBoundsObservers.removeValue(forKey: key)?.invalidate()', remove)
        layout = node.split('public func updateLayout()', 1)[1].split('public func reset()', 1)[0]
        self.assertLess(layout.index('self.updateSecondaryVideoLayerRotation(layer)'), layout.index('if bounds.isEmpty'))


if __name__ == '__main__':
    unittest.main()
